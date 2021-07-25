import os
from pathlib import Path

import PySide6.QtCore as QtCore
import PySide6.QtGui as QtGui
import PySide6.QtWidgets as QtWidgets

from ..lib import files, helpers
from ..lib.flightsim import Mod
from ..widgets.files_table import FilesTable
from . import success


class ModInfoDialog(QtWidgets.QDialog):
    """
    Info dialog for displaying mod info.
    """

    def __init__(
        self, parent: QtWidgets.QWidget, qapp: QtWidgets.QApplication, mod: Mod
    ) -> None:
        super().__init__()
        self.parent_ = parent
        self.qapp = qapp

        self.mod = mod
        self.has_changed = False

        self.setWindowTitle(f"{mod.name} - Info")
        self.setWindowIcon(QtGui.QIcon(str(helpers.resource_path(Path("icon.png")))))
        self.setWindowFlags(
            QtCore.Qt.WindowSystemMenuHint
            | QtCore.Qt.WindowTitleHint
            | QtCore.Qt.WindowMinimizeButtonHint
            | QtCore.Qt.WindowMaximizeButtonHint
            | QtCore.Qt.WindowCloseButtonHint
        )
        # self.setWindowModality(QtCore.Qt.ApplicationModal)

        # ===================
        # Build the layout
        # ===================

        layout = QtWidgets.QVBoxLayout()

        top_group = QtWidgets.QGroupBox()
        top_layout = QtWidgets.QFormLayout()

        self.content_type_field = QtWidgets.QLineEdit(self)
        top_layout.addRow("Content Type", self.content_type_field)

        self.title_field = QtWidgets.QLineEdit(self)
        top_layout.addRow("Title", self.title_field)

        self.manufacturer_field = QtWidgets.QLineEdit(self)
        top_layout.addRow("Manufacturer", self.manufacturer_field)

        self.creator_field = QtWidgets.QLineEdit(self)
        top_layout.addRow("Creator", self.creator_field)

        self.version_field = QtWidgets.QLineEdit(self)
        top_layout.addRow("Version", self.version_field)

        self.minimum_game_version_field = QtWidgets.QLineEdit(self)
        top_layout.addRow("Minimum Game Version", self.minimum_game_version_field)

        self.total_size_field = QtWidgets.QLineEdit(self)
        self.total_size_field.setReadOnly(True)
        top_layout.addRow("Total Size", self.total_size_field)

        top_group.setLayout(top_layout)
        layout.addWidget(top_group)

        sublayout = QtWidgets.QHBoxLayout()

        self.open_folder_button = QtWidgets.QPushButton("Open Folder", self)
        sublayout.addWidget(self.open_folder_button)

        self.save_button = QtWidgets.QPushButton("Save Changes", self)
        self.save_button.setDisabled(True)
        sublayout.addWidget(self.save_button)

        layout.addLayout(sublayout)

        self.files_table = FilesTable(self)
        self.files_table.setAccessibleName("mod_info_files")
        layout.addWidget(self.files_table)

        self.setLayout(layout)

        # ===================
        # Add connections
        # ===================

        # slots are not typed correctly
        self.content_type_field.textEdited.connect(self.field_change)  # type: ignore
        self.title_field.textEdited.connect(self.field_change)  # type: ignore
        self.manufacturer_field.textEdited.connect(self.field_change)  # type: ignore
        self.creator_field.textEdited.connect(self.field_change)  # type: ignore
        self.version_field.textEdited.connect(self.field_change)  # type: ignore
        self.minimum_game_version_field.textEdited.connect(self.field_change)  # type: ignore

        self.open_folder_button.clicked.connect(self.open_mod_folder)  # type: ignore
        self.save_button.clicked.connect(self.dump)  # type: ignore

        self.load()
        self.show()

    def load(self) -> None:
        """
        Load in the data from the mod.
        """
        # form data
        self.content_type_field.setText(self.mod.content_type)
        self.title_field.setText(self.mod.title)
        self.manufacturer_field.setText(self.mod.manufacturer)
        self.creator_field.setText(self.mod.creator)
        self.version_field.setText(self.mod.version)
        self.minimum_game_version_field.setText(self.mod.minimum_game_version)

        # files data
        self.files_table.set_data(self.mod.files, first=True)

        # resize
        helpers.max_resize(
            self, QtCore.QSize(self.sizeHint().width() + 32, self.sizeHint().height())
        )

        self.total_size_field.setText(files.human_readable_size(self.mod.size))

    def field_change(self) -> None:
        """
        Callback for when any text field has changed.
        """
        if not self.has_changed:
            self.has_changed = True
            self.save_button.setDisabled(False)

    def dump(self) -> None:
        """
        Saves the changes made to the mod.
        """
        self.mod.content_type = self.content_type_field.text()
        self.mod.title = self.title_field.text()
        self.mod.manufacturer = self.manufacturer_field.text()
        self.mod.creator = self.creator_field.text()
        self.mod.version = self.version_field.text()
        self.mod.minimum_game_version = self.minimum_game_version_field.text()

        self.mod.dump()

        success.mods_manifest_saved(self, self.mod)

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
