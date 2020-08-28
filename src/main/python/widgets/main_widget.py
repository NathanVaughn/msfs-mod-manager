import os
import sys

import PySide2.QtWidgets as QtWidgets

from widgets.main_table import main_table
from widgets.about_widget import about_widget
from widgets.progress_widget import progress_widget

from lib import flight_sim


class main_widget(QtWidgets.QWidget):
    def __init__(self, parent=None, appctxt=None):
        QtWidgets.QWidget.__init__(self)
        self.parent = parent
        self.appctxt = appctxt
        self.sim_path = ""

    def build(self):
        """Build layout"""
        self.layout = QtWidgets.QGridLayout()

        self.install_button = QtWidgets.QPushButton("Install", self)
        self.layout.addWidget(self.install_button, 0, 0)

        self.enable_button = QtWidgets.QPushButton("Enable", self)
        self.layout.addWidget(self.enable_button, 0, 1)

        self.disable_button = QtWidgets.QPushButton("Disable", self)
        self.layout.addWidget(self.disable_button, 0, 2)

        self.info_button = QtWidgets.QPushButton("Info", self)
        self.layout.addWidget(self.info_button, 0, 8)

        self.refresh_button = QtWidgets.QPushButton("Refresh", self)
        self.layout.addWidget(self.refresh_button, 0, 9)

        self.main_table = main_table(self)
        self.layout.addWidget(self.main_table, 1, 0, 1, 10)

        self.setLayout(self.layout)

        self.install_button.clicked.connect(self.install)
        self.enable_button.clicked.connect(self.enable)
        self.disable_button.clicked.connect(self.disable)
        self.refresh_button.clicked.connect(self.refresh)
        self.info_button.clicked.connect(self.info)
        self.main_table.doubleClicked.connect(self.info)

    def about(self):
        """Launch the about widget"""
        about_widget(self, self.appctxt).exec_()

    def get_selected_rows(self):
        """Returns a list of row indexes that are currently selected"""
        return list({index.row() for index in self.main_table.selectedIndexes()})

    def find_sim(self):
        """Sets the path to the simulator root folder"""

        def user_selection():
            """Function to keep user in a loop until they select correct folder"""
            # prompt user to select
            self.sim_path = QtWidgets.QFileDialog.getExistingDirectory(
                parent=self,
                caption="Select the root Microsoft Flight Simulator directory",
                dir=os.getenv("APPDATA"),
            )

            if not self.sim_path.strip():
                sys.exit()

            elif not flight_sim.is_sim_folder(self.sim_path):
                # show error
                QtWidgets.QMessageBox().warning(
                    self,
                    "Error",
                    "Invalid Microsoft Flight Simulator path."
                    + " Please select the root folder manually (which contains FlightSimulator.CFG)",
                )

                # send them through again
                user_selection()

        # try to automatically find the sim
        self.sim_path, success = flight_sim.find_sim_path()

        if not self.sim_path:
            # show error
            QtWidgets.QMessageBox().warning(
                self,
                "Error",
                "Microsoft Flight Simulator path could not be found."
                + " Please select the root folder manually (which contains FlightSimulator.CFG)",
            )

            user_selection()

        elif not success:
            # save the config file
            flight_sim.save_sim_path(self.sim_path)
            # notify user
            QtWidgets.QMessageBox().information(
                self,
                "Info",
                "Your Microsoft Flight Simulator folder path was automatically detected to {}".format(
                    self.sim_path
                ),
            )

    def info(self):
        """Open dialog to view mod info"""
        self.info_button.setEnabled(False)

        self.info_button.setEnabled(True)

    def install(self):
        """Installs selected mods"""
        self.install_button.setEnabled(False)

        # first, let user select multiple archives
        mod_archives = QtWidgets.QFileDialog.getOpenFileNames(
            parent=self,
            caption="Select mod archive",
            dir=os.path.join(os.path.expanduser("~"), "Downloads"),
            filter="Archives (*.zip *.rar *.tar *.bz2 *.7z)",
        )[0]

        progress = progress_widget(self, self.appctxt)
        progress.set_infinite()

        succeeded = []

        # for each archive, try to install it
        for mod_archive in mod_archives:
            try:
                succeeded.extend(flight_sim.install_mod(self.sim_path, mod_archive, update_func=progress.set_activity))
            except flight_sim.ExtractionError as e:
                QtWidgets.QMessageBox().warning(
                    self,
                    "Error",
                    "Unable to extract archive {}. You need to install a program which can extract this, such as 7zip.".format(
                        mod_archive
                    ),
                )
            except flight_sim.NoManifestError as e:
                QtWidgets.QMessageBox().warning(
                    self,
                    "Error",
                    "Unable to install mod {}. This is likely due to it missing a manifest.json file.".format(
                        mod_archive
                    ),
                )
            except flight_sim.AccessError as e:
                QtWidgets.QMessageBox().warning(
                    self,
                    "Error",
                    "Unable to install mod {} due to a permissions issue (unable to delete file/folder {}). Relaunch the program as an administrator.".format(
                        mod_archive, e
                    ),
                )
            except flight_sim.NoModsError as e:
                QtWidgets.QMessageBox().warning(
                    self,
                    "Error",
                    "Unable to find any mods inside {}".format(
                        mod_archive
                    ),
                )
            except Exception as e:
                QtWidgets.QMessageBox().warning(
                    self, "Error", "Something went terribly wrong.\n{}".format(e)
                )

        progress.close()

        if succeeded:
            QtWidgets.QMessageBox().information(
                self,
                "Success",
                "{} mod(s) installed!\n{}".format(
                    len(succeeded), "- \n".join(succeeded)
                ),
            )

        # refresh the data
        self.refresh()

        self.install_button.setEnabled(True)

    def enable(self):
        """Enables selected mods"""
        self.enable_button.setEnabled(False)

        for _id in self.get_selected_rows():
            # first, get the mod name and enabled status
            (mod_folder, enabled) = self.main_table.get_basic_info(_id)

            if enabled:
                # sanity check
                # raise Exception("Enabled mod cannot be enabled")
                QtWidgets.QMessageBox().warning(
                    self, "Warning", "Already enabled mod cannot be enabled."
                )
            else:
                # actually enable it
                flight_sim.enable_mod(self.sim_path, mod_folder)

        # refresh the data
        self.refresh()

        self.enable_button.setEnabled(True)

    def disable(self):
        """Disables selected mods"""
        self.disable_button.setEnabled(False)

        for _id in self.get_selected_rows():
            # first, get the mod name and disable status
            (mod_folder, enabled) = self.main_table.get_basic_info(_id)

            if not enabled:
                # sanity check
                # raise Exception("Disabled mod cannot be disabled")
                QtWidgets.QMessageBox().warning(
                    self, "Warning", "Already disabled mod cannot be disabled."
                )
            else:
                # actually disable it
                flight_sim.disable_mod(self.sim_path, mod_folder)

        # refresh the data
        self.refresh()

        self.disable_button.setEnabled(True)

    def refresh(self):
        """Refreshes all mod data"""
        self.refresh_button.setEnabled(False)

        try:
            enabled_mods = flight_sim.get_enabled_mods(self.sim_path)
            disabled_mods = flight_sim.get_disabled_mods()

            self.main_table.set_data(enabled_mods + disabled_mods)
        except flight_sim.NoManifestError as e:
            QtWidgets.QMessageBox().warning(
                self,
                "Error",
                "Unable to parse mod {}. This is likely due to it missing a manifest.json file.".format(
                    e
                ),
            )

        self.refresh_button.setEnabled(True)

    def contextMenuEvent(self, event):
        """Override default context menu event to provide right-click menu"""
        self.right_click_menu = QtWidgets.QMenu(self)

        enable_action = QtWidgets.QAction("Enable", self)
        enable_action.triggered.connect(self.enable)
        self.right_click_menu.addAction(enable_action)

        disable_action = QtWidgets.QAction("Disable", self)
        disable_action.triggered.connect(self.disable)
        self.right_click_menu.addAction(disable_action)

        info_action = QtWidgets.QAction("Info", self)
        info_action.triggered.connect(self.info)
        self.right_click_menu.addAction(info_action)

        # popup at cursor position
        self.right_click_menu.popup(self.mapToGlobal(event.pos()))
