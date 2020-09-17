import PySide2.QtCore as QtCore
import PySide2.QtGui as QtGui
import PySide2.QtWidgets as QtWidgets

LOOKUP = {
    "title": 0,
    "folder_name": 1,
    "content_type": 2,
    "creator": 3,
    "version": 4,
    "enabled": 5,
    "time_mod": 6,
}


class main_table(QtWidgets.QTableWidget):
    def __init__(self, parent=None):
        """Primary application table widget for mod summary."""

        super(main_table, self).__init__(parent)
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

        self.setSortingEnabled(True)
        self.setAlternatingRowColors(True)
        # set the correct size adjust policy to get the proper size hint
        self.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.horizontalHeader().setStretchLastSection(True)

    def set_data(self, data, first=False):
        """Puts mod data into table."""
        # workaround for data disappearing
        self.setSortingEnabled(False)
        # clear all data
        self.clear()
        self.horizontalHeader().reset()

        if data:
            # the row and column count based on the data size
            self.setColumnCount(len(LOOKUP))
            self.setRowCount(len(data))

            # create each item
            for r, row in enumerate(data):

                # turn the dictionary into a list of elements using the lookup table
                items = [None] * len(row)
                for key in row:
                    if key in LOOKUP:
                        items[LOOKUP[key]] = row[key]

                # put elements into the table
                for c, col in enumerate(items):
                    item = QtWidgets.QTableWidgetItem(str(col))
                    item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
                    self.setItem(r, c, item)

            # sort packages alphabetically
            if first:
                self.sortItems(0)

        # set the horizontal headers
        self.setHorizontalHeaderLabels(self.headers)

        # re-enable sorting
        self.setSortingEnabled(True)

        self.resize()

    def resize(self):
        """Resize the rows and columns."""
        # resize rows and columns
        self.resizeColumnsToContents()
        # this HAS to come second for some reason
        self.resizeRowsToContents()

    def set_colors(self, dark):
        """Set the colors for the rows, based on being a dark theme or not."""
        for r in range(self.rowCount()):
            _, enabled = self.get_basic_info(r)
            if not enabled:
                color = QtGui.QColor(150, 150, 150)
            elif dark:
                color = QtGui.QColor(255, 255, 255)
            else:
                color = QtGui.QColor(0, 0, 0)

            for c in range(self.columnCount()):
                self.item(r, c).setForeground(color)

    def get_basic_info(self, row_id):
        """Returns folder name and enabled status of a given row index."""
        return (
            self.item(row_id, LOOKUP["folder_name"]).text(),
            self.item(row_id, LOOKUP["enabled"]).text() == "True",
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
