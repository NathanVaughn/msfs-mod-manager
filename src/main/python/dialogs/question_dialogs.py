from PySide2.QtWidgets import QMessageBox

TITLE = "Question"


def backup_success(parent, archive):
    result = QMessageBox().question(
        parent,
        TITLE,
        "Backup successfully saved to {}. Would you like to open this directory?".format(
            archive
        ),
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.Yes,
    )
    return result == QMessageBox.Yes


def mod_delete(parent, length):
    result = QMessageBox().information(
        parent,
        TITLE,
        "This will permamentaly delete {} mod(s). Are you sure you want to continue?".format(
            length
        ),
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No,
    )
    return result == QMessageBox.Yes
