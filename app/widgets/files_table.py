from typing import Any, List

from PySide6 import QtGui, QtWidgets

from app.lib.flightsim import ModFile
from app.widgets.base_table import BaseTable


class FilesTable(BaseTable):
    """
    Table widget for displaying mod files.
    """

    def __init__(self, parent: QtWidgets.QWidget) -> None:
        self.parent_ = parent

        header_attributes = [("Path", "rel_path"), ("Size (Bytes)", "size")]

        super().__init__(self.parent_, header_attributes)

    def set_data(self, data: List[ModFile], first: bool = False) -> None:
        """
        Proxy function for the sake of type-hinting
        """
        return super().set_data(data, first=first)  # type: ignore

    def get_selected_row_objects(self) -> List[ModFile]:
        """
        Proxy function for the sake of type-hinting
        """
        return super().get_selected_row_objects()

    def contextMenuEvent(self, _: Any) -> None:
        """
        Override default context menu event to provide right-click menu.
        """
        right_click_menu = QtWidgets.QMenu(self)

        open_file_action = QtGui.QAction("Open File", self)
        # slot that isn't typed correctly
        open_file_action.triggered.connect(self.parent_.open_file_file)  # type: ignore
        right_click_menu.addAction(open_file_action)

        open_folder_action = QtGui.QAction("Open In Folder", self)
        # slot that isn't typed correctly
        open_folder_action.triggered.connect(self.parent_.open_file_folder)  # type: ignore
        right_click_menu.addAction(open_folder_action)

        # popup at cursor position
        right_click_menu.popup(QtGui.QCursor.pos())
