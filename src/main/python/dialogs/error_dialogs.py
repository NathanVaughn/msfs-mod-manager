from typing import Any

from PySide2.QtWidgets import QMessageBox, QWidget

TITLE = "Error"


def general(parent: QWidget, typ: Any, message: str) -> None:
    QMessageBox().critical(
        parent,
        TITLE,
        "Something went terribly wrong.\n{}: {}".format(typ, message),
    )


def _archive(parent: QWidget, archive: str, action: str, message: str) -> None:
    QMessageBox().critical(
        parent,
        TITLE,
        "Unable to {action} archive {archive}."
        + " You may need to install a program which can {action} this,"
        + " such as 7zip or WinRar.\n{message}".format(
            archive=archive, action=action, message=message
        ),
    )


def archive_create(parent: QWidget, archive: str, message: str) -> None:
    return _archive(parent, archive, "create", message)


def archive_extract(parent: QWidget, archive: str, message: str) -> None:
    return _archive(parent, archive, "extract", message)


def no_mods(parent: QWidget, original_object: str) -> None:
    QMessageBox().critical(
        parent, TITLE, "Unable to find any mods inside {}".format(original_object)
    )


def permission(parent: QWidget, mod: str, affected_object: str) -> None:
    QMessageBox().critical(
        parent,
        TITLE,
        "Unable to install mod {} due to a permissions issue"
        + " (unable to delete file/folder {}). Relaunch the program"
        + " as an administrator.".format(mod, affected_object),
    )
