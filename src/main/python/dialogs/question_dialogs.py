from PySide2.QtWidgets import QMessageBox, QWidget

TITLE = "Question"


def backup_success(parent: QWidget, archive) -> bool:
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


def mod_delete(parent: QWidget, length: int) -> bool:
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
