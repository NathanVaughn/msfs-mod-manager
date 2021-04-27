import json
import os
from datetime import datetime
from pathlib import Path
from typing import List

from loguru import logger

import lib.files as files
from lib.config import config


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
        self.size: int = self.abs_path.stat().st_size

    def open_file(self) -> None:
        """
        Open the file itself with the system default program.
        """
        os.startfile(self.abs_path.parent)

    def open_folder(self) -> None:
        """
        Open the folder containing the file in File Explorer.
        """
        os.startfile(self.abs_path)


class Mod:
    """
    Object to represent a MSFS mod.
    """

    def __init__(self, abs_path: Path) -> None:
        # prep variables
        # ====================================

        # manifest data
        self.content_type: str = ""
        self.title: str = ""
        self.manufacturer: str = ""
        self.creator: str = ""
        self.version: str = ""
        self.minimum_game_version: str = ""

        # metadata
        self.enabled: bool = False
        self.name: str = ""
        self.last_modified: datetime = datetime.now()

        # files
        # intentionally don't fully resolve this path, as we don't
        # want to resolve a symlink to be able to tell if this mod is enabled
        # or no
        self.abs_path: Path = files.add_magic(abs_path)
        self.manifest_path: Path = self.abs_path.joinpath("manifest.json")
        self.files: List[ModFile] = []
        self.size: int = 0

        # load in data from manifest file
        # ====================================
        if not self.manifest_path.exists():
            raise ManifestError

        with open(self.manifest_path, "r") as fp:
            manifest_data = json.load(fp)

        self.content_type = manifest_data.get("content_type", "")
        self.title = manifest_data.get("title", "")
        self.manufacturer = manifest_data.get("manufacturer", "")
        self.creator = manifest_data.get("creator", "")
        self.version = manifest_data.get("package_version", "")
        self.minimum_game_version = manifest_data.get("minimum_game_version", "")

        # check if absolute path to this mod is in the flightsim folder
        self.enabled = flightsim.packages_path in self.abs_path.parents
        self.name = self.abs_path.name
        self.last_modified = datetime.fromtimestamp(self.manifest_path.stat().st_ctime)

    def enable(self) -> None:
        """
        Enable the mod object. Does nothing if already enabled.
        """
        if self.enabled:
            return

        enabled_path = Path.joinpath(
            files.fix(flightsim.community_packages_path), self.name
        )
        files.create_junction(self.abs_path, enabled_path)

        # now mark as enabled
        self.enabled = True
        self.abs_path = enabled_path

    def disable(self) -> None:
        """
        Disable the mod object. Does nothing if already disabled.
        """
        if not self.enabled:
            return

        disabled_path = files.fix(Path.joinpath(config.disabled_mods_path, self.name))
        if files.is_junction(self.abs_path):
            # if the mod was installed via a symlink
            files.add_magic(self.abs_path).rmdir()
        else:
            # if the mod was installed via copy/paste
            files.move_dir(self.abs_path, disabled_path)

        # now mark as disabled
        self.enabled = False
        self.abs_path = disabled_path

    def load_files(self) -> None:
        """
        Load extra data on the files of a mod into the object.
        This is an expensive operation, so must be done explicitly.
        """
        for subfile in self.abs_path.glob("**/*.*"):
            self.files.append(
                ModFile(self.abs_path, subfile.relative_to(self.abs_path))
            )

        self.size = sum(file.size for file in self.files)


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
        self._packages_path = files.fix(value)
        self.community_packages_path = self._packages_path.joinpath("Community")
        self.official_packages_path = self._packages_path.joinpath("Official")

        config.packages_path = self._packages_path

    def _parse_user_cfg(self, path: Path) -> Path:
        """
        Given the folder or filepath to the `UserCfg.opt` file, try and
        parse it to locate the InstalledPackagesPath. Returns a new Path object.
        """
        # if a directory, add the filename
        if path.is_dir():
            path = path.joinpath("UserCfg.opt")

        installed_packages_path = ""

        with open(files.fix(path), "r", encoding="utf8") as fp:
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

        return installed_packages_path

    def _is_sim_packages_path(self, path: Path) -> bool:
        """
        Tests if a path is indeed the simulator packages folder.
        """
        return (
            files.fix(path).joinpath("Community").is_dir()
            and files.fix(path).joinpath("Official").is_dir()
        )

    def _is_sim_root_path(self, path: Path) -> bool:
        """
        Tests if a path is indeed the root simulation folder.
        """
        return files.fix(path).joinpath("FlightSimulator.CFG").is_file()

    def find_installation(self) -> bool:
        """
        Attempt to find the installation folder of MSFS 2020.
        Returns a boolean denoting if it succeeded.
        """
        # first, test if value from config file is valid
        logger.debug("Loading sim_packages_path from config file")
        config_packages_path = config.packages_path

        if self._is_sim_packages_path(config_packages_path):
            self.packages_path = config_packages_path
            return True

        # try Steam normal install path
        logger.debug("Loading sim_packages_path from normal Steam")
        normal_steam_root_path = Path.joinpath(
            Path(os.getenv("APPDATA")), "Microsoft Flight Simulator"  # type: ignore
        )

        if self._is_sim_root_path(normal_steam_root_path):
            normal_steam_packages_path = self._parse_user_cfg(normal_steam_root_path)
            if self._is_sim_packages_path(normal_steam_packages_path):
                self.packages_path = normal_steam_packages_path
                return True

        # try MS Store install path
        logger.debug("Loading sim_packages_path from MS Store")
        msstore_root_path = Path.joinpath(
            Path(os.getenv("LOCALAPPDATA")),  # type: ignore
            "Packages",
            "Microsoft.FlightSimulator_8wekyb3d8bbwe",
            "LocalCache",
        )

        if self._is_sim_root_path(msstore_root_path):
            msstore_packages_path = self._parse_user_cfg(msstore_root_path)
            if self._is_sim_packages_path(msstore_packages_path):
                self.packages_path = msstore_packages_path
                return True

        # try boxed edition install path
        logger.debug("Loading sim_packages_path from boxed edition")
        boxed_packages_path = Path.joinpath(
            Path(os.getenv("LOCALAPPDATA")), "MSFSPackages"  # type: ignore
        )

        if self._is_sim_packages_path(boxed_packages_path):
            self.packages_path = boxed_packages_path
            return True

        # try Steam Program Files normal install path
        programfiles_normal_steam_root_path = Path.joinpath(
            Path(os.getenv("PROGRAMFILES(x86)")),  # type: ignore
            "Steam",
            "steamapps",
            "common",
            "MicrosoftFlightSimulator",
        )

        if self._is_sim_root_path(programfiles_normal_steam_root_path):
            programfiles_normal_steam_packages_path = self._parse_user_cfg(
                programfiles_normal_steam_root_path
            )
            if self._is_sim_packages_path(programfiles_normal_steam_packages_path):
                self.packages_path = programfiles_normal_steam_packages_path
                return True

        # try Steam Program Files Chucky install path
        programfiles_chucky_steam_root_path = Path.joinpath(
            Path(os.getenv("PROGRAMFILES(x86)")),  # type: ignore
            "Steam",
            "steamapps",
            "common",
            "Chucky",
        )

        if self._is_sim_root_path(programfiles_chucky_steam_root_path):
            programfiles_chucky_steam_packages_path = self._parse_user_cfg(
                programfiles_chucky_steam_root_path
            )
            if self._is_sim_packages_path(programfiles_chucky_steam_packages_path):
                self.packages_path = programfiles_chucky_steam_packages_path
                return True

        return False

    def get_enabled_mods(self) -> List[Mod]:
        """
        Return a list of enabled mods.
        """
        return [Mod(subdir) for subdir in self.community_packages_path.glob("*/")]

    def get_disabled_mods(self) -> List[Mod]:
        """
        Return a list of disabled mods.
        """
        return [Mod(subdir) for subdir in config.disabled_mods_path.glob("*/")]


flightsim = _FlightSim()
