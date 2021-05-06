import os

import PySide2.QtCore as QtCore
import PySide2.QtWidgets as QtWidgets
from fbs_runtime.application_context.PySide2 import ApplicationContext

import lib.files as files
import lib.helpers as helpers
from lib.flightsim import Mod
from widgets.files_table import FilesTable


class ModInfoWidget(QtWidgets.QWidget):
    """
    Info widget/dialog for displaying mod info.
    """

    def __init__(
        self, parent: QtWidgets.QWidget, appctxt: ApplicationContext, mod: Mod
    ) -> None:
        QtWidgets.QWidget.__init__(self)
        self.parent = parent  # type: ignore
        self.appctxt = appctxt

        self.mod = mod

        self.setWindowTitle("{} - Info".format(mod.name))
        self.setWindowFlags(
            QtCore.Qt.WindowSystemMenuHint  # type: ignore
            | QtCore.Qt.WindowTitleHint  # type: ignore
            | QtCore.Qt.WindowMinimizeButtonHint
            | QtCore.Qt.WindowMaximizeButtonHint
            | QtCore.Qt.WindowCloseButtonHint
        )
        # self.setWindowModality(QtCore.Qt.ApplicationModal)

        # ===================
        # Build the layout
        # ===================

        layout = QtWidgets.QVBoxLayout()  # type: ignore

        top_group = QtWidgets.QGroupBox()  # type: ignore
        top_layout = QtWidgets.QFormLayout()

        self.content_type_field = QtWidgets.QLineEdit(self)
        self.content_type_field.setReadOnly(True)
        top_layout.addRow("Content Type", self.content_type_field)  # type: ignore

        self.title_field = QtWidgets.QLineEdit(self)
        self.title_field.setReadOnly(True)
        top_layout.addRow("Title", self.title_field)  # type: ignore

        self.manufacturer_field = QtWidgets.QLineEdit(self)
        self.manufacturer_field.setReadOnly(True)
        top_layout.addRow("Manufacturer", self.manufacturer_field)  # type: ignore

        self.creator_field = QtWidgets.QLineEdit(self)
        self.creator_field.setReadOnly(True)
        top_layout.addRow("Creator", self.creator_field)  # type: ignore

        self.package_version_field = QtWidgets.QLineEdit(self)
        self.package_version_field.setReadOnly(True)
        top_layout.addRow("Package Version", self.package_version_field)  # type: ignore

        self.minimum_game_version_field = QtWidgets.QLineEdit(self)
        self.minimum_game_version_field.setReadOnly(True)
        top_layout.addRow("Minimum Game Version", self.minimum_game_version_field)  # type: ignore

        self.total_size_field = QtWidgets.QLineEdit(self)
        self.total_size_field.setReadOnly(True)
        top_layout.addRow("Total Size", self.total_size_field)  # type: ignore

        top_group.setLayout(top_layout)
        layout.addWidget(top_group)

        self.open_folder_button = QtWidgets.QPushButton("Open Folder", self)
        layout.addWidget(self.open_folder_button)

        self.files_table = FilesTable(self)
        self.files_table.setAccessibleName("mod_info_files")
        layout.addWidget(self.files_table)

        self.setLayout(layout)

        # ===================
        # Add connections
        # ===================

        self.open_folder_button.clicked.connect(self.open_mod_folder)  # type: ignore

        # ===================
        # Populate data
        # ===================

        # form data
        self.content_type_field.setText(mod.content_type)
        self.title_field.setText(mod.title)
        self.manufacturer_field.setText(mod.manufacturer)
        self.creator_field.setText(mod.creator)
        self.package_version_field.setText(mod.version)
        self.minimum_game_version_field.setText(mod.minimum_game_version)

        # files data
        self.files_table.set_data(self.mod.files, first=True)

        # resize
        helpers.max_resize(
            self, QtCore.QSize(self.sizeHint().width() + 32, self.sizeHint().height())
        )

        self.total_size_field.setText(files.human_readable_size(self.mod.size))

    def open_mod_folder(self) -> None:
        """
        Opens the folder for the mod.
        """
        # this will always be opening a folder and therefore is safe
        os.startfile(self.mod.abs_path)  # nosec

    def open_file_folder(self) -> None:
        """
        Opens the folder for a selected file.
        """
        selected = self.files_table.get_selected_row_objects()

        if selected:
            selected[0].open_folder()

    def open_file_file(self) -> None:
        """
        Opens the selected file.
        """
        selected = self.files_table.get_selected_row_objects()

        if selected:
            selected[0].open_file()
