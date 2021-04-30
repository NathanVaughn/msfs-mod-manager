from typing import Any

from PySide2 import QtGui, QtWidgets

from widgets.base_table import BaseTable


class FilesTable(BaseTable):
    """
    Table widget for displaying mod files.
    """

    def __init__(self, parent: QtWidgets.QWidget) -> None:
        self.parent = parent  # type: ignore

        header_attributes = [("Path", "path"), ("Size (Bytes)", "size")]

        super().__init__(self.parent, header_attributes)

    def contextMenuEvent(self, event: Any) -> None:
        """
        Override default context menu event to provide right-click menu.
        """
        right_click_menu = QtWidgets.QMenu(self)  # type: ignore

        open_folder_action = QtWidgets.QAction("Open In Folder", self)
        open_folder_action.triggered.connect(self.parent.open_file_folder)  # type: ignore
        right_click_menu.addAction(open_folder_action)  # type: ignore

        # popup at cursor position
        right_click_menu.popup(QtGui.QCursor.pos())  # type: ignore
