import configparser
import os
from datetime import datetime
from pathlib import Path

class _Config:
    """
    Object to represent the global configuration
    """
    BASE_FOLDER: Path = Path.joinpath(os.getenv("APPDATA"), "MSFS Mod ManagerV2")  # type: ignore
    LOG_FILE: Path = Path.joinpath(BASE_FOLDER, "debug.log")
    CONFIG_FILE: Path = Path.joinpath(BASE_FOLDER, "config.ini")

    TIME_FORMAT: str = "%Y-%m-%d %H:%M:%S"

    def __init__(self) -> None:
        self._has_been_loaded: bool  = False
        
        # section header
        self._settings_section = "Settings"

        # path to community folder
        self._sim_packages_path: Path = Path()
        self._sim_packages_path_key: str = "sim_packages_path"

        # path to where disabled mods are stored
        self._disabled_mods_path: Path = Path.joinpath(
            self.BASE_FOLDER, "disabled_mods"
        )
        self._disabled_mods_path_key: str = "disabled_mods_path"

        # last time version was checked
        self._last_version_check: datetime = datetime.now()
        self._last_version_check_key: str = "last_version_check"
        # if user has stopped all version checks
        self._never_version_check: bool = False
        self._never_version_check_key: str = "never_version_check"

        # if custom theme should be used
        self._use_theme: bool = False
        self._use_theme_key: str = "use_theme"

    def _load(self) -> None:
        """
        Load the config file into the object.
        """
        if self._has_been_loaded:
            return
        
        parser = configparser.ConfigParser()
        parser.read(self.CONFIG_FILE)

        if self._settings_section not in parser:
            return

        section = parser[self._settings_section]

        # load the paths from the config
        self._sim_packages_path = Path(section.get(self._sim_packages_path_key, ""))
        self._disabled_mods_path = Path(section.get(self._disabled_mods_path_key, ""))

        # try load datetime from config
        try:
            self._last_version_check = datetime.strptime(
                section.get(self._last_version_check_key), self.TIME_FORMAT
            )
        except Exception:
            pass

        # load booleans
        self._never_version_check = section.getboolean(self._never_version_check_key)
        self._use_theme = section.getboolean(self._use_theme_key)
        
        self._has_been_loaded = True

    def _dump(self) -> None:
        """
        Dump the object into the config file.
        """
        parser = configparser.ConfigParser()
        parser.read(self.CONFIG_FILE)

        if self._settings_section not in parser:
            parser.add_section(self._settings_section)

        section = parser[self._settings_section]

        # save the paths to the config
        section[self._sim_packages_path_key] = str(self._sim_packages_path)
        section[self._disabled_mods_path_key] = str(self._disabled_mods_path)

        # save datetime
        section[self._last_version_check_key] = datetime.strftime(
            self._last_version_check, self.TIME_FORMAT
        )

        # save booleans
        section[self._never_version_check_key] = str(self._never_version_check)
        section[self._use_theme_key] = str(self._use_theme)

        with open(self.CONFIG_FILE, "w") as f:
            parser.write(f)
            
        self._has_been_loaded = False

    @property
    def sim_packages_path(self) -> Path:
        """
        Return the path of the sim community folder.
        """
        self._load()
        return self._sim_packages_path

    @sim_packages_path.setter
    def sim_packages_path(self, value: Path) -> None:
        """
        Set the path of the sim community folder.
        """
        self.sim_packages_path = value
        self._dump()

    @property
    def disabled_mods_path(self) -> Path:
        """
        Return the path of the disabled mods folder.
        """
        self._load()
        return self._disabled_mods_path

    @disabled_mods_path.setter
    def disabled_mods_path(self, value: Path) -> None:
        """
        Set the path of the disabled mods folder.
        """
        self.disabled_mods_path = value
        self._dump()

    @property
    def last_version_check(self) -> datetime:
        """
        Return the last time the version was checked.
        """
        self._load()
        return self._last_version_check

    @last_version_check.setter
    def last_version_check(self, value: datetime) -> None:
        """
        Set the last time the version was checked.
        """
        self._last_version_check = value
        self._dump()

    @property
    def never_version_check(self) -> bool:
        """
        Return if version checks have been disabled.
        """
        self._load()
        return self._never_version_check

    @never_version_check.setter
    def never_version_check(self, value: bool) -> None:
        """
        Set if version checks have been disabled.
        """
        self._never_version_check = value
        self._dump()

    @property
    def use_theme(self) -> bool:
        """
        Return if the custom theme should be used.
        """
        self._load()
        return self._use_theme

    @use_theme.setter
    def use_theme(self, value: bool) -> None:
        """
        Set if the custom theme should be used.
        """
        self._use_theme = value
        self._dump()
        
# singleton
# or something like that, I'm not a compsci major
config = _Config()