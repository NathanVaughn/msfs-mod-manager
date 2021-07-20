import json
import os
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Tuple

from loguru import logger

from . import files
from .config import config


class LayoutError(Exception):
    """
    Raised when a layout.json file cannot be parsed for a mod.
    """


class ManifestError(Exception):
    """
    Raised when a manifest.json file cannot be parsed for a mod.
    """


class ModFile:
    """
    Object to represent a mod file.
    """

    def __init__(self, base_path: Path, rel_path: Path) -> None:
        # path relative to the mod
        self.rel_path: Path = rel_path
        # absolute path on disk
        self.abs_path: Path = base_path.joinpath(self.rel_path)
        self.size: int = files.path_size(self.abs_path)

    def open_file(self) -> None:
        """
        Open the file itself with the system default program.
        """
        logger.debug(f"Opening {self.abs_path}")
        os.startfile(self.abs_path)

    def open_folder(self) -> None:
        """
        Open the folder containing the file in File Explorer.
        """
        logger.debug(f"Opening {self.abs_path.parent}")
        os.startfile(self.abs_path.parent)


class Mod:
    """
    Object to represent a MSFS mod.
    """

    def __init__(self, abs_path: Path) -> None:
        # manifest data
        self.content_type: str = ""
        self.title: str = ""
        self.manufacturer: str = ""
        self.creator: str = ""
        self.version: str = ""
        self.minimum_game_version: str = ""

        # metadata
        # check if absolute path to this mod is in the flightsim folder
        self.abs_path: Path = files.magic(abs_path)
        self.enabled = files.magic(flightsim.packages_path) in self.abs_path.parents
        self.name = self.abs_path.name

        self.manifest_path: Path = self.abs_path.joinpath("manifest.json")
        self.manifest_data: dict = {}

        if not self.manifest_path.exists():
            logger.error(f"{self.manifest_path} not found")
            raise ManifestError(f"{self.manifest_path} not found")

        # update information
        self.update_url: str = ""
        self.last_update_check: str = ""
        self.last_update_version: str = ""

        # files
        # intentionally don't fully resolve this path, as we don't
        # want to resolve a symlink to be able to tell if this mod is enabled
        # or no
        self.last_modified = datetime.fromtimestamp(self.manifest_path.stat().st_ctime)
        self.files: List[ModFile] = []
        self.size: int = 0

        # load manifest
        self.load()

    def load(self) -> None:
        """
        Load data from the manifest.json file.
        """
        logger.debug(f"Parsing manifest.json at {self.manifest_path}")

        # read
        try:
            with open(self.manifest_path, "r", encoding="utf8") as fp:
                self.manifest_data = json.load(fp)
        except Exception as e:
            raise ManifestError(f"{self.manifest_path} parsing error: {str(e.args)}")

        # game content
        self.content_type = self.manifest_data.get("content_type", "")
        self.title = self.manifest_data.get("title", "")
        self.manufacturer = self.manifest_data.get("manufacturer", "")
        self.creator = self.manifest_data.get("creator", "")
        self.version = self.manifest_data.get("package_version", "")
        self.minimum_game_version = self.manifest_data.get("minimum_game_version", "")

        # mod manager content
        self.url = self.manifest_data.get("_nvmmm_url", "")
        self.last_update_check = self.manifest_data.get("_nvmmm_last_check", "")
        self.last_update_version = self.manifest_data.get("_nvmmm_last_version", "")

    def load_files(self) -> None:
        """
        Load extra data on the files of a mod into the object.
        This is an expensive operation, so must be done explicitly.
        """
        logger.debug(f"Loading ModFiles for {self.name}")

        for subfile in self.abs_path.glob("**/*"):
            if subfile.is_file():
                self.files.append(
                    ModFile(self.abs_path, subfile.relative_to(self.abs_path))
                )

        self.size = sum(file.size for file in self.files)

    def dump(self) -> None:
        """
        Save data to the manifest.json file.
        """
        logger.debug(f"Saving {self.name}")

        # game content
        self.manifest_data["content_type"] = self.content_type
        self.manifest_data["title"] = self.title
        self.manifest_data["manufacturer"] = self.manufacturer
        self.manifest_data["creator"] = self.creator
        self.manifest_data["package_version"] = self.version
        self.manifest_data["minimum_game_version"] = self.minimum_game_version

        # mod manager content
        self.manifest_data["_nvmmm_url"] = self.update_url
        self.manifest_data["_nvmmm_last_check"] = self.last_update_check
        self.manifest_data["_nvmmm_last_version"] = self.last_update_version

        # write
        with open(self.manifest_path, "w", encoding="utf8") as fp:
            json.dump(self.manifest_data, fp, indent=4)

    def enable(
        self,
        activity_func: Callable = lambda x: None,
    ) -> None:
        """
        Enable the mod object. Does nothing if already enabled.
        """
        logger.debug(f"Enabling {self.name}")

        if self.enabled:
            logger.debug("Mod already enabled, returning.")
            return

        enabled_path = Path(
            files.magic_resolve(flightsim.community_packages_path), self.name
        )
        files.mk_junction(self.abs_path, enabled_path, activity_func=activity_func)

        # now mark as enabled
        self.enabled = True
        self.abs_path = enabled_path

    def disable(
        self,
        activity_func: Callable = lambda x: None,
    ) -> None:
        """
        Disable the mod object. Does nothing if already disabled.
        """
        logger.debug(f"Disabling {self.name}")

        if not self.enabled:
            logger.debug("Mod already disabled, returning.")
            return

        disabled_path = files.magic_resolve(Path(config.mods_path, self.name))
        if files.is_junction(self.abs_path):
            if files.magic_resolve(self.abs_path) == disabled_path:
                # if the mod was installed via a symlink
                logger.debug(
                    "Mod installation is directory junction, removing junction."
                )
                files.rm_junction(
                    files.magic(self.abs_path), activity_func=activity_func
                )
            else:
                # if the mod was installed somewhere else
                logger.debug(
                    "Mod installation is a directory junction, NOT pointing to its disabled path."
                )
                real_files = files.magic_resolve(self.abs_path)
                # remove the junction
                files.rm_junction(
                    files.magic(self.abs_path), activity_func=activity_func
                )
                # move the source files
                files.mv_path(real_files, disabled_path, activity_func=activity_func)
        else:
            # if the mod was installed via copy/paste
            logger.debug("Mod installation is not directory junction, moving.")
            files.mv_path(self.abs_path, disabled_path, activity_func=activity_func)

        # now mark as disabled
        self.enabled = False
        self.abs_path = disabled_path

    def uninstall(
        self,
        activity_func: Callable = lambda x: None,
    ) -> None:
        """
        Uninstalls the mod mod object.
        """
        logger.debug(f"Uninstalling {self.name}")

        self.disable(activity_func=activity_func)
        files.rm_path(self.abs_path, activity_func=activity_func)


class _FlightSim:
    """
    Object to represent the MSFS installation.
    """

    def __init__(self) -> None:
        self._packages_path: Path = Path()

        self.community_packages_path: Path = Path()
        self.official_packages_path: Path = Path()

    @property
    def packages_path(self) -> Path:
        """
        Return the path of the packages folder.
        """
        return self._packages_path

    @packages_path.setter
    def packages_path(self, value: Path) -> None:
        """
        Set the path of the packages folder.
        Also builds the path the community and official package folders.
        """
        self._packages_path = files.magic_resolve(value)
        logger.debug(f"_packages_path set to {self._packages_path}")

        self.community_packages_path = self._packages_path.joinpath("Community")
        logger.debug(f"community_packages_path set to {self.community_packages_path}")

        # the official packages folder contains a single folder
        # with the game source like Steam.
        self.official_packages_path = self._packages_path.joinpath("Official")
        subdirs = [
            subdir
            for subdir in self.official_packages_path.iterdir()
            if subdir.is_dir()
        ]
        self.official_packages_path = self._packages_path.joinpath(subdirs[0])
        logger.debug(f"official_packages_path set to {self.official_packages_path}")

        config.packages_path = self._packages_path

    def _parse_user_cfg(self, path: Path) -> Path:
        """
        Given the folder or filepath to the `UserCfg.opt` file, try and
        parse it to locate the InstalledPackagesPath. Returns a new Path object.
        """
        # if a directory, add the filename
        if path.is_dir():
            path = path.joinpath("UserCfg.opt")

        logger.debug(f"Attempting to parse UserCfg.opt at {path}")

        installed_packages_path = ""

        with open(files.magic_resolve(path), "r", encoding="utf8") as fp:
            for line in fp:
                if line.startswith("InstalledPackagesPath"):
                    installed_packages_path = line
                    break

        # splits the line once, and takes the second instance
        installed_packages_path = installed_packages_path.split(" ", 1)[1].strip()
        # normalize the string
        installed_packages_path = installed_packages_path.strip('"').strip("'")
        # evaluate the path
        installed_packages_path = Path(installed_packages_path)

        logger.debug(f"InstalledPackagesPath found to be {installed_packages_path}")

        return installed_packages_path

    def get_game_version(self) -> str:
        """
        Attempts to guess the game's version.
        This is based on the fs-base package and the minimum game version listed.
        """
        version = "???"
        # build path to fs-base manifest
        fs_base = files.magic_resolve(self.official_packages_path.joinpath("fs-base"))
        logger.debug(f"fs-base path: {str(fs_base)}")

        # parse it if we guessed correct
        if fs_base.exists():
            fs_base_mod = Mod(fs_base)
            version = fs_base_mod.minimum_game_version

        logger.debug(f"Game version: {version}")
        return version

    def is_sim_packages_path(self, path: Path) -> bool:
        """
        Tests if a path is indeed the simulator packages folder.
        """
        logger.debug(f"Testing if {path} is the Packages folder")
        return (
            files.magic_resolve(path).joinpath("Community").is_dir()
            and files.magic_resolve(path).joinpath("Official").is_dir()
        )

    def is_sim_root_path(self, path: Path) -> bool:
        """
        Tests if a path is indeed the root simulation folder.
        """
        logger.debug(f"Testing if {path} is the simulator root folder")
        return files.magic_resolve(path).joinpath("FlightSimulator.CFG").is_file()

    def find_installation(self) -> bool:
        """
        Attempt to find the installation folder of MSFS 2020.
        Returns a boolean denoting if it succeeded.
        """
        # first, test if value from config file is valid
        logger.debug("Loading sim_packages_path from config file")
        config_packages_path = config.packages_path

        if self.is_sim_packages_path(config_packages_path):
            self.packages_path = config_packages_path
            return True

        # try Steam normal install path
        logger.debug("Loading sim_packages_path from normal Steam")
        normal_steam_root_path = Path(os.getenv("APPDATA"), "Microsoft Flight Simulator")  # type: ignore

        if self.is_sim_root_path(normal_steam_root_path):
            normal_steam_packages_path = self._parse_user_cfg(normal_steam_root_path)
            if self.is_sim_packages_path(normal_steam_packages_path):
                self.packages_path = normal_steam_packages_path
                return True

        # try MS Store install path
        logger.debug("Loading sim_packages_path from MS Store")
        msstore_root_path = Path(
            os.getenv("LOCALAPPDATA"),  # type: ignore
            "Packages",
            "Microsoft.FlightSimulator_8wekyb3d8bbwe",
            "LocalCache",
        )

        if self.is_sim_root_path(msstore_root_path):
            msstore_packages_path = self._parse_user_cfg(msstore_root_path)
            if self.is_sim_packages_path(msstore_packages_path):
                self.packages_path = msstore_packages_path
                return True

        # try boxed edition install path
        logger.debug("Loading sim_packages_path from boxed edition")
        boxed_packages_path = Path(
            os.getenv("LOCALAPPDATA"), "MSFSPackages"  # type: ignore
        )

        if self.is_sim_packages_path(boxed_packages_path):
            self.packages_path = boxed_packages_path
            return True

        # try Steam Program Files normal install path
        programfiles_normal_steam_root_path = Path(
            os.getenv("PROGRAMFILES(x86)"),  # type: ignore
            "Steam",
            "steamapps",
            "common",
            "MicrosoftFlightSimulator",
        )

        if self.is_sim_root_path(programfiles_normal_steam_root_path):
            programfiles_normal_steam_packages_path = self._parse_user_cfg(
                programfiles_normal_steam_root_path
            )
            if self.is_sim_packages_path(programfiles_normal_steam_packages_path):
                self.packages_path = programfiles_normal_steam_packages_path
                return True

        # try Steam Program Files Chucky install path
        programfiles_chucky_steam_root_path = Path(
            os.getenv("PROGRAMFILES(x86)"),  # type: ignore
            "Steam",
            "steamapps",
            "common",
            "Chucky",
        )

        if self.is_sim_root_path(programfiles_chucky_steam_root_path):
            programfiles_chucky_steam_packages_path = self._parse_user_cfg(
                programfiles_chucky_steam_root_path
            )
            if self.is_sim_packages_path(programfiles_chucky_steam_packages_path):
                self.packages_path = programfiles_chucky_steam_packages_path
                return True

        return False

    def get_enabled_mods(
        self,
        activity_func: Callable = lambda x: None,
        percent_func: Callable = lambda x: None,
    ) -> Tuple[List[Mod], List[Exception]]:
        """
        Return a list of enabled mods.
        """
        logger.debug("Getting enabled mods")

        enabled_mods = []
        parsing_errors = []

        subdirs = list(self.community_packages_path.glob("*/"))

        percent_func((0, len(subdirs) - 1))

        for i, subdir in enumerate(subdirs):
            activity_func(f"Parsing {subdir.name}")
            try:
                enabled_mods.append(Mod(subdir))
            except Exception as e:
                parsing_errors.append(e)
            percent_func(i)

        return enabled_mods, parsing_errors

    def get_disabled_mods(
        self,
        activity_func: Callable = lambda x: None,
        percent_func: Callable = lambda x: None,
    ) -> Tuple[List[Mod], List[Exception]]:
        """
        Return a list of disabled mods.
        """
        logger.debug("Getting disabled mods")
        # because mods are just symlinked to the Community folder
        # first, get a list of folders there
        enabled_dirs = [
            subdir.name for subdir in self.community_packages_path.glob("*/")
        ]
        # now, only return Mods that don't have a folder of the same name in
        # the Community folder
        disabled_mods = []
        parsing_errors = []
        subdirs = list(config.mods_path.glob("*/"))

        percent_func((0, len(subdirs) - 1))

        for i, subdir in enumerate(subdirs):
            if subdir.name not in enabled_dirs:
                activity_func(f"Parsing {subdir.name}")
                try:
                    disabled_mods.append(Mod(subdir))
                except Exception as e:
                    parsing_errors.append(e)

            percent_func(i)

        return disabled_mods, parsing_errors

    def get_all_mods(
        self,
        activity_func: Callable = lambda x: None,
        percent_func: Callable = lambda x: None,
    ) -> Tuple[List[Mod], List[Exception]]:
        """
        Return a list of all mods.
        """
        logger.debug("Getting all mods")
        enabled_mods, enabled_errors = self.get_enabled_mods(
            activity_func=activity_func, percent_func=percent_func
        )
        disabled_mods, disabled_errors = self.get_disabled_mods(
            activity_func=activity_func, percent_func=percent_func
        )

        return enabled_mods + disabled_mods, enabled_errors + disabled_errors

    def install_directory(
        self,
        dir: Path,
        activity_func: Callable = lambda x: None,
        percent_func: Callable = lambda x: None,
    ) -> List[Mod]:
        """
        Installs a mod (directory)
        """
        installed_mods = []

        # find mods in the directory
        found_mods = self.find_mods(dir)

        for found_mod in found_mods:
            # create a new mod object
            mod = Mod(found_mod)
            # disable it (this moves it to the disabled folder
            # regardles of where it is originally)
            mod.disable(activity_func=activity_func)
            # enable it
            mod.enable(activity_func=activity_func)

            installed_mods.append(mod)

        return installed_mods

    def install_archives(
        self,
        archives: List[Path],
        activity_func: Callable = lambda x: None,
        percent_func: Callable = lambda x: None,
    ) -> List[Mod]:
        """
        Given a list of archive files, extracts the archive, discovers mods inside,
        and installs them. Returns a list of Mod objects installed.
        """
        installed_mods = []

        # set the progress length to the number of archives selected
        percent_func((0, (len(archives) - 1)))

        for i, archive in enumerate(archives):
            # first, extract the archive
            extracted = files.extract_archive(archive, activity_func=activity_func)

            # find mods in archive
            found_mods = self.find_mods(extracted)

            installed_mods.extend(
                self.install_directory(mod, activity_func=activity_func)
                for mod in found_mods
            )

            # update percent
            percent_func(i)

        return installed_mods

    @staticmethod
    def enable_mods(
        mods: List[Mod],
        activity_func: Callable = lambda x: None,
        percent_func: Callable = lambda x: None,
    ) -> None:
        """
        Enable a list of Mod objects.
        """
        logger.debug("Enabling mods")
        percent_func((0, len(mods) - 1))

        for i, mod in enumerate(mods):
            activity_func(f"Enabling {mod.name}")
            mod.enable(activity_func=activity_func)
            percent_func(i)

    @staticmethod
    def disable_mods(
        mods: List[Mod],
        activity_func: Callable = lambda x: None,
        percent_func: Callable = lambda x: None,
    ) -> None:
        """
        Disable a list of Mod objects.
        """
        logger.debug("Disabling mods")
        percent_func((0, len(mods) - 1))

        for i, mod in enumerate(mods):
            activity_func(f"Disabling {mod.name}")
            mod.disable(activity_func=activity_func)
            percent_func(i)

    @staticmethod
    def uninstall_mods(
        mods: List[Mod],
        activity_func: Callable = lambda x: None,
        percent_func: Callable = lambda x: None,
    ) -> None:
        """
        Uninstall a list of Mod objects.
        """
        logger.debug("Uninstalling mods")
        percent_func((0, len(mods) - 1))

        for i, mod in enumerate(mods):
            activity_func(f"Uninstalling {mod.name}")
            mod.uninstall(activity_func=activity_func)
            percent_func(i)

    @staticmethod
    def find_mods(path: Path) -> List[Path]:
        """
        Discovers mods nested inside of a directory and returns a list of directories
        which are mods
        """
        assert path.is_dir()

        found_mods = []

        # walk the path
        for root, dirs, _ in os.walk(path):
            # check top level directory
            if Path(root, "manifest.json").is_file():
                found_mods.append(Path(root))

            # check subdirectories
            for dir_ in dirs:
                # if directory contains a manifest.json, add it to found list
                if Path(root, dir_, "manifest.json").is_file():
                    found_mods.append(Path(root, dir_))

        return found_mods


flightsim = _FlightSim()
