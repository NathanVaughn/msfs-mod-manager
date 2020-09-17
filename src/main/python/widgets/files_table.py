import PySide2.QtCore as QtCore
import PySide2.QtGui as QtGui
import PySide2.QtWidgets as QtWidgets

LOOKUP = {
    "path": 0,
    "size": 1,
}


class files_table(QtWidgets.QTableWidget):
    def __init__(self, parent=None):
        """Table widget for displaying mod files."""

        super(files_table, self).__init__(parent)
        self.parent = parent

        self.headers = [
            "Path",
            "Size (Bytes)",
        ]

        self.setSortingEnabled(True)
        self.setAlternatingRowColors(True)
        # set the correct size adjust policy to get the proper size hint
        self.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.horizontalHeader().setStretchLastSection(True)

    def set_data(self, data):
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
                    item = QtWidgets.QTableWidgetItem()
                    item.setData(QtCore.Qt.EditRole, col)
                    item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
                    self.setItem(r, c, item)

            # sort packages alphabetically
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

    def get_basic_info(self, row_id):
        """Returns path of a given row index."""
        return self.item(row_id, LOOKUP["path"]).text()

    def contextMenuEvent(self, event):
        """Override default context menu event to provide right-click menu."""
        right_click_menu = QtWidgets.QMenu(self)

        open_folder_action = QtWidgets.QAction("Open In Folder", self)
        open_folder_action.triggered.connect(self.parent.open_file_folder)
        right_click_menu.addAction(open_folder_action)

        # popup at cursor position
        right_click_menu.popup(QtGui.QCursor.pos())
