import PySide2.QtCore as QtCore
import PySide2.QtWidgets as QtWidgets

import lib.types as types


class base_table(QtWidgets.QTableWidget):
    """Base table widget."""

    def __init__(self, parent=None):
        """Initialize table widget."""
        super().__init__(parent)
        self.parent = None
        self.headers = []
        self.LOOKUP = {}

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
            self.setColumnCount(len(self.LOOKUP))
            self.setRowCount(len(data))

            # create each item
            for r, row in enumerate(data):

                # turn the dictionary into a list of elements using the lookup table
                items = [None] * len(row)
                for key in row:
                    if key in self.LOOKUP:
                        items[self.LOOKUP[key]] = row[key]

                # put elements into the table
                for c, col in enumerate(items):
                    # leave ints as ints, but convert all else to strings
                    if not types.is_int(col):
                        col = str(col)

                    # if it's a boolean, convert to string so capitalization
                    # is preserved, which oddly Qt does not do
                    if isinstance(col, bool):
                        col = str(col)

                    item = QtWidgets.QTableWidgetItem()
                    item.setData(QtCore.Qt.EditRole, col)
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

    def get_row_strings(self):
        """Returns list of row data as strings."""
        return [
            ", ".join([self.item(r, c).text() for c in range(self.columnCount())])
            for r in range(self.rowCount())
        ]

    def hide_rows(self, rows):
        """Hides given row indexes."""
        [self.hideRow(r) for r in rows]

    def show_all_rows(self):
        """Shows all rows."""
        [self.showRow(r) for r in range(self.rowCount())]
