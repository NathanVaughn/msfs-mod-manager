from typing import Any, List

from PySide6 import QtGui, QtWidgets

from ..lib.flightsim import Mod
from .base_table import BaseTable


class ModTable(BaseTable):
    """
    Primary application table widget for mod summary.
    """

    def __init__(self, parent: QtWidgets.QWidget) -> None:
        self.parent_ = parent

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

        super().__init__(self.parent_, header_attributes)

    def set_data(self, data: List[Mod], first: bool = False) -> None:
        """
        Proxy function for the sake of type-hinting
        """
        return super().set_data(data, first=first)  # type: ignore

    def get_row(self, id_: int) -> Mod:
        """
        Proxy function for the sake of type-hinting
        """
        return super().get_row(id_=id_)  # type: ignore

    def set_colors(self, dark: bool) -> None:
        """
        Set the colors for the rows, based on being a dark theme or not.
        """
        for r in range(self.row_count()):
            if not self.get_row(r).enabled:
                # light, disabled
                color = QtGui.QColor(150, 150, 150)
            elif dark:
                # dark, enabled
                color = QtGui.QColor(255, 255, 255)
            else:
                # light, enabled
                color = QtGui.QColor(0, 0, 0)

            for c in range(self.column_count()):
                self.get_item(r, c).setForeground(color)

    def contextMenuEvent(self, event: Any) -> None:
        """
        Override default context menu event to provide right-click menu.
        """
        right_click_menu = QtWidgets.QMenu(self)

        info_action = QtGui.QAction("Info", self)
        info_action.triggered.connect(self.parent_.info)  # type: ignore
        right_click_menu.addAction(info_action)

        right_click_menu.addSeparator()

        enable_action = QtGui.QAction("Enable", self)
        enable_action.triggered.connect(self.parent_.enable)  # type: ignore
        right_click_menu.addAction(enable_action)

        disable_action = QtGui.QAction("Disable", self)
        disable_action.triggered.connect(self.parent_.disable)  # type: ignore
        right_click_menu.addAction(disable_action)

        right_click_menu.addSeparator()

        uninstall_action = QtGui.QAction("Uninstall", self)
        uninstall_action.triggered.connect(self.parent_.uninstall)  # type: ignore
        right_click_menu.addAction(uninstall_action)

        # popup at cursor position
        right_click_menu.popup(QtGui.QCursor.pos())
