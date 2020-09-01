import PySide2.QtCore as QtCore
import PySide2.QtGui as QtGui
import PySide2.QtWidgets as QtWidgets

LOOKUP = {
    "title": 0,
    "folder_name": 1,
    "content_type": 2,
    "creator": 3,
    "version": 4,
    "installed": 5,
}


class main_table(QtWidgets.QTableWidget):
    def __init__(self, parent=None):
        super(main_table, self).__init__(parent)
        self.parent = parent

        self.headers = [
            "Title",
            "Folder Name",
            "Type",
            "Creator",
            "Version",
            "Enabled",
        ]

        self.setSortingEnabled(True)
        self.setAlternatingRowColors(True)
        # set the correct size adjust policy to get the proper size hint
        self.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.horizontalHeader().setStretchLastSection(True)

    def set_data(self, data):
        """Puts mod data into table"""
        # workaround for data disappearing
        self.setSortingEnabled(False)
        # clear all data
        self.clear()
        self.horizontalHeader().reset()

        if data:
            # the row and column count based on the data size
            self.setColumnCount(len(data[0]))
            self.setRowCount(len(data))

            # create each item
            for r, row in enumerate(data):

                # turn the dictionary into a list of elements using the lookup table
                items = [None] * len(row)
                for key in row:
                    items[LOOKUP[key]] = row[key]

                # put elements into the table
                for c, col in enumerate(items):
                    item = QtWidgets.QTableWidgetItem(str(col))
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
        """Resize the rows and columns"""
        # resize rows and columns
        self.resizeColumnsToContents()
        # this HAS to come second for some reason
        self.resizeRowsToContents()

    def set_colors(self, dark):
        """Set the colors for the rows, based on being a dark theme or not"""
        for r in range(self.rowCount()):
            if self.item(r, LOOKUP["installed"]).text() == "False":
                color = QtGui.QColor(150, 150, 150)
            elif dark:
                color = QtGui.QColor(255, 255, 255)
            else:
                color = QtGui.QColor(0, 0, 0)

            for c in range(self.columnCount()):
                self.item(r, c).setForeground(color)

    def get_basic_info(self, row_id):
        """Returns folder name and installed status of a given row index"""
        return (
            self.item(row_id, LOOKUP["folder_name"]).text(),
            self.item(row_id, LOOKUP["installed"]).text() == "True",
        )
