import os
import sys
from pathlib import Path

from fbs_runtime.application_context.PySide2 import ApplicationContext
from PySide2 import QtCore, QtGui, QtWidgets

import dialogs.information
import dialogs.warning
from dialogs.about import AboutDialog
from dialogs.progress import ProgressDialog
from lib.config import config
from lib.flightsim import flightsim
from lib.thread import Thread, wait_for_thread
from widgets.mod_table import ModTable

ARCHIVE_FILTER = "Archives (*.zip *.rar *.tar *.bz2 *.7z)"

# ======================
# Decorators
# ======================


def disable_button(button_name: str):
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            button: QtWidgets.QPushButton = getattr(self, button_name)

            button.setEnabled(False)
            output = func(self, *args, **kwargs)
            button.setEnabled(True)

            return output

        return wrapper

    return decorator


class MainWidget(QtWidgets.QWidget):
    """
    Main application widget.
    """

    def __init__(self, parent: QtWidgets.QWidget, appctxt: ApplicationContext) -> None:
        QtWidgets.QWidget.__init__(self)
        self.parent = parent  # type: ignore
        self.appctxt = appctxt

        layout = QtWidgets.QGridLayout(self)

        # layouts don't work with keyword arguments ????

        self.install_button = QtWidgets.QPushButton("Install", self)
        layout.addWidget(self.install_button, 0, 0)  # type: ignore

        self.uninstall_button = QtWidgets.QPushButton("Uninstall", self)
        layout.addWidget(self.uninstall_button, 0, 1)  # type: ignore

        self.enable_button = QtWidgets.QPushButton("Enable", self)
        layout.addWidget(self.enable_button, 0, 4)  # type: ignore

        self.disable_button = QtWidgets.QPushButton("Disable", self)
        layout.addWidget(self.disable_button, 0, 5)  # type: ignore

        self.info_button = QtWidgets.QPushButton("Info", self)
        layout.addWidget(self.info_button, 0, 8)  # type: ignore

        self.refresh_button = QtWidgets.QPushButton("Refresh", self)
        layout.addWidget(self.refresh_button, 0, 9)  # type: ignore

        sublayout = QtWidgets.QHBoxLayout()  # type: ignore

        search_label = QtWidgets.QLabel("Search:", self)
        sublayout.addWidget(search_label)

        self.search_field = QtWidgets.QLineEdit(self)
        sublayout.addWidget(self.search_field)

        self.clear_button = QtWidgets.QPushButton("Clear", self)
        sublayout.addWidget(self.clear_button)

        layout.addLayout(sublayout, 1, 6, 1, 4)

        self.main_table = ModTable(self)
        layout.addWidget(self.main_table, 2, 0, 1, 10)  # type: ignore

        self.setLayout(layout)

        # buttons
        self.install_button.clicked.connect(self.install_archive)  # type: ignore
        self.uninstall_button.clicked.connect(self.uninstall)  # type: ignore
        self.enable_button.clicked.connect(self.enable)  # type: ignore
        self.disable_button.clicked.connect(self.disable)  # type: ignore
        self.refresh_button.clicked.connect(self.refresh)  # type: ignore
        self.info_button.clicked.connect(self.info)  # type: ignore
        self.main_table.doubleClicked.connect(self.info)  # type: ignore

        self.clear_button.clicked.connect(self.clear_search)  # type: ignore
        self.search_field.textChanged.connect(self.search)  # type: ignore

        # shortcuts
        shortcut_delete = QtWidgets.QShortcut(
            QtGui.QKeySequence(QtCore.Qt.Key_Delete), self  # type: ignore
        )
        shortcut_delete.activated.connect(self.uninstall)  # type: ignore

    # ======================
    # Path Selection
    # ======================

    def select_sim_path(self) -> bool:
        """
        Function to keep user in a loop until they select correct path to simulator.
        Returns if something was selected.
        """
        # prompt user to select

        result = QtWidgets.QFileDialog.getExistingDirectory(
            parent=self,
            caption="Select the root Microsoft Flight Simulator directory",
            dir=os.getenv("APPDATA"),  # type: ignore
        )

        # if nothing is selected, cancel
        if not result:
            return False

        result_path = Path(result)

        if flightsim.is_sim_root_path(result_path):
            flightsim.packages_path = result_path.joinpath("Packages")
            return True

        if flightsim.is_sim_packages_path(result_path):
            flightsim.packages_path = result_path
            return True

        # show error
        dialogs.warning.sim_path_invalid(self)
        # send them through again
        self.select_sim_path()
        return True

    def select_mod_path(self):
        pass

    # ======================
    # Install
    # ======================

    def install_archive(self):
        pass

    def install_folder(self):
        pass

    def uninstall(self):
        pass

    # ======================
    # Enable/disable
    # ======================

    def enable(self):
        pass

    def disable(self):
        pass

    # ======================
    # Data
    # ======================

    @disable_button("refresh_button")
    def refresh(self, first: bool = False):
        """
        Refresh main table data.
        """
        # temporarily clear search so that header resizing doesn't get borked
        self.search(override="")

        progress = ProgressDialog(self, self.appctxt)
        progress.set_mode(progress.PERCENT)

        all_mods_thread = Thread(flightsim.get_all_mods)
        all_mods_thread.percent_update.connect(progress.set_percent)
        all_mods_thread.activity_update.connect(progress.set_activity)

        all_mods = wait_for_thread(all_mods_thread)

        self.main_table.set_data(all_mods, first=True)
        self.main_table.set_colors(config.use_theme)

        progress.close()

        # put the search back to how it was
        self.search()

    def info(self):
        pass

    def about(self):
        """
        Launch the about dialog.
        """
        AboutDialog(self, self.appctxt).exec_()

    def versions(self):
        pass

    def check_version(self):
        pass

    # ======================
    # Search
    # ======================

    def search(self, override: str = None) -> None:
        """
        Filter rows to match search term.
        """
        # strip
        term = self.search_field.text().strip()
        # override
        if override is not None:
            term = override

        # search
        self.main_table.search(term)

    def clear_search(self) -> None:
        """
        Clear the search field.
        """
        self.search_field.clear()

    # ======================
    # Other
    # ======================

    def find_sim(self) -> None:
        """
        Sets the path to the simulator root path.
        """

        # try to automatically find the sim
        success = flightsim.find_installation()

        if success:
            return

        # show error
        dialogs.warning.sim_not_detected(self)
        # let user select folder
        selection = self.select_sim_path()

        # this function only runs at first startup
        # so if nothing is selected, exit
        if not selection:
            sys.exit()

    def create_backup(self):
        pass
