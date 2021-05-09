import os
import webbrowser
from pathlib import Path

from fbs_runtime.application_context.PySide2 import ApplicationContext
from PySide2 import QtGui, QtWidgets

from lib import versions
from lib.config import config
from lib.flightsim import flightsim
from widgets.main_widget import MainWidget


class MainWindow(QtWidgets.QMainWindow):
    """
    Main application window.
    """

    def __init__(self, parent: QtWidgets.QWidget, appctxt: ApplicationContext) -> None:
        QtWidgets.QMainWindow.__init__(self)
        self.parent = parent  # type: ignore
        self.appctxt = appctxt

        self.setWindowTitle(
            f"MSFS Mod Manager - {versions.get_app_version(self.appctxt)}"
        )
        self.setWindowIcon(
            QtGui.QIcon(self.appctxt.get_resource(Path("icons", "icon.png")))
        )

        self.main_widget = MainWidget(parent=self, appctxt=self.appctxt)

        self.setCentralWidget(self.main_widget)

        main_menu = self.menuBar()
        file_menu = main_menu.addMenu("File")

        self.theme_menu_action = QtWidgets.QAction("FS Theme", self, checkable=True)  # type: ignore
        self.theme_menu_action.setChecked(config.use_theme)
        self.theme_menu_action.triggered.connect(self.set_theme)  # type: ignore
        file_menu.addAction(self.theme_menu_action)  # type: ignore

        file_menu.addSeparator()

        menu_action = QtWidgets.QAction("Install Mod(s) from Archive", self)
        menu_action.triggered.connect(self.main_widget.install_archive)  # type: ignore
        file_menu.addAction(menu_action)  # type: ignore

        menu_action = QtWidgets.QAction("Install Mod from Folder", self)
        menu_action.triggered.connect(self.main_widget.install_folder)  # type: ignore
        file_menu.addAction(menu_action)  # type: ignore

        menu_action = QtWidgets.QAction("Uninstall Mods", self)
        menu_action.triggered.connect(self.main_widget.uninstall)  # type: ignore
        file_menu.addAction(menu_action)  # type: ignore

        file_menu.addSeparator()

        menu_action = QtWidgets.QAction("Create Backup", self)
        menu_action.triggered.connect(self.main_widget.create_backup)  # type: ignore
        file_menu.addAction(menu_action)  # type: ignore

        file_menu.addSeparator()

        menu_action = QtWidgets.QAction("Exit", self)
        menu_action.triggered.connect(self.parent.quit)  # type: ignore
        file_menu.addAction(menu_action)  # type: ignore

        edit_menu = main_menu.addMenu("Edit")

        menu_action = QtWidgets.QAction("Enable Selected Mods", self)
        menu_action.triggered.connect(self.main_widget.enable)  # type: ignore
        edit_menu.addAction(menu_action)  # type: ignore

        menu_action = QtWidgets.QAction("Disable Selected Mods", self)
        menu_action.triggered.connect(self.main_widget.disable)  # type: ignore
        edit_menu.addAction(menu_action)  # type: ignore

        edit_menu.addSeparator()

        menu_action = QtWidgets.QAction("Change Mod Install Path", self)
        menu_action.triggered.connect(self.main_widget.select_mod_path)  # type: ignore
        edit_menu.addAction(menu_action)  # type: ignore

        info_menu = main_menu.addMenu("Info")

        menu_action = QtWidgets.QAction("Refresh Mods", self)
        menu_action.triggered.connect(self.main_widget.refresh)  # type: ignore
        info_menu.addAction(menu_action)  # type: ignore

        menu_action = QtWidgets.QAction("Mod Info", self)
        menu_action.triggered.connect(self.main_widget.info)  # type: ignore
        info_menu.addAction(menu_action)  # type: ignore

        help_menu = main_menu.addMenu("Help")

        menu_action = QtWidgets.QAction("About", self)
        menu_action.triggered.connect(self.main_widget.about)  # type: ignore
        help_menu.addAction(menu_action)  # type: ignore

        menu_action = QtWidgets.QAction("Versions", self)
        menu_action.triggered.connect(self.main_widget.versions)  # type: ignore
        help_menu.addAction(menu_action)  # type: ignore

        help_menu.addSeparator()

        menu_action = QtWidgets.QAction("Open Official Website", self)
        menu_action.triggered.connect(  # type: ignore
            lambda: webbrowser.open("https://github.com/NathanVaughn/msfs-mod-manager/")
        )
        help_menu.addAction(menu_action)  # type: ignore

        menu_action = QtWidgets.QAction("Open Issues/Suggestions", self)
        menu_action.triggered.connect(  # type: ignore
            lambda: webbrowser.open(
                "https://github.com/NathanVaughn/msfs-mod-manager/issues/"
            )
        )
        help_menu.addAction(menu_action)  # type: ignore

        help_menu.addSeparator()

        menu_action = QtWidgets.QAction("Open Debug Log", self)
        menu_action.triggered.connect(lambda: os.startfile(config.LOG_FILE))  # type: ignore
        help_menu.addAction(menu_action)  # type: ignore

        menu_action = QtWidgets.QAction("Open Config File", self)
        menu_action.triggered.connect(lambda: os.startfile(config.CONFIG_FILE))  # type: ignore
        help_menu.addAction(menu_action)  # type: ignore

        help_menu.addSeparator()

        menu_action = QtWidgets.QAction("Open Community Folder", self)
        menu_action.triggered.connect(  # type: ignore
            lambda: os.startfile(flightsim.community_packages_path)
        )
        help_menu.addAction(menu_action)  # type: ignore

        menu_action = QtWidgets.QAction("Open Mod Install Folder", self)
        menu_action.triggered.connect(  # type: ignore
            lambda: os.startfile(config.packages_path)
        )
        help_menu.addAction(menu_action)  # type: ignore

        self.set_theme()

    def set_theme(self) -> None:
        """
        Apply theme to the window.
        """
        # set config
        config.use_theme = self.theme_menu_action.isChecked()

        if config.use_theme:
            # apply theme
            stylesheet = self.appctxt.get_resource("fs_style.qss")
            self.appctxt.app.setStyleSheet(
                open(stylesheet, "r", encoding="utf8").read()
            )
        else:
            # remove theme
            self.appctxt.app.setStyleSheet("")

        # reformat table
        self.main_widget.main_table.set_colors(config.use_theme)
        self.main_widget.main_table.resize()
