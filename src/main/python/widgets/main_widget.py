import functools
import os
import sys
from pathlib import Path

from fbs_runtime.application_context.PySide2 import ApplicationContext
from loguru import logger
from PySide2 import QtCore, QtGui, QtWidgets

import dialogs.error
import dialogs.information
import dialogs.warning
from dialogs.about import AboutDialog
from dialogs.progress import ProgressDialog
from dialogs.versions_info import VersionsInfoDialog
from lib.config import config
from lib.flightsim import disable_mods, enable_mods, flightsim, uninstall_mods
from lib.thread import Thread, wait_for_thread
from widgets.mod_info_widget import ModInfoWidget
from widgets.mod_table import ModTable

ARCHIVE_FILTER = "Archives (*.zip *.rar *.tar *.bz2 *.7z)"

# ======================
# Decorators
# ======================


def disable_button(button_name: str):
    """
    Decorator to disable a given button name before function execution
    and re-enable it after the function is done.
    """

    def decorator(func):
        def wrapper(self, *args, **kwargs):
            button: QtWidgets.QPushButton = getattr(self, button_name)

            button.setEnabled(False)
            output = func(self, *args, **kwargs)
            button.setEnabled(True)

            return output

        return wrapper

    return decorator


def try_except():
    """
    Decorator to display a dialog box if an uncaught exception occurs.
    """

    def decorator(func):
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                logger.exception(e)
                dialogs.error.general(self, e)

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

    def find_sim_path(self) -> None:
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
        raise NotImplementedError

    # ======================
    # Install
    # ======================

    def install_archive(self):
        raise NotImplementedError

    def install_folder(self):
        raise NotImplementedError

    @disable_button("uninstall_button")
    @try_except()
    def uninstall(self):
        """
        Uninstall the selected Mod objects.
        """
        logger.debug("Uninstall button clicked")

        mods = self.main_table.get_selected_row_objects()
        if not mods:
            return

        progress = ProgressDialog(self, self.appctxt)
        progress.set_mode(progress.PERCENT)

        enable_mods_thread = Thread(functools.partial(uninstall_mods, mods))
        enable_mods_thread.percent_update.connect(progress.set_percent)
        enable_mods_thread.activity_update.connect(progress.set_activity)

        wait_for_thread(enable_mods_thread)

        progress.close()
        self.refresh()

    # ======================
    # Enable/disable
    # ======================

    @disable_button("enable_button")
    @try_except()
    def enable(self):
        """
        Enable the selected Mod objects.
        """
        logger.debug("Enable button clicked")

        mods = self.main_table.get_selected_row_objects()
        if not mods:
            return

        if all(mod.enabled for mod in mods):
            # all mods selected already enabled
            return

        progress = ProgressDialog(self, self.appctxt)
        progress.set_mode(progress.PERCENT)

        enable_mods_thread = Thread(functools.partial(enable_mods, mods))
        enable_mods_thread.percent_update.connect(progress.set_percent)
        enable_mods_thread.activity_update.connect(progress.set_activity)

        wait_for_thread(enable_mods_thread)

        progress.close()
        self.refresh()

    @disable_button("disable_button")
    @try_except()
    def disable(self):
        """
        Disable the selected Mod objects.
        """
        logger.debug("Disable button clicked")

        mods = self.main_table.get_selected_row_objects()
        if not mods:
            return

        if all(not mod.enabled for mod in mods):
            # all mods selected already disabled
            return

        progress = ProgressDialog(self, self.appctxt)
        progress.set_mode(progress.PERCENT)

        disable_mods_thread = Thread(functools.partial(disable_mods, mods))
        disable_mods_thread.percent_update.connect(progress.set_percent)
        disable_mods_thread.activity_update.connect(progress.set_activity)

        wait_for_thread(disable_mods_thread)

        progress.close()
        self.refresh()

    # ======================
    # Data
    # ======================

    @disable_button("refresh_button")
    @try_except()
    def refresh(self, first: bool = False):
        """
        Refresh main table data.
        """
        if not first:
            logger.debug("Refresh button clicked")

        # temporarily clear search so that header resizing doesn't get borked
        self.search(override="")

        progress = ProgressDialog(self, self.appctxt)
        progress.set_mode(progress.PERCENT)

        all_mods_thread = Thread(flightsim.get_all_mods)
        all_mods_thread.percent_update.connect(progress.set_percent)
        all_mods_thread.activity_update.connect(progress.set_activity)

        all_mods, parsing_errors = wait_for_thread(all_mods_thread)

        self.main_table.set_data(all_mods, first=first)
        self.main_table.set_colors(config.use_theme)

        progress.close()

        # put the search back to how it was
        self.search()

        if parsing_errors:
            dialogs.warning.mod_parsing(self, parsing_errors)

    def info(self):
        """
        Launch the info widget for the selected Mod.
        """
        logger.debug("Info button clicked")

        mods = self.main_table.get_selected_row_objects()
        if not mods:
            return

        mod = mods[0]
        mod.load_files()

        ModInfoWidget(self, self.appctxt, mod).show()

    def about(self):
        """
        Launch the about dialog.
        """
        logger.debug("Launching about dialog")
        AboutDialog(self, self.appctxt).exec_()

    def version_info(self):
        """
        Launch the version info dialog.
        """
        logger.debug("Launching versions info dialog")
        VersionsInfoDialog(self, self.appctxt).exec_()

    def check_version(self):
        raise NotImplementedError

    # ======================
    # Search
    # ======================

    def search(self, override: str = None) -> None:
        """
        Filter rows to match search term.
        """
        logger.debug("Search button clicked")

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
        logger.debug("Clear search button clicked")
        self.search_field.clear()

    # ======================
    # Other
    # ======================

    def create_backup(self):
        raise NotImplementedError
