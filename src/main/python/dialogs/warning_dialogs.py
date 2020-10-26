from PySide2.QtWidgets import QMessageBox

TITLE = "Warning"


def sim_not_detected(parent):
    QMessageBox().warning(
        parent,
        TITLE,
        "Microsoft Flight Simulator path could not be found."
        + " Please select the Packages folder manually"
        + " (which contains the Official and Community folders).",
    )


def sim_path_invalid(parent):
    QMessageBox().warning(
        parent,
        TITLE,
        "Invalid Microsoft Flight Simulator path."
        + " Please select the Packages folder manually"
        + " (which contains the Official and Community folders).",
    )


def mod_parsing(parent, mods):
    QMessageBox().warning(
        parent,
        TITLE,
        "Unable to parse mod(s):\n{} \nThis is likely due to a missing or corrupt manifest.json file. See the debug log for more info.".format(
            "\n".join(["- {}".format(mod) for mod in mods])
        ),
    )
