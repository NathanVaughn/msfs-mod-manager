from pathlib import Path
from typing import List

from PySide2.QtWidgets import QMessageBox, QWidget

TITLE = "Info"


def sim_detected(parent: QWidget, path: Path) -> None:
    QMessageBox().information(
        parent,
        "Info",
        f"Your Microsoft Flight Simulator folder path was automatically detected to {str(path)}",
    )


def mods_installed(parent: QWidget, mods: List[str]) -> None:
    QMessageBox().information(
        parent,
        TITLE,
        "{} mod(s) installed!\n{}".format(
            len(mods), "\n".join("- {}".format(mod) for mod in mods)
        ),
    )


def mod_install_folder(parent: QWidget) -> None:
    QMessageBox().information(
        parent,
        TITLE,
        "The mod install folder is the folder in which the mod manager"
        " installs mods to. This is NOT the same as the MSFS Community"
        " folder where the simulator expects mods from. This is handled"
        + " for you automatically."
        + "\n !!! Only change this if you know what you're doing!!!",
    )


def mod_install_folder_set(parent: QWidget, path: str) -> None:
    QMessageBox().information(
        parent,
        TITLE,
        f"The mod install path has been set to {str(path)}",
    )
