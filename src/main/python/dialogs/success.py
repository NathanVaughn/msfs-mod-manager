from typing import List

from PySide2.QtWidgets import QMessageBox, QWidget

from lib.flightsim import Mod

TITLE = "Success"


def mods_installed(parent: QWidget, mods: List[Mod]) -> None:
    """
    Dialog for showing the user what mods were installed.
    """
    QMessageBox().information(
        parent,
        TITLE,
        "{} mod(s) installed!\n{}".format(
            len(mods), "\n".join("- {}".format(mod.name) for mod in mods)
        ),
    )


def mods_manifest_saved(parent: QWidget, mod: Mod) -> None:
    """
    Dialog for informing the user that the mod manifest has been updated.
    """
    QMessageBox().information(parent, TITLE, f"Changes have been saved for {mod.name}")
