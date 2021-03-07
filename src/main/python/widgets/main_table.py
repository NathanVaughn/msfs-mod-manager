from typing import Any, Tuple

import PySide2.QtGui as QtGui
import PySide2.QtWidgets as QtWidgets

import lib.type_helper as type_helper
from widgets.base_table import base_table


class main_table(base_table):
    """Primary application table widget for mod summary."""

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        """Initialize table widget."""
        self.headers = [
            "Title",
            "Folder Name",
            "Type",
            "Creator",
            "Version",
            "Minimum Game Version",
            "Enabled",
            "Last Modified",
        ]

        self.LOOKUP = {
            "title": 0,
            "folder_name": 1,
            "content_type": 2,
            "creator": 3,
            "version": 4,
            "minimum_game_version": 5,
            "enabled": 6,
            "time_mod": 7,
        }

        super().__init__(parent)
        self.parent = parent  # type: ignore

    def set_colors(self, dark: bool) -> None:
        """Set the colors for the rows, based on being a dark theme or not."""
        for r in range(self.rowCount()):
            _, enabled = self.get_basic_info(r)
            if not enabled:
                # light, disabled
                color = QtGui.QColor(150, 150, 150)  # type: ignore
            elif dark:
                # dark, enabled
                color = QtGui.QColor(255, 255, 255)  # type: ignore
            else:
                # light, enabled
                color = QtGui.QColor(0, 0, 0)  # type: ignore

            for c in range(self.columnCount()):
                self.get_item(r, c).setForeground(color)  # type: ignore

    def get_basic_info(self, row_id: int) -> Tuple[str, bool]:
        """Returns folder name and enabled status of a given row index."""
        name = self.get_item(row_id, self.LOOKUP["folder_name"]).text()
        enabled = type_helper.str2bool(
            self.get_item(row_id, self.LOOKUP["enabled"]).text()
        )

        return (name, enabled)

    def contextMenuEvent(self, event: Any) -> None:
        """Override default context menu event to provide right-click menu."""
        right_click_menu = QtWidgets.QMenu(self)  # type: ignore

        info_action = QtWidgets.QAction("Info", self)
        info_action.triggered.connect(self.parent.info)  # type: ignore
        right_click_menu.addAction(info_action)  # type: ignore

        right_click_menu.addSeparator()

        enable_action = QtWidgets.QAction("Enable", self)
        enable_action.triggered.connect(self.parent.enable)  # type: ignore
        right_click_menu.addAction(enable_action)  # type: ignore

        disable_action = QtWidgets.QAction("Disable", self)
        disable_action.triggered.connect(self.parent.disable)  # type: ignore
        right_click_menu.addAction(disable_action)  # type: ignore

        right_click_menu.addSeparator()

        uninstall_action = QtWidgets.QAction("Uninstall", self)
        uninstall_action.triggered.connect(self.parent.uninstall)  # type: ignore
        right_click_menu.addAction(uninstall_action)  # type: ignore

        # popup at cursor position
        right_click_menu.popup(QtGui.QCursor.pos())  # type: ignore
