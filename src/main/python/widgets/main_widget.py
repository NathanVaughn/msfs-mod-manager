import datetime
import os
import sys
import webbrowser

from loguru import logger
import PySide2.QtWidgets as QtWidgets

import lib.config as config
from lib import flight_sim, version
from lib.thread_wait import thread_wait
from widgets.about_widget import about_widget
from widgets.info_widget import info_widget
from widgets.main_table import main_table
from widgets.progress_widget import progress_widget

ARCHIVE_FILTER = "Archives (*.zip *.rar *.tar *.bz2 *.7z)"


class main_widget(QtWidgets.QWidget):
    def __init__(self, parent=None, appctxt=None):
        """Main application widget."""

        QtWidgets.QWidget.__init__(self)
        self.parent = parent
        self.appctxt = appctxt
        self.sim_folder = ""

    def build(self):
        """Build layout."""
        self.layout = QtWidgets.QGridLayout()

        self.install_button = QtWidgets.QPushButton("Install", self)
        self.layout.addWidget(self.install_button, 0, 0)

        self.uninstall_button = QtWidgets.QPushButton("Uninstall", self)
        self.layout.addWidget(self.uninstall_button, 0, 1)

        self.enable_button = QtWidgets.QPushButton("Enable", self)
        self.layout.addWidget(self.enable_button, 0, 4)

        self.disable_button = QtWidgets.QPushButton("Disable", self)
        self.layout.addWidget(self.disable_button, 0, 5)

        self.info_button = QtWidgets.QPushButton("Info", self)
        self.layout.addWidget(self.info_button, 0, 8)

        self.refresh_button = QtWidgets.QPushButton("Refresh", self)
        self.layout.addWidget(self.refresh_button, 0, 9)

        self.main_table = main_table(self)
        self.layout.addWidget(self.main_table, 1, 0, 1, 10)

        self.setLayout(self.layout)

        self.install_button.clicked.connect(self.install_archive)
        self.uninstall_button.clicked.connect(self.uninstall)
        self.enable_button.clicked.connect(self.enable)
        self.disable_button.clicked.connect(self.disable)
        self.refresh_button.clicked.connect(self.refresh)
        self.info_button.clicked.connect(self.info)
        self.main_table.doubleClicked.connect(self.info)

    def get_selected_rows(self):
        """Returns a list of row indexes that are currently selected."""
        return list({index.row() for index in self.main_table.selectedIndexes()})

    def find_sim(self):
        """Sets the path to the simulator root folder."""
        def user_selection():
            """Function to keep user in a loop until they select correct folder"""
            # prompt user to select
            self.sim_folder = QtWidgets.QFileDialog.getExistingDirectory(
                parent=self,
                caption="Select the root Microsoft Flight Simulator directory",
                dir=os.getenv("APPDATA"),
            )

            if not self.sim_folder.strip():
                sys.exit()

            elif flight_sim.is_sim_packages_folder(self.sim_folder):
                # save the config file
                config.set_key_value(config.SIM_FOLDER_KEY, self.sim_folder)

            else:
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
        (
            success,
            self.sim_folder,
        ) = flight_sim.find_sim_folder()

        if not self.sim_folder:
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
            config.set_key_value(config.SIM_FOLDER_KEY, self.sim_folder)
            # notify user
            QtWidgets.QMessageBox().information(
                self,
                "Info",
                "Your Microsoft Flight Simulator folder path was automatically detected to {}".format(
                    self.sim_folder
                ),
            )

    def check_version(self):
        """Checks the application version and allows user to open browser to update."""
        return_url = version.check_version(self.appctxt)

        if return_url:
            result = QtWidgets.QMessageBox().information(
                self,
                "Confirmation",
                "A new version is available. Would you like to go to GitHub to download it?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.Yes,
            )
            if result == QtWidgets.QMessageBox.Yes:
                webbrowser.open(return_url)

    def about(self):
        """Launch the about widget."""
        about_widget(self, self.appctxt).exec_()

    def info(self):
        """Open dialog to view mod info."""
        # self.info_button.setEnabled(False)

        selected = self.get_selected_rows()

        if selected:
            (mod_folder, enabled) = self.main_table.get_basic_info(selected[0])

            wid = info_widget(self, self.appctxt)
            wid.set_data(
                flight_sim.parse_mod_manifest(self.sim_folder, mod_folder, enabled),
                flight_sim.parse_mod_files(self.sim_folder, mod_folder, enabled),
            )
            wid.show()

        # self.info_button.setEnabled(True)

    def install_archive(self):
        """Installs selected mod archives."""
        self.install_button.setEnabled(False)

        # first, let user select multiple archives
        mod_archives = QtWidgets.QFileDialog.getOpenFileNames(
            parent=self,
            caption="Select mod archive(s)",
            dir=os.path.join(os.path.expanduser("~"), "Downloads"),
            filter=ARCHIVE_FILTER,
        )[0]

        # cancel if result was empty
        if not mod_archives:
            self.install_button.setEnabled(True)
            return

        progress = progress_widget(self, self.appctxt)
        progress.set_infinite()

        succeeded = []

        # for each archive, try to install it
        for mod_archive in mod_archives:

            def finish(result):
                # this function is required as the results will be a list,
                # which is not a hashable type
                succeeded.extend(result)

            def failed(err):
                typ = type(err)
                message = err

                if flight_sim.ExtractionError == typ:
                    QtWidgets.QMessageBox().warning(
                        self,
                        "Error",
                        "Unable to extract archive {}. You need to install a program which can extract this, such as 7zip.".format(
                            mod_archive
                        ),
                    )

                elif flight_sim.NoManifestError == typ:
                    QtWidgets.QMessageBox().warning(
                        self,
                        "Error",
                        "Unable to install mod {}. This is likely due to it missing a manifest.json file.".format(
                            mod_archive
                        ),
                    )
                elif flight_sim.AccessError == typ:
                    QtWidgets.QMessageBox().warning(
                        self,
                        "Error",
                        "Unable to install mod {} due to a permissions issue (unable to delete file/folder {}). Relaunch the program as an administrator.".format(
                            mod_archive, message
                        ),
                    )
                elif flight_sim.NoModsError == typ:
                    QtWidgets.QMessageBox().warning(
                        self,
                        "Error",
                        "Unable to find any mods inside {}".format(mod_archive),
                    )
                else:
                    logger.exception("Failed to install mod archive")
                    QtWidgets.QMessageBox().warning(
                        self,
                        "Error",
                        "Something went terribly wrong.\n{}: {}".format(typ, message),
                    )

            # setup installer thread
            installer = flight_sim.install_mod_archive_thread(
                self.sim_folder, mod_archive
            )
            installer.activity_update.connect(progress.set_activity)

            # start the thread
            with thread_wait(
                installer.finished,
                finsh_func=finish,
                failed_signal=installer.failed,
                failed_func=failed,
                update_signal=installer.activity_update,
            ):
                installer.start()

        progress.close()

        if succeeded:
            QtWidgets.QMessageBox().information(
                self,
                "Success",
                "{} mod(s) installed!\n{}".format(
                    len(succeeded), "\n".join(["- {}".format(mod) for mod in succeeded])
                ),
            )

        # refresh the data
        self.refresh()

        self.install_button.setEnabled(True)

    def install_folder(self):
        """Installs selected mod folders."""
        # self.install_button.setEnabled(False)

        # first, let user select multiple folders
        mod_folder = QtWidgets.QFileDialog.getExistingDirectory(
            parent=self,
            caption="Select mod folder",
            dir=os.path.join(os.path.expanduser("~"), "Downloads"),
        )

        # cancel if result was empty
        if not mod_folder:
            return

        progress = progress_widget(self, self.appctxt)
        progress.set_infinite()

        succeeded = []

        def finish(result):
            # this function is required as the results will be a list,
            # which is not a hashable type
            succeeded.extend(result)

        def failed(err):
            typ = type(err)
            message = err

            if flight_sim.NoManifestError == typ:
                QtWidgets.QMessageBox().warning(
                    self,
                    "Error",
                    "Unable to install mod {}. This is likely due to it missing a manifest.json file.".format(
                        mod_folder
                    ),
                )
            elif flight_sim.AccessError == typ:
                QtWidgets.QMessageBox().warning(
                    self,
                    "Error",
                    "Unable to install mod {} due to a permissions issue (unable to delete file/folder {}). Relaunch the program as an administrator.".format(
                        mod_folder, message
                    ),
                )
            elif flight_sim.NoModsError == typ:
                QtWidgets.QMessageBox().warning(
                    self,
                    "Error",
                    "Unable to find any mods inside {}".format(mod_folder),
                )
            else:
                logger.exception("Failed to install mod folder")
                QtWidgets.QMessageBox().warning(
                    self,
                    "Error",
                    "Something went terribly wrong.\n{}: {}".format(typ, message),
                )

        # setup installer thread
        installer = flight_sim.install_mods_thread(self.sim_folder, mod_folder)
        installer.activity_update.connect(progress.set_activity)

        # start the thread
        with thread_wait(
            installer.finished,
            finsh_func=finish,
            failed_signal=installer.failed,
            failed_func=failed,
            update_signal=installer.activity_update,
        ):
            installer.start()

        progress.close()

        if succeeded:
            QtWidgets.QMessageBox().information(
                self,
                "Success",
                "{} mod(s) installed!\n{}".format(
                    len(succeeded), "\n".join(["- {}".format(mod) for mod in succeeded])
                ),
            )

        # refresh the data
        self.refresh()

        # self.install_button.setEnabled(True)

    def uninstall(self):
        """Uninstalls selected mods."""
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
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No,
            )
            if result == QtWidgets.QMessageBox.No:
                self.uninstall_button.setEnabled(True)
                return

        progress = progress_widget(self, self.appctxt)
        progress.set_infinite()

        for _id in self.get_selected_rows():
            # first, get the mod name and enabled status
            (mod_folder, enabled) = self.main_table.get_basic_info(_id)

            # setup uninstaller thread
            uninstaller = flight_sim.uninstall_mod_thread(
                self.sim_folder, mod_folder, enabled
            )
            uninstaller.activity_update.connect(progress.set_activity)

            def failed(err):
                typ = type(err)
                message = err

                logger.exception("Failed to uninstall mod")
                QtWidgets.QMessageBox().warning(
                    self,
                    "Error",
                    "Something went terribly wrong.\n{}: {}".format(typ, message),
                )

            # start the thread
            with thread_wait(
                uninstaller.finished,
                failed_signal=uninstaller.failed,
                failed_func=failed,
                update_signal=uninstaller.activity_update,
            ):
                uninstaller.start()

        # refresh the data
        self.refresh()

        self.uninstall_button.setEnabled(True)

    def enable(self):
        """Enables selected mods."""
        self.enable_button.setEnabled(False)

        progress = progress_widget(self, self.appctxt)
        progress.set_infinite()

        for _id in self.get_selected_rows():
            # first, get the mod name and enabled status
            (mod_folder, enabled) = self.main_table.get_basic_info(_id)

            if enabled:
                continue

            # setup enabler thread
            enabler = flight_sim.enable_mod_thread(self.sim_folder, mod_folder)
            enabler.activity_update.connect(progress.set_activity)

            def failed(err):
                typ = type(err)
                message = err

                logger.exception("Failed to enable mod")
                QtWidgets.QMessageBox().warning(
                    self,
                    "Error",
                    "Something went terribly wrong.\n{}: {}".format(typ, message),
                )

            # start the thread
            with thread_wait(
                enabler.finished,
                failed_signal=enabler.failed,
                failed_func=failed,
                update_signal=enabler.activity_update,
            ):
                enabler.start()

        # refresh the data
        self.refresh()

        progress.close()
        self.enable_button.setEnabled(True)

    def disable(self):
        """Disables selected mods."""
        self.disable_button.setEnabled(False)

        progress = progress_widget(self, self.appctxt)
        progress.set_infinite()

        for _id in self.get_selected_rows():
            # first, get the mod name and disable status
            (mod_folder, enabled) = self.main_table.get_basic_info(_id)

            if not enabled:
                continue

            # setup disabler thread
            disabler = flight_sim.disable_mod_thread(self.sim_folder, mod_folder)
            disabler.activity_update.connect(progress.set_activity)

            def failed(err):
                typ = type(err)
                message = err

                logger.exception("Failed to disable mod")
                QtWidgets.QMessageBox().warning(
                    self,
                    "Error",
                    "Something went terribly wrong.\n{}: {}".format(typ, message),
                )

            # start the thread
            with thread_wait(
                disabler.finished,
                failed_signal=disabler.failed,
                failed_func=failed,
                update_signal=disabler.activity_update,
            ):
                disabler.start()

        # refresh the data
        self.refresh()

        progress.close()
        self.disable_button.setEnabled(True)

    def create_backup(self):
        """Creates a backup of all enabled mods."""

        archive = QtWidgets.QFileDialog.getSaveFileName(
            parent=self,
            caption="Save Backup As",
            dir=os.path.join(
                config.BASE_FOLDER,
                "msfs-mod-backup-{}.zip".format(
                    datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                ),
            ),
            filter=ARCHIVE_FILTER,
        )[0]

        # no selection will be blank
        if not archive:
            return

        progress = progress_widget(self, self.appctxt)
        progress.set_infinite()

        # setup backuper thread
        backuper = flight_sim.create_backup_thread(self.sim_folder, archive)
        backuper.activity_update.connect(progress.set_activity)

        def failed(err):
            typ = type(err)
            message = err

            if flight_sim.ExtractionError == typ:
                QtWidgets.QMessageBox().warning(
                    self,
                    "Error",
                    "Unable to create archive {}. You need to install a program which can create this, such as 7zip or WinRar.".format(
                        archive
                    ),
                )
            else:
                logger.exception("Failed to create backup")
                QtWidgets.QMessageBox().warning(
                    self,
                    "Error",
                    "Something went terribly wrong.\n{}: {}".format(typ, message),
                )

        # start the thread, with extra 20 min timeout
        with thread_wait(
            backuper.finished,
            timeout=1200000,
            failed_signal=backuper.failed,
            failed_func=failed,
            update_signal=backuper.activity_update,
        ):
            backuper.start()

        result = QtWidgets.QMessageBox().information(
            self,
            "Success",
            "Backup successfully saved to {}. Would you like to open this directory?".format(
                archive
            ),
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.Yes,
        )
        # open resulting directory
        if result == QtWidgets.QMessageBox.Yes:
            # this will always be opening a folder and therefore is safe
            os.startfile(os.path.dirname(archive)) # nosec

    def refresh(self, first=False):
        """Refreshes all mod data."""
        self.refresh_button.setEnabled(False)

        enabled_mods, enabled_errors = flight_sim.get_enabled_mods(self.sim_folder)
        disabled_mods, disabled_errors = flight_sim.get_disabled_mods(self.sim_folder)

        total_errors = enabled_errors + disabled_errors

        self.main_table.set_data(enabled_mods + disabled_mods, first=first)
        self.main_table.set_colors(self.parent.theme_menu_action.isChecked())

        if total_errors:
            QtWidgets.QMessageBox().warning(
                self,
                "Error",
                "Unable to parse mod(s):\n{} \nThis is likely due to a missing manifest.json file.".format(
                    "\n".join(["- {}".format(error) for error in total_errors])
                ),
            )

        self.refresh_button.setEnabled(True)
