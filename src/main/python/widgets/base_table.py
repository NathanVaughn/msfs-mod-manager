from typing import List

import PySide2.QtCore as QtCore
import PySide2.QtGui as QtGui
import PySide2.QtWidgets as QtWidgets


class base_table(QtWidgets.QTableView):
    """Base table widget."""

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        """Initialize table widget."""
        super().__init__(parent)
        self.parent = None  # type: ignore
        # needs to be set by inherited class
        # self.headers = []
        # self.LOOKUP = {}

        self.setSortingEnabled(True)
        self.setAlternatingRowColors(True)
        self.setWordWrap(False)
        self.setEditTriggers(
            QtWidgets.QAbstractItemView.NoEditTriggers  # type: ignore
        )  # disable editing

        # set the correct size adjust policy to get the proper size hint
        self.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)  # type: ignore
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)  # type: ignore
        self.horizontalHeader().setStretchLastSection(True)

        # create data model
        self.base_model = QtGui.QStandardItemModel(0, len(self.LOOKUP))  # type: ignore
        # set model headers
        for i, header in enumerate(self.headers):  # type: ignore
            self.base_model.setHeaderData(i, QtCore.Qt.Horizontal, header)  # type: ignore

        # proxy model
        # self.proxy_model = MyProxy()
        self.proxy_model = QtCore.QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.base_model)
        self.proxy_model.setDynamicSortFilter(True)
        self.proxy_model.setFilterKeyColumn(-1)  # all columns
        # proxy model sort settings
        self.proxy_model.setSortCaseSensitivity(QtCore.Qt.CaseInsensitive)  # type: ignore
        self.proxy_model.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)  # type: ignore

        # set table model
        self.setModel(self.proxy_model)

    def set_row(self, row_data: dict) -> None:
        """Set a row's data."""
        self.base_model.insertRow(0)

        for col, item in row_data.items():
            # skip items not in lookup list
            if col not in self.LOOKUP:  # type: ignore
                continue

            # if it's a boolean, convert to string so capitalization
            # is preserved, which oddly Qt does not do
            if isinstance(item, bool):
                item = str(item)

            self.base_model.setData(self.base_model.index(0, self.LOOKUP[col]), item)  # type: ignore

    def set_data(self, data: List[dict], first: bool = False) -> None:
        """Set the table data."""
        # clear
        self.clear()

        # set data
        for row in data:
            self.set_row(row)

        # finish
        if first:
            self.sortByColumn(0, QtCore.Qt.AscendingOrder)  # type: ignore

        self.resize()

    def clear(self) -> None:
        """Clears the source table model."""
        self.base_model.removeRows(0, self.base_model.rowCount())

    def get_item(self, r: int, c: int) -> QtGui.QStandardItem:
        """Convience function to get table item."""
        return self.base_model.item(r, c)

    def rowCount(self) -> int:
        """Convience proxy function for rowCount like QTableWidget."""
        return self.base_model.rowCount()

    def columnCount(self) -> int:
        """Convience proxy function for columnCount like QTableWidget."""
        return self.base_model.columnCount()

    def sizeHint(self) -> QtCore.QSize:
        """Reimplements sizeHint function to increase the width."""
        # I have no idea why by default the width size hint is too small, but it is
        old_size = super().sizeHint()
        # add a magic 25 pixels to eliminate the scroll bar by default
        return QtCore.QSize(old_size.width() + 0, old_size.height())

    def resize(self) -> None:
        """Resize the rows and columns."""
        # resize rows and columns
        self.resizeColumnsToContents()
        # this HAS to come second for some reason
        self.resizeRowsToContents()

    def get_selected_rows(self) -> list:
        """Returns a list of selected row indexes."""
        # this gets the list of model indexes from the table, then maps them
        # to the source data via the proxy model, and returns the row elements
        return [
            y.row()
            for y in [
                self.proxy_model.mapToSource(x)
                for x in self.selectionModel().selectedRows()
            ]
        ]

    def search(self, term: str) -> None:
        """Filters the proxy model with wildcard expression."""
        self.proxy_model.setFilterWildcard(term)
        self.resizeRowsToContents()
