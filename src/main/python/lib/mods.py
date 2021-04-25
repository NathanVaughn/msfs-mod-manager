import json
import os
from datetime import datetime
from pathlib import Path
from typing import List

import lib.files as files


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

    def __init__(self) -> None:
        self.rel_path: Path = Path()
        self.abs_path: Path = Path()
        self.size: int = 0

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

    def __init__(self, flightsim, abs_path: Path) -> None:
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
        self.abs_path: Path = files.fix(abs_path)
        self.manifest_path: Path = files.add_magic(
            self.abs_path.joinpath("manifest.json")
        )
        # TODO
        self.files: List[ModFile] = []

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

        # TODO
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

    def disable(self) -> None:
        """
        Disable the mod object. Does nothing if already disabled.
        """
        if not self.enabled:
            return
