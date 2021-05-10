from typing import List

from PySide2.QtWidgets import QMessageBox, QWidget

from lib.flightsim import Mod

TITLE = "Success"


def mods_installed(parent: QWidget, mods: List[Mod]) -> None:
    """
    Dialog for showing the user what mods were installed.
    """
    mod_list_str = "\n".join("- {}".format(mod.name) for mod in mods)
    QMessageBox().information(
        parent, TITLE, f"{len(mods)} mod(s) installed!\n{mod_list_str}"
    )


def mods_manifest_saved(parent: QWidget, mod: Mod) -> None:
    """
    Dialog for informing the user that the mod manifest has been updated.
    """
    QMessageBox().information(parent, TITLE, f"Changes have been saved for {mod.name}")
