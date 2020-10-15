import datetime
import os
import sys
import webbrowser

import PySide2.QtWidgets as QtWidgets
from loguru import logger

import lib.config as config
import lib.files as files
import lib.flight_sim as flight_sim
import lib.thread as thread
import lib.version as version
from widgets.about_widget import about_widget
from widgets.info_widget import info_widget
from widgets.main_table import main_table
from widgets.progress_widget import progress_widget
from widgets.versions_widget import versions_widget
import dialogs.error_dialogs as error_dialogs
import dialogs.warning_dialogs as warning_dialogs
import dialogs.question_dialogs as question_dialogs
import dialogs.information_dialogs as information_dialogs
from dialogs.version_check_dialog import version_check_dialog

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

        self.sublayout = QtWidgets.QHBoxLayout()

        self.search_label = QtWidgets.QLabel("Search:", self)
        self.sublayout.addWidget(self.search_label)

        self.search_field = QtWidgets.QLineEdit(self)
        self.sublayout.addWidget(self.search_field)

        self.clear_button = QtWidgets.QPushButton("Clear", self)
        self.sublayout.addWidget(self.clear_button)

        self.layout.addLayout(self.sublayout, 1, 6, 1, 4)

        self.main_table = main_table(self)
        self.layout.addWidget(self.main_table, 2, 0, 1, 10)

        self.setLayout(self.layout)

        self.install_button.clicked.connect(self.install_archive)
        self.uninstall_button.clicked.connect(self.uninstall)
        self.enable_button.clicked.connect(self.enable)
        self.disable_button.clicked.connect(self.disable)
        self.refresh_button.clicked.connect(self.refresh)
        self.info_button.clicked.connect(self.info)
        self.main_table.doubleClicked.connect(self.info)

        self.clear_button.clicked.connect(self.clear_search)
        self.search_field.textChanged.connect(self.search)

    def find_sim(self):
        """Sets the path to the simulator root folder."""

        def user_selection():
            """Function to keep user in a loop until they select correct folder."""
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
                warning_dialogs.sim_path_invalid(self)
                # send them through again
                user_selection()

        # try to automatically find the sim
        (success, self.sim_folder,) = flight_sim.find_sim_folder()

        if not self.sim_folder:
            # show error
            warning_dialogs.sim_not_detected(self)
            # let user select folder
            user_selection()

        elif not success:
            # save the config file
            config.set_key_value(config.SIM_FOLDER_KEY, self.sim_folder)
            # notify user
            information_dialogs.sim_detected(self, self.sim_folder)

    def check_version(self):
        """Checks the application version and allows user to open browser to update."""
        installed = version.is_installed()
        return_url = version.check_version(self.appctxt, installed)

        if return_url:
            result, remember = version_check_dialog(self, installed).exec_()
            if result:
                if installed:
                    # progress bar
                    progress = progress_widget(self, self.appctxt)
                    progress.set_percent()
                    progress.set_activity(
                        "Downloading latest version ({})".format(return_url)
                    )

                    # setup downloader thread
                    downloader = version.download_new_version_thread(return_url)
                    downloader.activity_update.connect(progress.set_percentage)

                    def failed(err):
                        typ = type(err)
                        message = err

                        logger.exception("Failed to download new version")
                        error_dialogs.general(self, typ, message)

                    # start the thread
                    with thread.thread_wait(
                        downloader.finished,
                        finish_func=version.install_new_version,
                        failed_signal=downloader.failed,
                        failed_func=failed,
                        update_signal=downloader.activity_update,
                    ):
                        downloader.start()

                    progress.close()
                else:
                    webbrowser.open(return_url)
            elif remember:
                config.set_key_value(config.NEVER_VER_CHEK_KEY, True)

    def select_mod_cache(self):
        """Allow user to select new mod cache folder"""
        selection = QtWidgets.QFileDialog.getExistingDirectory(
            parent=self,
            caption="Select disabled mod folder",
            dir=files.get_mod_cache_folder(),
        )

        if selection:
            config.set_key_value(config.MOD_CACHE_FOLDER_KEY, selection)
            information_dialogs.disabled_mods_folder(self, selection)
            self.refresh()

    def about(self):
        """Launch the about widget."""
        about_widget(self, self.appctxt).exec_()

    def versions(self):
        """Launch the versions widget."""
        versions_widget(self.sim_folder, self, self.appctxt).exec_()

    def info(self):
        """Open dialog to view mod info."""
        # self.info_button.setEnabled(False)

        selected = self.main_table.get_selected_rows()

        if selected:
            (mod_folder, enabled) = self.main_table.get_basic_info(selected[0])

            wid = info_widget(self, self.appctxt)
            wid.set_data(
                flight_sim.parse_mod_manifest(self.sim_folder, mod_folder, enabled),
                flight_sim.parse_mod_files(self.sim_folder, mod_folder, enabled),
            )
            wid.show()

        # self.info_button.setEnabled(True)

    def base_fail(self, error, mapping, fallback_text):
        """Base thread failure function."""
        typ = type(error)
        message = error

        if typ not in mapping:
            logger.exception(fallback_text)
            error_dialogs.general(self, typ, message)
        else:
            func = mapping[typ]
            func()

    def base_action(
        self,
        core_func,
        button=None,
        sanity_dialog=None,
        empty_check=False,
        empty_val=None,
    ):
        """Base function for GUI actions."""
        if empty_check and not empty_val:
            return

        if button:
            button.setEnabled(False)

        # sanity check
        if sanity_dialog:
            question = sanity_dialog()
            if not question:
                # cancel
                button.setEnabled(True)
                return

        # build progress widget
        progress = progress_widget(self, self.appctxt)
        progress.set_infinite()

        # execute the core function
        core_func(progress)

        # refresh the data
        self.refresh()

        # cleanup
        progress.close()
        if button:
            button.setEnabled(True)

    def install_archive(self):
        """Installs selected mod archives."""

        # first, let user select multiple archives
        mod_archives = QtWidgets.QFileDialog.getOpenFileNames(
            parent=self,
            caption="Select mod archive(s)",
            dir=files.get_last_open_folder(),
            filter=ARCHIVE_FILTER,
        )[0]

        succeeded = []

        def core(progress):
            # for each archive, try to install it
            for mod_archive in mod_archives:

                def finish(result):
                    # this function is required as the results will be a list,
                    # which is not a hashable type
                    succeeded.extend(result)

                def failed(error):
                    mapping = {
                        flight_sim.ExtractionError: lambda: error_dialogs.archive_extract(
                            self, mod_archive
                        ),
                        flight_sim.NoManifestError: lambda: warning_dialogs.mod_parsing(
                            self, [mod_archive]
                        ),
                        files.AccessError: lambda: error_dialogs.permission(
                            self, mod_archive, error
                        ),
                        flight_sim.NoModsError: lambda: error_dialogs.no_mods(
                            self, mod_archive
                        ),
                    }

                    self.base_fail(
                        error, mapping, "Failed to install mod archive",
                    )

                # setup installer thread
                installer = flight_sim.install_mod_archive_thread(
                    self.sim_folder, mod_archive
                )
                installer.activity_update.connect(progress.set_activity)

                # start the thread
                with thread.thread_wait(
                    installer.finished,
                    finish_func=finish,
                    failed_signal=installer.failed,
                    failed_func=failed,
                    update_signal=installer.activity_update,
                ):
                    installer.start()

        self.base_action(
            core, button=self.install_button, empty_check=True, empty_val=mod_archives,
        )

        if succeeded:
            config.set_key_value(
                config.LAST_OPEN_FOLDER_KEY, os.path.dirname(mod_archives[0])
            )
            information_dialogs.mods_installed(self, succeeded)

    def install_folder(self):
        """Installs selected mod folders."""

        # first, let user select a folder
        mod_folder = QtWidgets.QFileDialog.getExistingDirectory(
            parent=self, caption="Select mod folder", dir=files.get_last_open_folder(),
        )

        succeeded = []

        def core(progress):
            def finish(result):
                # this function is required as the results will be a list,
                # which is not a hashable type
                succeeded.extend(result)

            def failed(error):
                mapping = {
                    flight_sim.NoManifestError: lambda: warning_dialogs.mod_parsing(
                        self, [mod_folder]
                    ),
                    files.AccessError: lambda: error_dialogs.permission(
                        self, mod_folder, error
                    ),
                    flight_sim.NoModsError: lambda: error_dialogs.no_mods(
                        self, mod_folder
                    ),
                }

                self.base_fail(
                    error, mapping, "Failed to install mod folder",
                )

            # setup installer thread
            installer = flight_sim.install_mods_thread(self.sim_folder, mod_folder)
            installer.activity_update.connect(progress.set_activity)

            # start the thread
            with thread.thread_wait(
                installer.finished,
                finish_func=finish,
                failed_signal=installer.failed,
                failed_func=failed,
                update_signal=installer.activity_update,
            ):
                installer.start()

        self.base_action(
            core, button=self.install_button, empty_check=True, empty_val=mod_folder,
        )

        if succeeded:
            config.set_key_value(
                config.LAST_OPEN_FOLDER_KEY, os.path.dirname(mod_folder)
            )
            information_dialogs.mods_installed(self, succeeded)

    def uninstall(self):
        """Uninstalls selected mods."""
        selected = self.main_table.get_selected_rows()

        def core(progress):
            for _id in selected:
                # first, get the mod name and enabled status
                (mod_folder, enabled) = self.main_table.get_basic_info(_id)

                # setup uninstaller thread
                uninstaller = flight_sim.uninstall_mod_thread(
                    self.sim_folder, mod_folder, enabled
                )
                uninstaller.activity_update.connect(progress.set_activity)

                def failed(error):
                    self.base_fail(error, {}, "Failed to uninstall mod")

                # start the thread
                with thread.thread_wait(
                    uninstaller.finished,
                    failed_signal=uninstaller.failed,
                    failed_func=failed,
                    update_signal=uninstaller.activity_update,
                ):
                    uninstaller.start()

        self.base_action(
            core,
            button=self.uninstall_button,
            sanity_dialog=lambda: question_dialogs.mod_delete(self, len(selected)),
            empty_check=True,
            empty_val=selected,
        )

    def enable(self):
        """Enables selected mods."""
        selected = self.main_table.get_selected_rows()

        def core(progress):
            for _id in selected:
                # first, get the mod name and enabled status
                (mod_folder, enabled) = self.main_table.get_basic_info(_id)

                if enabled:
                    continue

                # setup enabler thread
                enabler = flight_sim.enable_mod_thread(self.sim_folder, mod_folder)
                enabler.activity_update.connect(progress.set_activity)

                def failed(error):
                    self.base_fail(error, {}, "Failed to enable mod")

                # start the thread
                with thread.thread_wait(
                    enabler.finished,
                    failed_signal=enabler.failed,
                    failed_func=failed,
                    update_signal=enabler.activity_update,
                ):
                    enabler.start()

        self.base_action(
            core, button=self.enable_button, empty_check=True, empty_val=selected
        )

    def disable(self):
        """Disables selected mods."""
        selected = self.main_table.get_selected_rows()

        def core(progress):
            for _id in selected:
                # first, get the mod name and disable status
                (mod_folder, enabled) = self.main_table.get_basic_info(_id)

                if not enabled:
                    continue

                # setup disabler thread
                disabler = flight_sim.disable_mod_thread(self.sim_folder, mod_folder)
                disabler.activity_update.connect(progress.set_activity)

                def failed(error):
                    self.base_fail(error, {}, "Failed to disable mod")

                # start the thread
                with thread.thread_wait(
                    disabler.finished,
                    failed_signal=disabler.failed,
                    failed_func=failed,
                    update_signal=disabler.activity_update,
                ):
                    disabler.start()

        self.base_action(
            core, button=self.disable_button, empty_check=True, empty_val=selected
        )

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

        succeeded = []

        def core(progress):
            # setup backuper thread
            backuper = flight_sim.create_backup_thread(self.sim_folder, archive)
            backuper.activity_update.connect(progress.set_activity)

            def finish(result):
                # this function is required as the results will be a list,
                # which is not a hashable type
                succeeded.extend(result)

            def failed(error):
                mapping = {
                    flight_sim.ExtractionError: lambda: error_dialogs.archive_create(
                        self, archive
                    )
                }

                self.base_fail(
                    error, mapping, "Failed to create backup",
                )

            # start the thread, with extra 20 min timeout
            with thread.thread_wait(
                backuper.finished,
                timeout=1200000,
                failed_signal=backuper.failed,
                failed_func=failed,
                update_signal=backuper.activity_update,
            ):
                backuper.start()

        self.base_action(
            core, empty_check=True, empty_val=archive,
        )

        if succeeded:
            # open resulting directory
            question = question_dialogs.backup_success(self, archive)

            if question:
                # this will always be opening a folder and therefore is safe
                os.startfile(os.path.dirname(archive))  # nosec

    def refresh(self, first=False):
        """Refreshes all mod data."""
        self.refresh_button.setEnabled(False)

        # build list of mods
        enabled_mods, enabled_errors = flight_sim.get_enabled_mods(self.sim_folder)
        disabled_mods, disabled_errors = flight_sim.get_disabled_mods(self.sim_folder)

        all_errors = enabled_errors + disabled_errors

        # set data
        self.main_table.set_data(enabled_mods + disabled_mods, first=first)
        self.main_table.set_colors(self.parent.theme_menu_action.isChecked())

        # display errors
        if all_errors:
            warning_dialogs.mod_parsing(self, all_errors)

        self.search()
        self.refresh_button.setEnabled(True)

    def search(self):
        """Filter rows to match search term."""
        # strip and lowercase
        term = self.search_field.text().strip().lower()
        self.main_table.search(term)

    def clear_search(self):
        """Clear the search field."""
        self.search_field.clear()
