from PySide2.QtWidgets import QMessageBox

TITLE = "Info"


def sim_detected(parent, folder):
    QMessageBox().information(
        parent,
        "Info",
        "Your Microsoft Flight Simulator folder path was automatically detected to {}".format(
            folder
        ),
    )


def mods_installed(parent, mods):
    QMessageBox().information(
        parent,
        TITLE,
        "{} mod(s) installed!\n{}".format(
            len(mods), "\n".join(["- {}".format(mod) for mod in mods])
        ),
    )


def disabled_mods_folder(parent, folder):
    QMessageBox().information(
        parent, TITLE, "The disabled mod folder has been set to {}".format(folder),
    )
