from __future__ import annotations

import functools
import os
import sys
from pathlib import Path
from typing import Any, Callable

from loguru import logger
from PySide6 import QtCore, QtGui, QtWidgets

from ..dialogs import error, success, warning
from ..dialogs.about import AboutDialog
from ..dialogs.mod_info import ModInfoDialog
from ..dialogs.progress import ProgressDialog
from ..dialogs.versions_info import VersionsInfoDialog
from ..lib.config import config
from ..lib.flightsim import flightsim
from ..lib.thread import Thread, wait_for_thread
from .mod_table import ModTable

ARCHIVE_FILTER = "Archives (*.zip *.rar *.tar *.bz2 *.7z)"

# ======================
# Decorators
# ======================


def disable_button(button_name: str) -> Callable:
    """
    Decorator to disable a given button name before function execution
    and re-enable it after the function is done.
    I don't like how this is done, but couldn't find a better way
    to modify class variables.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self: MainWidget, *args, **kwargs) -> Any:
            button: QtWidgets.QPushButton = getattr(self, button_name)

            button.setEnabled(False)
            output = func(self, *args, **kwargs)
            button.setEnabled(True)

            return output

        return wrapper

    return decorator


def error_catch() -> Callable:
    """
    Decorator to display a dialog box if an uncaught exception occurs.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self: MainWidget, *args, **kwargs) -> Any:
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                logger.exception(e)
                error.general(self, e)

        return wrapper

    return decorator


class MainWidget(QtWidgets.QWidget):
    """
    Main application widget.
    """

    def __init__(self, parent: QtWidgets.QWidget, qapp: QtWidgets.QApplication) -> None:
        super().__init__(parent=parent)
        self.parent_ = parent
        self.qapp = qapp

        layout = QtWidgets.QGridLayout(self)

        # layouts don't work with keyword arguments ????

        self.install_button = QtWidgets.QPushButton("Install", self)
        layout.addWidget(self.install_button, 0, 0)

        self.uninstall_button = QtWidgets.QPushButton("Uninstall", self)
        layout.addWidget(self.uninstall_button, 0, 1)

        self.enable_button = QtWidgets.QPushButton("Enable", self)
        layout.addWidget(self.enable_button, 0, 4)

        self.disable_button = QtWidgets.QPushButton("Disable", self)
        layout.addWidget(self.disable_button, 0, 5)

        self.info_button = QtWidgets.QPushButton("Info", self)
        layout.addWidget(self.info_button, 0, 8)

        self.refresh_button = QtWidgets.QPushButton("Refresh", self)
        layout.addWidget(self.refresh_button, 0, 9)

        sublayout = QtWidgets.QHBoxLayout()

        search_label = QtWidgets.QLabel("Search:", self)
        sublayout.addWidget(search_label)

        self.search_field = QtWidgets.QLineEdit(self)
        sublayout.addWidget(self.search_field)

        self.clear_button = QtWidgets.QPushButton("Clear", self)
        sublayout.addWidget(self.clear_button)

        layout.addLayout(sublayout, 1, 6, 1, 4)

        self.main_table = ModTable(self)
        layout.addWidget(self.main_table, 2, 0, 1, 10)

        self.setLayout(layout)

        # buttons
        # slots aren't type correctly still
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
        shortcut_delete = QtGui.QShortcut(
            QtGui.QKeySequence(QtCore.Qt.Key_Delete), self
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
        if flightsim.find_installation():
            return

        # show error
        warning.sim_not_detected(self)
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
            dir=os.environ["APPDATA"],
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
        warning.sim_path_invalid(self)
        # send them through again
        self.select_sim_path()
        return True

    def select_mod_path(self) -> None:
        raise NotImplementedError

    # ======================
    # Install
    # ======================

    @disable_button("install_button")
    @error_catch()
    def install_archive(self) -> None:
        """
        Install the selected archives
        """
        logger.debug("Install button clicked")

        mod_archives = QtWidgets.QFileDialog.getOpenFileNames(
            parent=self,
            caption="Select mod archive(s)",
            dir=str(config.last_opened_path),
            filter=ARCHIVE_FILTER,
        )[0]

        # cancel if nothing is selected
        if len(mod_archives) == 0:
            return

        # convert strings to Paths
        mod_archives = [Path(a) for a in mod_archives]

        # set the last opened folder, based off the parent directory
        # of the first item in the list
        config.last_opened_path = mod_archives[0].parent

        progress = ProgressDialog(self, self.qapp)
        progress.set_mode(progress.PERCENT)

        install_mod_archives_thread = Thread(
            functools.partial(flightsim.install_archives, mod_archives)
        )
        install_mod_archives_thread.percent_update.connect(progress.set_percent)
        install_mod_archives_thread.activity_update.connect(progress.set_activity)

        mods_installed = wait_for_thread(install_mod_archives_thread)

        progress.close()

        success.mods_installed(self, mods_installed)

        self.refresh()

    @error_catch()
    def install_folder(self) -> None:
        mod_folder = QtWidgets.QFileDialog.getExistingDirectory(
            parent=self,
            caption="Select mod folder",
            dir=str(config.last_opened_path),
        )

        # cancel if nothing is selected
        if mod_folder == "":
            return

        # convert string to Path
        mod_folder = Path(mod_folder)

        # set the last opened folder, based off the parent directory
        config.last_opened_path = mod_folder.parent

        progress = ProgressDialog(self, self.qapp)
        progress.set_mode(progress.PERCENT)

        install_mod_folder_thread = Thread(
            functools.partial(flightsim.install_directory, mod_folder)
        )
        install_mod_folder_thread.percent_update.connect(progress.set_percent)
        install_mod_folder_thread.activity_update.connect(progress.set_activity)

        mods_installed = wait_for_thread(install_mod_folder_thread)

        progress.close()

        success.mods_installed(self, mods_installed)

        self.refresh()

    @disable_button("uninstall_button")
    @error_catch()
    def uninstall(self) -> None:
        """
        Uninstall the selected Mod objects.
        """
        logger.debug("Uninstall button clicked")

        mods = self.main_table.get_selected_row_objects()
        if not mods:
            return

        if not warning.mod_uninstalls(self, mods):
            return

        progress = ProgressDialog(self, self.qapp)
        progress.set_mode(progress.PERCENT)

        uninstall_mods_thread = Thread(
            functools.partial(flightsim.uninstall_mods, mods)
        )
        uninstall_mods_thread.percent_update.connect(progress.set_percent)
        uninstall_mods_thread.activity_update.connect(progress.set_activity)

        wait_for_thread(uninstall_mods_thread)

        progress.close()
        self.refresh()

    # ======================
    # Enable/disable
    # ======================

    @disable_button("enable_button")
    @error_catch()
    def enable(self) -> None:
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

        progress = ProgressDialog(self, self.qapp)
        progress.set_mode(progress.PERCENT)

        enable_mods_thread = Thread(functools.partial(flightsim.enable_mods, mods))
        enable_mods_thread.percent_update.connect(progress.set_percent)
        enable_mods_thread.activity_update.connect(progress.set_activity)

        wait_for_thread(enable_mods_thread)

        progress.close()
        self.refresh()

    @disable_button("disable_button")
    @error_catch()
    def disable(self) -> None:
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

        progress = ProgressDialog(self, self.qapp)
        progress.set_mode(progress.PERCENT)

        disable_mods_thread = Thread(functools.partial(flightsim.disable_mods, mods))
        disable_mods_thread.percent_update.connect(progress.set_percent)
        disable_mods_thread.activity_update.connect(progress.set_activity)

        wait_for_thread(disable_mods_thread)

        progress.close()
        self.refresh()

    # ======================
    # Data
    # ======================

    @disable_button("refresh_button")
    @error_catch()
    def refresh(self, first: bool = False) -> None:
        """
        Refresh main table data.
        """
        if not first:
            logger.debug("Refresh button clicked")

        # temporarily clear search so that header resizing doesn't get borked
        self.search(override="")

        progress = ProgressDialog(self, self.qapp)
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
            warning.mod_parsing(self, parsing_errors)

    def info(self) -> None:
        """
        Launch the info widget for the selected Mod.
        """
        logger.debug("Info button clicked")

        mods = self.main_table.get_selected_row_objects()
        if not mods:
            return

        mod = mods[0]
        mod.load_files()

        ModInfoDialog(self, self.qapp, mod).exec()

    def about(self) -> None:
        """
        Launch the about dialog.
        """
        logger.debug("Launching about dialog")
        AboutDialog(self, self.qapp).exec()

    def version_info(self) -> None:
        """
        Launch the version info dialog.
        """
        logger.debug("Launching versions info dialog")
        VersionsInfoDialog(self, self.qapp).exec()

    def check_version(self) -> None:
        raise NotImplementedError

    # ======================
    # Search
    # ======================

    def search(self, override: str = None) -> None:
        """
        Filter rows to match search term.
        """
        if override is not None:
            # don't print to log if override is set
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

    def create_backup(self) -> None:
        raise NotImplementedError
