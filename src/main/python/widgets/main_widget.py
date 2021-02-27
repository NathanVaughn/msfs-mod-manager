import datetime
import os
import sys
import webbrowser
from typing import Any, Callable

import PySide2.QtCore as QtCore
import PySide2.QtGui as QtGui
import PySide2.QtWidgets as QtWidgets
from fbs_runtime.application_context.PySide2 import ApplicationContext
from loguru import logger

import dialogs.error_dialogs as error_dialogs
import dialogs.information_dialogs as information_dialogs
import dialogs.question_dialogs as question_dialogs
import dialogs.warning_dialogs as warning_dialogs
import lib.config as config
import lib.files as files
import lib.flight_sim as flight_sim
import lib.thread as thread
import lib.version as version
from dialogs.version_check_dialog import version_check_dialog
from widgets.about_widget import about_widget
from widgets.info_widget import info_widget
from widgets.main_table import main_table
from widgets.progress_widget import progress_widget
from widgets.versions_widget import versions_widget

ARCHIVE_FILTER = "Archives (*.zip *.rar *.tar *.bz2 *.7z)"


class main_widget(QtWidgets.QWidget):
    def __init__(
        self, parent: QtWidgets.QWidget = None, appctxt: ApplicationContext = None
    ) -> None:
        """Main application widget."""
        QtWidgets.QWidget.__init__(self)
        self.parent = parent # type: ignore
        self.appctxt = appctxt

    def build(self) -> None:
        """Build layout."""
        self.layout = QtWidgets.QGridLayout() # type: ignore

        self.install_button = QtWidgets.QPushButton("Install", self)
        self.layout.addWidget(self.install_button, 0, 0) # type: ignore

        self.uninstall_button = QtWidgets.QPushButton("Uninstall", self)
        self.layout.addWidget(self.uninstall_button, 0, 1) # type: ignore

        self.enable_button = QtWidgets.QPushButton("Enable", self)
        self.layout.addWidget(self.enable_button, 0, 4) # type: ignore

        self.disable_button = QtWidgets.QPushButton("Disable", self)
        self.layout.addWidget(self.disable_button, 0, 5) # type: ignore

        self.info_button = QtWidgets.QPushButton("Info", self)
        self.layout.addWidget(self.info_button, 0, 8) # type: ignore

        self.refresh_button = QtWidgets.QPushButton("Refresh", self)
        self.layout.addWidget(self.refresh_button, 0, 9) # type: ignore

        self.sublayout = QtWidgets.QHBoxLayout() # type: ignore

        self.search_label = QtWidgets.QLabel("Search:", self)
        self.sublayout.addWidget(self.search_label)

        self.search_field = QtWidgets.QLineEdit(self)
        self.sublayout.addWidget(self.search_field)

        self.clear_button = QtWidgets.QPushButton("Clear", self)
        self.sublayout.addWidget(self.clear_button)

        self.layout.addLayout(self.sublayout, 1, 6, 1, 4)

        self.main_table = main_table(self)
        self.layout.addWidget(self.main_table, 2, 0, 1, 10) # type: ignore

        self.setLayout(self.layout)

        # buttons
        self.install_button.clicked.connect(self.install_archive) # type: ignore
        self.uninstall_button.clicked.connect(self.uninstall) # type: ignore
        self.enable_button.clicked.connect(self.enable) # type: ignore
        self.disable_button.clicked.connect(self.disable) # type: ignore
        self.refresh_button.clicked.connect(self.refresh) # type: ignore
        self.info_button.clicked.connect(self.info) # type: ignore
        self.main_table.doubleClicked.connect(self.info) # type: ignore

        self.clear_button.clicked.connect(self.clear_search) # type: ignore
        self.search_field.textChanged.connect(self.search) # type: ignore

        # shortcuts
        self.shortcut_delete = QtWidgets.QShortcut(
            QtGui.QKeySequence(QtCore.Qt.Key_Delete), self # type: ignore
        )
        self.shortcut_delete.activated.connect(self.uninstall) # type: ignore

        # handle to data
        self.flight_sim = flight_sim.flight_sim()

    # ======================
    # Sim Functions
    # ======================

    def find_sim(self) -> None:
        """Sets the path to the simulator root folder."""

        def user_selection() -> None:
            """Function to keep user in a loop until they select correct folder."""
            # prompt user to select
            self.flight_sim.sim_packages_folder = (
                QtWidgets.QFileDialog.getExistingDirectory(
                    parent=self,
                    caption="Select the root Microsoft Flight Simulator directory",
                    dir=os.getenv("APPDATA"), # type: ignore
                )
            )

            if not self.flight_sim.sim_packages_folder.strip():
                sys.exit()

            elif self.flight_sim.is_sim_packages_folder(
                self.flight_sim.sim_packages_folder
            ):
                # save the config file
                config.set_key_value(
                    config.SIM_FOLDER_KEY,
                    self.flight_sim.sim_packages_folder,
                    path=True,
                )

            elif self.flight_sim.is_sim_packages_folder(
                os.path.join(self.flight_sim.sim_packages_folder, "Packages")
            ):
                # save the config file
                config.set_key_value(
                    config.SIM_FOLDER_KEY,
                    os.path.join(self.flight_sim.sim_packages_folder, "Packages"),
                    path=True,
                )

            else:
                # show error
                warning_dialogs.sim_path_invalid(self)
                # send them through again
                user_selection()

        # try to automatically find the sim
        (
            success,
            self.flight_sim.sim_packages_folder, # type: ignore
        ) = self.flight_sim.find_sim_packages_folder()

        if not self.flight_sim.sim_packages_folder:
            # show error
            warning_dialogs.sim_not_detected(self)
            # let user select folder
            user_selection()

        elif not success:
            # save the config file
            config.set_key_value(
                config.SIM_FOLDER_KEY, self.flight_sim.sim_packages_folder, path=True
            )
            # notify user
            information_dialogs.sim_detected(self, self.flight_sim.sim_packages_folder)

    def select_mod_install(self) -> None:
        """Allow user to select new mod install folder."""
        old_install = files.get_mod_install_folder()

        new_install = QtWidgets.QFileDialog.getExistingDirectory(
            parent=self,
            caption="Select mod install folder",
            dir=os.path.dirname(old_install),
        )

        def core(progress: Callable) -> None:
            # setup mover thread
            mover = files.move_folder_thread(old_install, new_install)
            mover.activity_update.connect(progress.set_activity) # type: ignore

            def failed(err: Exception) -> None:
                typ = type(err)
                message = str(err)

                logger.exception("Failed to move folder")
                error_dialogs.general(self, typ, message)

            # start the thread
            with thread.thread_wait(
                mover.finished,
                failed_signal=mover.failed,
                failed_func=failed,
                update_signal=mover.activity_update,
            ):
                mover.start()

            config.set_key_value(config.MOD_INSTALL_FOLDER_KEY, new_install, path=True)
            information_dialogs.disabled_mods_folder(self, new_install)

        if new_install and not files.check_same_path(old_install, new_install):
            self.base_action(core)

    # ======================
    # Inherited Functions
    # ======================

    def base_fail(self, error: Exception, mapping: dict, fallback_text: str) -> None:
        """Base thread failure function."""
        typ = type(error)
        message = str(error)

        if typ not in mapping:
            logger.error(fallback_text)
            logger.error("{}: {}", typ, message)
            error_dialogs.general(self, typ, message)
        else:
            func = mapping[typ]
            func()

    def base_action(
        self,
        core_func: Callable,
        button: QtWidgets.QPushButton = None,
        sanity_dialog: Callable = None,
        empty_check: bool = False,
        empty_val: Any = None,
        refresh: bool = True,
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
        progress.set_mode(progress.INFINITE)

        # execute the core function
        core_func(progress)
        progress.close()

        # refresh the data
        if refresh:
            self.refresh(automated=True)

        # cleanup
        if button:
            button.setEnabled(True)

    # ======================
    # Version Check
    # ======================

    def check_version(self) -> None:
        """Checks the application version and allows user to open browser to update."""
        installed = version.is_installed()
        return_url = version.check_version(self.appctxt, installed) # type: ignore

        def core(progress: Callable) -> None:
            progress.set_mode(progress.PERCENT)
            progress.set_activity("Downloading latest version ({})".format(return_url))

            # setup downloader thread
            downloader = version.download_new_version_thread(return_url) # type: ignore
            downloader.percent_update.connect(progress.set_percent) # type: ignore

            def failed(err: Exception) -> None:
                typ = type(err)
                message = str(err)

                logger.exception("Failed to download new version")
                error_dialogs.general(self, typ, message)

            # start the thread
            with thread.thread_wait(
                downloader.finished,
                finish_func=version.install_new_version,
                failed_signal=downloader.failed,
                failed_func=failed,
                update_signal=downloader.percent_update,
            ):
                downloader.start()

        if not return_url:
            return

        result, remember = version_check_dialog(self, installed).exec_()
        if result:
            if installed:
                self.base_action(core, refresh=False)
            else:
                webbrowser.open(return_url) # type: ignore
        elif remember:
            config.set_key_value(config.NEVER_VER_CHEK_KEY, True)

    # ======================
    # Data Operations
    # ======================

    def install_archive(self) -> None:
        """Installs selected mod archives."""

        # first, let user select multiple archives
        mod_archives = QtWidgets.QFileDialog.getOpenFileNames(
            parent=self,
            caption="Select mod archive(s)",
            dir=files.get_last_open_folder(),
            filter=ARCHIVE_FILTER,
        )[0]

        succeeded = []

        def core(progress: Callable) -> None:
            # for each archive, try to install it
            for mod_archive in mod_archives:

                def finish(result: list) -> None:
                    # this function is required as the results will be a list,
                    # which is not a hashable type
                    succeeded.extend(result)

                def failed(err: Exception) -> None:
                    message = str(err)

                    mapping = {
                        files.ExtractionError: lambda: error_dialogs.archive_extract(
                            self, mod_archive, message
                        ),
                        flight_sim.NoManifestError: lambda: warning_dialogs.mod_parsing(
                            self, [mod_archive]
                        ),
                        files.AccessError: lambda: error_dialogs.permission(
                            self, mod_archive, message
                        ),
                        flight_sim.NoModsError: lambda: error_dialogs.no_mods(
                            self, mod_archive
                        ),
                    }

                    self.base_fail(
                        err,
                        mapping,
                        "Failed to install mod archive",
                    )

                # setup installer thread
                installer = flight_sim.install_mod_archive_thread(
                    self.flight_sim, mod_archive
                )
                installer.activity_update.connect(progress.set_activity) # type: ignore
                installer.percent_update.connect(progress.set_percent) # type: ignore

                # start the thread
                with thread.thread_wait(
                    installer.finished,
                    finish_func=finish,
                    failed_signal=installer.failed,
                    failed_func=failed,
                    update_signal=installer.activity_update,
                    timeout=1200000,
                ):
                    installer.start()

        self.base_action(
            core,
            button=self.install_button,
            empty_check=True,
            empty_val=mod_archives,
        )

        if succeeded:
            config.set_key_value(
                config.LAST_OPEN_FOLDER_KEY, os.path.dirname(mod_archives[0]), path=True
            )
            information_dialogs.mods_installed(self, succeeded)

    def install_folder(self) -> None:
        """Installs selected mod folders."""

        # first, let user select a folder
        mod_folder = QtWidgets.QFileDialog.getExistingDirectory(
            parent=self,
            caption="Select mod folder",
            dir=files.get_last_open_folder(),
        )

        succeeded = []

        def core(progress: Callable) -> None:
            def finish(result: list) -> None:
                # this function is required as the results will be a list,
                # which is not a hashable type
                succeeded.extend(result)

            def failed(err: Exception) -> None:
                message = str(err)

                mapping = {
                    flight_sim.NoManifestError: lambda: warning_dialogs.mod_parsing(
                        self, [mod_folder]
                    ),
                    files.AccessError: lambda: error_dialogs.permission(
                        self, mod_folder, message
                    ),
                    flight_sim.NoModsError: lambda: error_dialogs.no_mods(
                        self, mod_folder
                    ),
                }

                self.base_fail(
                    err,
                    mapping,
                    "Failed to install mod folder",
                )

            # setup installer thread
            installer = flight_sim.install_mods_thread(self.flight_sim, mod_folder)
            installer.activity_update.connect(progress.set_activity) # type: ignore

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
            core,
            button=self.install_button,
            empty_check=True,
            empty_val=mod_folder,
        )

        if succeeded:
            config.set_key_value(
                config.LAST_OPEN_FOLDER_KEY, os.path.dirname(mod_folder), path=True
            )
            information_dialogs.mods_installed(self, succeeded)

    def uninstall(self) -> None:
        """Uninstalls selected mods."""
        selected = self.main_table.get_selected_rows()

        def core(progress: Callable) -> None:
            for i, _id in enumerate(selected):
                # first, get the mod name and enabled status
                (folder, enabled) = self.main_table.get_basic_info(_id)
                mod_folder = self.flight_sim.get_mod_folder(folder, enabled)

                # setup uninstaller thread
                uninstaller = flight_sim.uninstall_mod_thread(
                    self.flight_sim, mod_folder
                )
                uninstaller.activity_update.connect(progress.set_activity) # type: ignore

                def failed(err: Exception) -> None:
                    self.base_fail(err, {}, "Failed to uninstall mod")

                # start the thread
                with thread.thread_wait(
                    uninstaller.finished,
                    failed_signal=uninstaller.failed,
                    failed_func=failed,
                    update_signal=uninstaller.activity_update,
                ):
                    uninstaller.start()

                progress.set_percent(i, total=len(selected) - 1)

        self.base_action(
            core,
            button=self.uninstall_button,
            sanity_dialog=lambda: question_dialogs.mod_delete(self, len(selected)),
            empty_check=True,
            empty_val=selected,
        )

    def enable(self) -> None:
        """Enables selected mods."""
        selected = self.main_table.get_selected_rows()

        def core(progress: Callable) -> None:
            for i, _id in enumerate(selected):
                # first, get the mod name and enabled status
                (folder, enabled) = self.main_table.get_basic_info(_id)

                if enabled:
                    continue

                # setup enabler thread
                enabler = flight_sim.enable_mod_thread(self.flight_sim, folder)
                enabler.activity_update.connect(progress.set_activity) # type: ignore

                def failed(err: Exception) -> None:
                    self.base_fail(err, {}, "Failed to enable mod")

                # start the thread
                with thread.thread_wait(
                    enabler.finished,
                    failed_signal=enabler.failed,
                    failed_func=failed,
                    update_signal=enabler.activity_update,
                ):
                    enabler.start()

                progress.set_percent(i, total=len(selected) - 1)

        self.base_action(
            core, button=self.enable_button, empty_check=True, empty_val=selected
        )

    def disable(self) -> None:
        """Disables selected mods."""
        selected = self.main_table.get_selected_rows()

        def core(progress: Callable) -> None:
            for i, _id in enumerate(selected):
                # first, get the mod name and disable status
                (folder, enabled) = self.main_table.get_basic_info(_id)

                if not enabled:
                    continue

                # setup disabler thread
                disabler = flight_sim.disable_mod_thread(self.flight_sim, folder)
                disabler.activity_update.connect(progress.set_activity) # type: ignore

                def failed(err: Exception) -> None:
                    self.base_fail(err, {}, "Failed to disable mod")

                # start the thread
                with thread.thread_wait(
                    disabler.finished,
                    failed_signal=disabler.failed,
                    failed_func=failed,
                    update_signal=disabler.activity_update,
                ):
                    disabler.start()

                progress.set_percent(i, total=len(selected) - 1)

        self.base_action(
            core, button=self.disable_button, empty_check=True, empty_val=selected
        )

    def create_backup(self) -> None:
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

        def core(progress: Callable) -> None:
            # setup backuper thread
            backuper = flight_sim.create_backup_thread(self.flight_sim, archive)
            backuper.activity_update.connect(progress.set_activity) # type: ignore

            def finish(result: list) -> None:
                # this function is required as the results will be a list,
                # which is not a hashable type
                succeeded.extend(result)

            def failed(err: Exception) -> None:
                message = str(err)

                mapping = {
                    files.ExtractionError: lambda: error_dialogs.archive_create(
                        self, archive, message
                    )
                }

                self.base_fail(
                    err,
                    mapping,
                    "Failed to create backup",
                )

            # start the thread, with no timeout
            with thread.thread_wait(
                backuper.finished,
                timeout=None,
                finish_func=finish,
                failed_signal=backuper.failed,
                failed_func=failed,
                update_signal=backuper.activity_update,
            ):
                backuper.start()

        self.base_action(
            core,
            empty_check=True,
            empty_val=archive,
        )

        if succeeded:
            # open resulting directory
            question = question_dialogs.backup_success(self, archive)

            if question:
                # this will always be opening a folder and therefore is safe
                os.startfile(os.path.dirname(archive))  # nosec

    def refresh(self, first: bool = False, automated: bool = False) -> None:
        """Refreshes all mod data."""

        """This is not a separate thread, as the time it takes to parse each manifest
        is so low, that the GUI will easily stay responsive, even running in
        the foreground thread. I believe Windows gives applications around
        4 seconds to respond to incoming events before being marked as unresponsive,
        which should never happen in the process of parsing manifest.json files"""

        def core(progress: Callable) -> None:
            # temporarily clear search so that header resizing doesn't get borked
            self.search(override="")

            progress.set_mode(progress.PERCENT)

            def update(message: str, percent: int, total: int) -> None:
                progress.set_activity(message)
                progress.set_percent(percent, total)
                # make sure the progress bar gets updated.
                self.appctxt.app.processEvents()

            # clear mod cache if a human clicked the button
            if not automated:
                self.flight_sim.clear_mod_cache()

            # build list of mods
            all_mods_data, all_mods_errors = self.flight_sim.get_all_mods(
                progress_func=update
            )

            # set data
            self.main_table.set_data(all_mods_data, first=first)
            self.main_table.set_colors(self.parent.theme_menu_action.isChecked())

            # display errors
            if all_mods_errors:
                warning_dialogs.mod_parsing(self, all_mods_errors)

            # put the search back to how it was
            self.search()

        self.base_action(
            core,
            button=self.refresh_button,
            refresh=False,
        )

    # ======================
    # Child Widgets
    # ======================

    def info(self) -> None:
        """Open dialog to view mod info."""
        # self.info_button.setEnabled(False)

        selected = self.main_table.get_selected_rows()

        if not selected:
            return

        (folder, enabled) = self.main_table.get_basic_info(selected[0])
        mod_folder = self.flight_sim.get_mod_folder(folder, enabled)

        wid = info_widget(self.flight_sim, self, self.appctxt)
        wid.set_data(
            self.flight_sim.parse_mod_manifest(mod_folder),
            self.flight_sim.parse_mod_files(mod_folder),
        )
        wid.show()

        # self.info_button.setEnabled(True)

    def about(self) -> None:
        """Launch the about widget."""
        about_widget(self, self.appctxt).exec_()

    def versions(self) -> None:
        """Launch the versions widget."""
        versions_widget(self.flight_sim, self, self.appctxt).exec_()

    # ======================
    # Search
    # ======================

    def search(self, override: str = None) -> None:
        """Filter rows to match search term."""
        # strip
        term = self.search_field.text().strip()
        # override
        if override is not None:
            term = override

        # search
        self.main_table.search(term)

    def clear_search(self) -> None:
        """Clear the search field."""
        self.search_field.clear()
