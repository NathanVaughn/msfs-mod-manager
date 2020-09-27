import PySide2.QtGui as QtGui
import PySide2.QtWidgets as QtWidgets

import lib.types as types
from widgets.base_table import base_table


class main_table(base_table):
    """Primary application table widget for mod summary."""

    def __init__(self, parent=None):
        """Initialize table widget."""
        super().__init__(parent)
        self.parent = parent

        self.headers = [
            "Title",
            "Folder Name",
            "Type",
            "Creator",
            "Version",
            "Enabled",
            "Last Modified",
        ]

        self.LOOKUP = {
            "title": 0,
            "folder_name": 1,
            "content_type": 2,
            "creator": 3,
            "version": 4,
            "enabled": 5,
            "time_mod": 6,
        }

    def set_colors(self, dark):
        """Set the colors for the rows, based on being a dark theme or not."""
        for r in range(self.rowCount()):
            _, enabled = self.get_basic_info(r)
            if not enabled:
                # light, disabled
                color = QtGui.QColor(150, 150, 150)
            elif dark:
                # dark, enabled
                color = QtGui.QColor(255, 255, 255)
            else:
                # light, enabled
                color = QtGui.QColor(0, 0, 0)

            for c in range(self.columnCount()):
                self.item(r, c).setForeground(color)

    def get_basic_info(self, row_id):
        """Returns folder name and enabled status of a given row index."""
        return (
            self.item(row_id, self.LOOKUP["folder_name"]).text(),
            types.str2bool(self.item(row_id, self.LOOKUP["enabled"]).text()),
        )

    def contextMenuEvent(self, event):
        """Override default context menu event to provide right-click menu."""
        right_click_menu = QtWidgets.QMenu(self)

        info_action = QtWidgets.QAction("Info", self)
        info_action.triggered.connect(self.parent.info)
        right_click_menu.addAction(info_action)

        right_click_menu.addSeparator()

        enable_action = QtWidgets.QAction("Enable", self)
        enable_action.triggered.connect(self.parent.enable)
        right_click_menu.addAction(enable_action)

        disable_action = QtWidgets.QAction("Disable", self)
        disable_action.triggered.connect(self.parent.disable)
        right_click_menu.addAction(disable_action)

        right_click_menu.addSeparator()

        uninstall_action = QtWidgets.QAction("Uninstall", self)
        uninstall_action.triggered.connect(self.parent.uninstall)
        right_click_menu.addAction(uninstall_action)

        # popup at cursor position
        right_click_menu.popup(QtGui.QCursor.pos())
