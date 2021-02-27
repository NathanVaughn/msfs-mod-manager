import os

import PySide2.QtCore as QtCore
import PySide2.QtWidgets as QtWidgets
from fbs_runtime.application_context.PySide2 import ApplicationContext

import lib.files as files
import lib.resize as resize
from lib.flight_sim import flight_sim
from widgets.files_table import files_table
from typing import List


class info_widget(QtWidgets.QWidget):
    def __init__(
        self,
        flight_sim_handle: flight_sim,
        parent: QtWidgets.QWidget = None,
        appctxt: ApplicationContext = None,
    ) -> None:
        """Info widget/dialog for displaying mod info."""
        QtWidgets.QWidget.__init__(self)
        self.flight_sim = flight_sim_handle
        self.parent = parent # type: ignore
        self.appctxt = appctxt

        # self.setWindowTitle("Info")
        self.setWindowFlags(
            QtCore.Qt.WindowSystemMenuHint # type: ignore
            | QtCore.Qt.WindowTitleHint # type: ignore
            | QtCore.Qt.WindowMinimizeButtonHint
            | QtCore.Qt.WindowMaximizeButtonHint
            | QtCore.Qt.WindowCloseButtonHint
        )
        # self.setWindowModality(QtCore.Qt.ApplicationModal)

        self.layout = QtWidgets.QVBoxLayout() # type: ignore

        self.top_group = QtWidgets.QGroupBox() # type: ignore
        self.top_layout = QtWidgets.QFormLayout()

        self.content_type_field = QtWidgets.QLineEdit(self)
        self.content_type_field.setReadOnly(True)
        self.top_layout.addRow("Content Type", self.content_type_field) # type: ignore

        self.title_field = QtWidgets.QLineEdit(self)
        self.title_field.setReadOnly(True)
        self.top_layout.addRow("Title", self.title_field) # type: ignore

        self.manufacturer_field = QtWidgets.QLineEdit(self)
        self.manufacturer_field.setReadOnly(True)
        self.top_layout.addRow("Manufacturer", self.manufacturer_field) # type: ignore

        self.creator_field = QtWidgets.QLineEdit(self)
        self.creator_field.setReadOnly(True)
        self.top_layout.addRow("Creator", self.creator_field) # type: ignore

        self.package_version_field = QtWidgets.QLineEdit(self)
        self.package_version_field.setReadOnly(True)
        self.top_layout.addRow("Package Version", self.package_version_field) # type: ignore

        self.minimum_game_version_field = QtWidgets.QLineEdit(self)
        self.minimum_game_version_field.setReadOnly(True)
        self.top_layout.addRow("Minimum Game Version", self.minimum_game_version_field) # type: ignore

        self.total_size_field = QtWidgets.QLineEdit(self)
        self.total_size_field.setReadOnly(True)
        self.top_layout.addRow("Total Size", self.total_size_field) # type: ignore

        self.top_group.setLayout(self.top_layout)
        self.layout.addWidget(self.top_group)

        self.open_folder_button = QtWidgets.QPushButton("Open Folder", self)
        self.layout.addWidget(self.open_folder_button)

        self.files_table = files_table(self)
        self.files_table.setAccessibleName("info_files")
        self.layout.addWidget(self.files_table)

        self.setLayout(self.layout)

        self.open_folder_button.clicked.connect(self.open_folder) # type: ignore

    def set_data(self, mod_data: dict, files_data: List[dict]) -> None:
        """Loads all the data for the widget."""
        self.setWindowTitle("{} - Info".format(mod_data["folder_name"]))

        # form data
        self.content_type_field.setText(mod_data["content_type"])
        self.title_field.setText(mod_data["title"])
        self.manufacturer_field.setText(mod_data["manufacturer"])
        self.creator_field.setText(mod_data["creator"])
        self.package_version_field.setText(mod_data["version"])
        self.minimum_game_version_field.setText(mod_data["minimum_game_version"])

        # file data
        self.files_table.set_data(files_data, first=True)

        # resize
        resize.max_resize(
            self, QtCore.QSize(self.sizeHint().width() + 32, self.sizeHint().height())
        )

        # misc data to hold onto
        self.mod_path = mod_data["full_path"]

        self.total_size_field.setText(
            files.human_readable_size(files.get_folder_size(self.mod_path))
        )

    def open_folder(self) -> None:
        """Opens the folder for the mod."""
        # this will always be opening a folder and therefore is safe
        os.startfile(self.mod_path)  # nosec

    def open_file_folder(self) -> None:
        """Opens the folder for a selected file."""
        selected = self.files_table.get_selected_rows()

        if selected:
            file_path = self.files_table.get_basic_info(selected[0])
            full_path = os.path.join(
                self.mod_path,
                file_path,
            )
            # this takes off the filename
            # this will always be opening a folder and therefore is safe
            os.startfile(os.path.dirname(full_path))  # nosec
