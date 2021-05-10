from PySide2.QtWidgets import QMessageBox, QWidget

TITLE = "Error"


def general(parent: QWidget, exception: Exception) -> None:
    """
    Dialog for general error.
    """
    QMessageBox().critical(
        parent,
        TITLE,
        f"Something went terribly wrong.\n{type(exception).__name__}: {str(exception)}",
    )


def _archive(parent: QWidget, archive: str, action: str, message: str) -> None:
    """
    Base archive error dialog. Not meant to be called directly.
    """
    QMessageBox().critical(
        parent,
        TITLE,
        f"Unable to {action} archive {archive}."
        + f" You may need to install a program which can {action} this,"
        + f" such as 7zip or WinRar.\n{message}",
    )


def archive_create(parent: QWidget, archive: str, message: str) -> None:
    """
    Dialog for archive creation error.
    """
    return _archive(parent, archive, "create", message)


def archive_extract(parent: QWidget, archive: str, message: str) -> None:
    """
    Dialog for archive extraction error.
    """
    return _archive(parent, archive, "extract", message)


def no_mods(parent: QWidget, original_object: str) -> None:
    """
    Dialog for no mods found error.
    """
    QMessageBox().critical(
        parent, TITLE, f"Unable to find any mods inside {original_object}"
    )


def permission(parent: QWidget, mod: str, affected_object: str) -> None:
    """
    Dialog for file permissions error.
    """
    QMessageBox().critical(
        parent,
        TITLE,
        f"Unable to install mod {mod} due to a permissions issue"
        + f" (unable to delete file/folder {affected_object}). Relaunch the program"
        + " as an administrator.",
    )
