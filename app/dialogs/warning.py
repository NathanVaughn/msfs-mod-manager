from typing import List

from PySide6.QtWidgets import QMessageBox, QWidget

from app.lib.flightsim import Mod

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


def mod_parsing(parent: QWidget, errors: List[Exception]) -> None:
    """
    Dialog for warning the user that the given mods had parsing errors.
    """
    error_list_str = "\n".join(f"- {error}" for error in errors)

    QMessageBox().warning(
        parent,
        TITLE,
        f"Unable to parse mod(s):\n{error_list_str} \n"
        + " This is likely due to a missing or corrupt manifest.json file."
        + " See the debug log for more info.",
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


def mod_uninstalls(parent: QWidget, mods: List[Mod]) -> bool:
    """
    Dialog for warning the user that they're about to uninstall mods.
    """
    result = QMessageBox().warning(
        parent,
        TITLE,
        f"You're about to permamently delete {len(mods)} mod(s). "
        + "Are you sure you want to continue?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,
    )
    return result == QMessageBox.StandardButton.Yes
