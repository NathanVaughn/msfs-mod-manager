import os
import sys

import PySide2.QtWidgets as QtWidgets

from lib import flight_sim
from widgets.about_widget import about_widget
from widgets.main_table import main_table
from widgets.progress_widget import progress_widget
from lib.thread_wait import thread_wait


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

        self.uninstall_button = QtWidgets.QPushButton("Uninstall", self)
        self.layout.addWidget(self.uninstall_button, 0, 1)

        self.enable_button = QtWidgets.QPushButton("Enable", self)
        self.layout.addWidget(self.enable_button, 0, 4)

        self.disable_button = QtWidgets.QPushButton("Disable", self)
        self.layout.addWidget(self.disable_button, 0, 5)

        # self.info_button = QtWidgets.QPushButton("Info", self)
        # self.layout.addWidget(self.info_button, 0, 8)

        self.refresh_button = QtWidgets.QPushButton("Refresh", self)
        self.layout.addWidget(self.refresh_button, 0, 9)

        self.main_table = main_table(self)
        self.layout.addWidget(self.main_table, 1, 0, 1, 10)

        self.setLayout(self.layout)

        self.install_button.clicked.connect(self.install)
        self.uninstall_button.clicked.connect(self.uninstall)
        self.enable_button.clicked.connect(self.enable)
        self.disable_button.clicked.connect(self.disable)
        self.refresh_button.clicked.connect(self.refresh)
        # self.info_button.clicked.connect(self.info)
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

            elif not flight_sim.is_sim_packages_folder(self.sim_path):
                # show error
                QtWidgets.QMessageBox().warning(
                    self,
                    "Error",
                    "Invalid Microsoft Flight Simulator path."
                    + " Please select the Packages folder manually"
                    + " (which contains the Official and Community folders).",
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
                + " Please select the Packages folder manually"
                + " (which contains the Official and Community folders).",
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

                def finish(result):
                    # this function is required as the results will be a list,
                    # which is not a hashable type
                    succeeded.extend(result)

                # setup installer thread
                installer = flight_sim.install_mod_thread(self.sim_path, mod_archive)
                installer.activity_update.connect(progress.set_activity)

                # start the thread
                with thread_wait(installer.finished, finsh_func=finish):
                    installer.start()

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
                    "Unable to find any mods inside {}".format(mod_archive),
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

    def uninstall(self):
        """Uninstalls selected mods"""
        self.uninstall_button.setEnabled(False)

        selected = self.get_selected_rows()

        if selected:
            # sanity check
            result = QtWidgets.QMessageBox().information(
                self,
                "Confirmation",
                "This will permamentaly delete {} mod(s). Are you sure you want to continue?".format(
                    len(selected)
                ),
                QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel,
                QtWidgets.QMessageBox.Cancel,
            )
            if result == QtWidgets.QMessageBox.Cancel:
                self.uninstall_button.setEnabled(True)
                return

        progress = progress_widget(self, self.appctxt)
        progress.set_infinite()

        for _id in self.get_selected_rows():
            # first, get the mod name and enabled status
            (mod_folder, enabled) = self.main_table.get_basic_info(_id)

            # setup uninstaller thread
            uninstaller = flight_sim.uninstall_mod_thread(
                self.sim_path, mod_folder, enabled
            )
            uninstaller.activity_update.connect(progress.set_activity)

            # start the thread
            with thread_wait(uninstaller.finished):
                uninstaller.start()

        # refresh the data
        self.refresh()

        self.install_button.setEnabled(True)

    def enable(self):
        """Enables selected mods"""
        self.enable_button.setEnabled(False)

        progress = progress_widget(self, self.appctxt)
        progress.set_infinite()

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
                # setup enabler thread
                enabler = flight_sim.enable_mod_thread(self.sim_path, mod_folder)
                enabler.activity_update.connect(progress.set_activity)

                # start the thread
                with thread_wait(enabler.finished):
                    enabler.start()

        # refresh the data
        self.refresh()

        progress.close()
        self.enable_button.setEnabled(True)

    def disable(self):
        """Disables selected mods"""
        self.disable_button.setEnabled(False)

        progress = progress_widget(self, self.appctxt)
        progress.set_infinite()

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
                # setup disabler thread
                disabler = flight_sim.disable_mod_thread(self.sim_path, mod_folder)
                disabler.activity_update.connect(progress.set_activity)

                # start the thread
                with thread_wait(disabler.finished):
                    disabler.start()

        # refresh the data
        self.refresh()

        progress.close()
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

        # info_action = QtWidgets.QAction("Info", self)
        # info_action.triggered.connect(self.info)
        # self.right_click_menu.addAction(info_action)

        # popup at cursor position
        self.right_click_menu.popup(self.mapToGlobal(event.pos()))
