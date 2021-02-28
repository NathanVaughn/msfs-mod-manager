from typing import List

from PySide2.QtWidgets import QMessageBox, QWidget

TITLE = "Info"


def sim_detected(parent: QWidget, folder: str) -> None:
    QMessageBox().information(
        parent,
        "Info",
        "Your Microsoft Flight Simulator folder path was automatically detected to {}".format(
            folder
        ),
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


def mod_install_folder_set(parent: QWidget, folder: str) -> None:
    QMessageBox().information(
        parent,
        TITLE,
        "The mod install folder has been set to {}".format(folder),
    )
