from typing import Any, List

from PySide2 import QtGui, QtWidgets

from lib.flightsim import Mod
from widgets.base_table import BaseTable


class ModTable(BaseTable):
    """
    Primary application table widget for mod summary.
    """

    def __init__(self, parent: QtWidgets.QWidget) -> None:
        self.parent = parent  # type: ignore

        header_attributes = [
            ("Title", "title"),
            ("Folder Name", "name"),
            ("Type", "content_type"),
            ("Manufacturer", "manufacturer"),
            ("Creator", "creator"),
            ("Version", "version"),
            ("Minimum Game Version", "minimum_game_version"),
            ("Enabled", "enabled"),
            ("Last Modified", "last_modified"),
        ]

        super().__init__(self.parent, header_attributes)

    def set_data(self, data: List[Mod], first: bool = False) -> None:
        """
        Proxy function for the sake of type-hinting
        """
        super().set_data(data, first=first)  # type: ignore

    def set_colors(self, dark: bool) -> None:
        """
        Set the colors for the rows, based on being a dark theme or not.
        """
        for r in range(self.row_count()):
            if not self.get_row(r).enabled:  # type: ignore
                # light, disabled
                color = QtGui.QColor(150, 150, 150)  # type: ignore
            elif dark:
                # dark, enabled
                color = QtGui.QColor(255, 255, 255)  # type: ignore
            else:
                # light, enabled
                color = QtGui.QColor(0, 0, 0)  # type: ignore

            for c in range(self.column_count()):
                self.get_item(r, c).setForeground(color)  # type: ignore

    def contextMenuEvent(self, event: Any) -> None:
        """
        Override default context menu event to provide right-click menu.
        """
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
