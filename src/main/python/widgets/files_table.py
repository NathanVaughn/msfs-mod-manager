from typing import Any

import PySide2.QtGui as QtGui
import PySide2.QtWidgets as QtWidgets

from widgets.base_table import base_table


class files_table(base_table):
    """Table widget for displaying mod files."""

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        """Initialize table widget."""
        self.headers = [
            "Path",
            "Size (Bytes)",
        ]

        self.LOOKUP = {
            "path": 0,
            "size": 1,
        }

        super().__init__(parent)
        self.parent = parent

    def get_basic_info(self, row_id: int) -> str:
        """Returns path of a given row index."""
        return self.get_item(row_id, self.LOOKUP["path"]).text()

    def contextMenuEvent(self, event: Any) -> None:
        """Override default context menu event to provide right-click menu."""
        right_click_menu = QtWidgets.QMenu(self)

        open_folder_action = QtWidgets.QAction("Open In Folder", self)
        open_folder_action.triggered.connect(self.parent.open_file_folder)
        right_click_menu.addAction(open_folder_action)

        # popup at cursor position
        right_click_menu.popup(QtGui.QCursor.pos())
