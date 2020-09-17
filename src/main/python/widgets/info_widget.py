import os

import PySide2.QtCore as QtCore
import PySide2.QtWidgets as QtWidgets

import lib.flight_sim as flight_sim
from widgets.files_table import files_table


class info_widget(QtWidgets.QWidget):
    def __init__(self, parent=None, appctxt=None):
        """Info widget/dialog for displaying mod info."""

        QtWidgets.QWidget.__init__(self)
        self.parent = parent
        self.appctxt = appctxt

        # self.setWindowTitle("Info")
        self.setWindowFlags(
            QtCore.Qt.WindowSystemMenuHint
            | QtCore.Qt.WindowTitleHint
            | QtCore.Qt.WindowCloseButtonHint
        )
        # self.setWindowModality(QtCore.Qt.ApplicationModal)

        self.layout = QtWidgets.QVBoxLayout()

        self.top_group = QtWidgets.QGroupBox()
        self.top_layout = QtWidgets.QFormLayout()

        self.content_type_field = QtWidgets.QLineEdit()
        self.content_type_field.setReadOnly(True)
        self.top_layout.addRow("Content Type", self.content_type_field)

        self.title_field = QtWidgets.QLineEdit()
        self.title_field.setReadOnly(True)
        self.top_layout.addRow("Title", self.title_field)

        self.manufacturer_field = QtWidgets.QLineEdit()
        self.manufacturer_field.setReadOnly(True)
        self.top_layout.addRow("Manufacturer", self.manufacturer_field)

        self.creator_field = QtWidgets.QLineEdit()
        self.creator_field.setReadOnly(True)
        self.top_layout.addRow("Creator", self.creator_field)

        self.package_version_field = QtWidgets.QLineEdit()
        self.package_version_field.setReadOnly(True)
        self.top_layout.addRow("Package Version", self.package_version_field)

        self.minimum_game_version_field = QtWidgets.QLineEdit()
        self.minimum_game_version_field.setReadOnly(True)
        self.top_layout.addRow("Minimum Game Version", self.minimum_game_version_field)

        self.total_size_field = QtWidgets.QLineEdit()
        self.total_size_field.setReadOnly(True)
        self.top_layout.addRow("Total Size", self.total_size_field)

        self.top_group.setLayout(self.top_layout)
        self.layout.addWidget(self.top_group)

        self.open_folder_button = QtWidgets.QPushButton("Open Folder")
        self.layout.addWidget(self.open_folder_button)

        self.files_table = files_table(self)
        self.files_table.setAccessibleName("info_files")
        self.layout.addWidget(self.files_table)

        self.setLayout(self.layout)

        self.open_folder_button.clicked.connect(self.open_folder)

    def get_selected_rows(self):
        """Returns a list of row indexes that are currently selected."""
        return list({index.row() for index in self.files_table.selectedIndexes()})

    def set_data(self, mod_data, files_data):
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
        self.files_table.set_data(files_data)

        # resize
        self.setMaximumHeight(700)
        # weird magic number to account for too small size hint
        self.resize(self.sizeHint().width() + 32, self.sizeHint().height())

        # misc data to hold onto
        self.mod_folder = mod_data["folder_name"]
        self.enabled = mod_data["enabled"]

        self.total_size_field.setText(
            flight_sim.human_readable_size(
                flight_sim.get_folder_size(
                    flight_sim.get_mod_folder(
                        self.parent.sim_folder, self.mod_folder, self.enabled
                    )
                )
            )
        )

    def open_folder(self):
        """Opens the folder for the mod."""
        # this will always be opening a folder and therefore is safe
        os.startfile( # nosec
            flight_sim.get_mod_folder(
                self.parent.sim_folder, self.mod_folder, self.enabled
            ),
        )

    def open_file_folder(self):
        """Opens the folder for a selected file."""
        selected = self.get_selected_rows()

        if selected:
            file_path = self.files_table.get_basic_info(selected[0])
            full_path = os.path.join(
                flight_sim.get_mod_folder(
                    self.parent.sim_folder, self.mod_folder, self.enabled
                ),
                file_path,
            )
            # this takes off the filename
            # this will always be opening a folder and therefore is safe
            os.startfile(os.path.dirname(full_path))  # nosec
