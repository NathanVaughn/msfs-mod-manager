from pathlib import Path

from PySide6.QtWidgets import QMessageBox, QWidget

TITLE = "Info"


def sim_detected(parent: QWidget, path: Path) -> None:
    """
    Dialog for showing the user what path the sim installation was detected.
    """
    QMessageBox().information(
        parent,
        "Info",
        f"Your Microsoft Flight Simulator folder path was automatically detected to {str(path)}",
    )


def mod_install_folder(parent: QWidget) -> None:
    """
    Dialog for informing the use what the mod install folder is used for.
    """
    QMessageBox().information(
        parent,
        TITLE,
        "The mod install folder is the folder in which the mod manager"
        " installs mods to. This is NOT the same as the MSFS Community"
        " folder where the simulator expects mods from. This is handled"
        + " for you automatically."
        + "\n !!! Only change this if you know what you're doing!!!",
    )


def mod_install_folder_set(parent: QWidget, path: Path) -> None:
    """
    Dialog for showing the user what path the mod install folder has changed to.
    """
    QMessageBox().information(
        parent,
        TITLE,
        f"The mod install path has been set to {str(path)}",
    )
