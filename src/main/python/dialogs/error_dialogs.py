from PySide2.QtWidgets import QMessageBox

TITLE = "Error"


def general(parent, typ, message):
    QMessageBox().critical(
        parent,
        TITLE,
        "Something went terribly wrong.\n{}: {}".format(typ, message),
    )


def _archive(parent, archive, action, message):
    QMessageBox().critical(
        parent,
        TITLE,
        "Unable to {action} archive {archive}. You may need to install a program which can {action} this, such as 7zip or WinRar.\n{message}".format(
            archive=archive, action=action, message=message
        ),
    )


def archive_create(parent, archive, message):
    return _archive(parent, archive, "create", message)


def archive_extract(parent, archive, message):
    return _archive(parent, archive, "extract", message)


def no_mods(parent, original_object):
    QMessageBox().critical(
        parent, TITLE, "Unable to find any mods inside {}".format(original_object)
    )


def permission(parent, mod, affected_object):
    QMessageBox().critical(
        parent,
        TITLE,
        "Unable to install mod {} due to a permissions issue (unable to delete file/folder {}). Relaunch the program as an administrator.".format(
            mod, affected_object
        ),
    )
