from typing import List

from PySide2.QtWidgets import QMessageBox, QWidget

from lib.flightsim import Mod

TITLE = "Warning"


def sim_not_detected(parent: QWidget) -> None:
    """
    Dialog for warning the user that the sim installation could not be detected.
    """
    QMessageBox().warning(
        parent,
        TITLE,
        "Microsoft Flight Simulator path could not be found."
        + " Please select the Packages folder manually"
        + " (which contains the Official and Community folders).",
    )


def sim_path_invalid(parent: QWidget) -> None:
    """
    Dialog for warning the user that the select sim installation path is invalid.
    """
    QMessageBox().warning(
        parent,
        TITLE,
        "Invalid Microsoft Flight Simulator path."
        + " Please select the Packages folder manually"
        + " (which contains the Official and Community folders).",
    )


def mod_parsing(parent: QWidget, mods: List[Mod]) -> None:
    """
    Dialog for warning the user that the given mods had parsing errors.
    """
    QMessageBox().warning(
        parent,
        TITLE,
        "Unable to parse mod(s):\n{} \nThis is likely due to a missing or corrupt manifest.json file. See the debug log for more info.".format(
            "\n".join("- {}".format(mod.name) for mod in mods)
        ),
    )


def mod_install_folder_same(parent: QWidget) -> None:
    """
    Dialog for warning the user that selected mod install folder is the same
    as the currently set folder.
    """
    QMessageBox().warning(
        parent,
        TITLE,
        "The mod install folder you've selected is the same as what's currently set.",
    )


def mod_install_folder_in_sim_path(parent: QWidget) -> None:
    """
    Dialog for warning the user that selected mod install folder is in
    the same directory structure as the currently set folder.
    """
    QMessageBox().warning(
        parent,
        TITLE,
        "The mod install folder you've selected contains the same path"
        + " as the simulator. You, more than likely, do not want this.",
    )
