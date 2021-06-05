import os
import webbrowser
from pathlib import Path

from lib import helpers, versions
from lib.config import config
from lib.flightsim import flightsim
from PySide6 import QtGui, QtWidgets
from widgets.main_widget import MainWidget


class MainWindow(QtWidgets.QMainWindow):
    """
    Main application window.
    """

    def __init__(
        self, parent: QtWidgets.QApplication, qapp: QtWidgets.QApplication
    ) -> None:
        QtWidgets.QMainWindow.__init__(self)
        self.parent = parent  # type: ignore
        self.qapp = qapp

        self.setWindowTitle(f"MSFS Mod Manager - {versions.get_app_version()}")
        self.setWindowIcon(
            QtGui.QIcon(str(helpers.resource_path(Path("assets", "icon.png"))))
        )

        self.main_widget = MainWidget(parent=self, qapp=self.qapp)

        self.setCentralWidget(self.main_widget)

        main_menu = self.menuBar()
        file_menu = main_menu.addMenu("File")

        # overload type isn't available
        self.theme_menu_action = QtGui.QAction("FS Theme", parent=self, checkable=True)  # type: ignore
        self.theme_menu_action.setChecked(config.use_theme)
        self.theme_menu_action.triggered.connect(self.set_theme)  # type: ignore
        file_menu.addAction(self.theme_menu_action)

        file_menu.addSeparator()

        menu_action = QtGui.QAction("Install Mod(s) from Archive", parent=self)
        menu_action.triggered.connect(self.main_widget.install_archive)  # type: ignore
        file_menu.addAction(menu_action)

        menu_action = QtGui.QAction("Install Mod from Folder", parent=self)
        menu_action.triggered.connect(self.main_widget.install_folder)  # type: ignore
        file_menu.addAction(menu_action)

        menu_action = QtGui.QAction("Uninstall Mods", parent=self)
        menu_action.triggered.connect(self.main_widget.uninstall)  # type: ignore
        file_menu.addAction(menu_action)

        file_menu.addSeparator()

        menu_action = QtGui.QAction("Create Backup", parent=self)
        menu_action.triggered.connect(self.main_widget.create_backup)  # type: ignore
        file_menu.addAction(menu_action)

        file_menu.addSeparator()

        menu_action = QtGui.QAction("Exit", parent=self)
        menu_action.triggered.connect(self.parent.quit)  # type: ignore
        file_menu.addAction(menu_action)

        edit_menu = main_menu.addMenu("Edit")

        menu_action = QtGui.QAction("Enable Selected Mods", parent=self)
        menu_action.triggered.connect(self.main_widget.enable)  # type: ignore
        edit_menu.addAction(menu_action)

        menu_action = QtGui.QAction("Disable Selected Mods", parent=self)
        menu_action.triggered.connect(self.main_widget.disable)  # type: ignore
        edit_menu.addAction(menu_action)

        edit_menu.addSeparator()

        menu_action = QtGui.QAction("Change Mod Install Path", parent=self)
        menu_action.triggered.connect(self.main_widget.select_mod_path)  # type: ignore
        edit_menu.addAction(menu_action)

        info_menu = main_menu.addMenu("Info")

        menu_action = QtGui.QAction("Refresh Mods", parent=self)
        menu_action.triggered.connect(self.main_widget.refresh)  # type: ignore
        info_menu.addAction(menu_action)

        menu_action = QtGui.QAction("Mod Info", parent=self)
        menu_action.triggered.connect(self.main_widget.info)  # type: ignore
        info_menu.addAction(menu_action)

        help_menu = main_menu.addMenu("Help")

        menu_action = QtGui.QAction("About", parent=self)
        menu_action.triggered.connect(self.main_widget.about)  # type: ignore
        help_menu.addAction(menu_action)

        menu_action = QtGui.QAction("Versions", parent=self)
        menu_action.triggered.connect(self.main_widget.version_info)  # type: ignore
        help_menu.addAction(menu_action)

        help_menu.addSeparator()

        menu_action = QtGui.QAction("Open Official Website", parent=self)
        menu_action.triggered.connect(  # type: ignore
            lambda: webbrowser.open("https://github.com/NathanVaughn/msfs-mod-manager/")
        )
        help_menu.addAction(menu_action)  # type: ignore

        menu_action = QtGui.QAction("Open Issues/Suggestions", parent=self)
        menu_action.triggered.connect(  # type: ignore
            lambda: webbrowser.open(
                "https://github.com/NathanVaughn/msfs-mod-manager/issues/"
            )
        )
        help_menu.addAction(menu_action)

        help_menu.addSeparator()

        menu_action = QtGui.QAction("Open Debug Log", parent=self)
        menu_action.triggered.connect(lambda: os.startfile(config.LOG_FILE))  # type: ignore
        help_menu.addAction(menu_action)

        menu_action = QtGui.QAction("Open Config File", parent=self)
        menu_action.triggered.connect(lambda: os.startfile(config.CONFIG_FILE))  # type: ignore
        help_menu.addAction(menu_action)

        help_menu.addSeparator()

        menu_action = QtGui.QAction("Open Community Folder", parent=self)
        menu_action.triggered.connect(  # type: ignore
            lambda: os.startfile(flightsim.community_packages_path)
        )
        help_menu.addAction(menu_action)

        menu_action = QtGui.QAction("Open Mod Install Folder", parent=self)
        menu_action.triggered.connect(  # type: ignore
            lambda: os.startfile(config.mods_path)
        )
        help_menu.addAction(menu_action)

        self.set_theme()

    def set_theme(self) -> None:
        """
        Apply theme to the window.
        """
        # set config
        config.use_theme = self.theme_menu_action.isChecked()

        if config.use_theme:
            # apply theme
            stylesheet = helpers.resource_path(Path("assets", "fs_style.qss"))
            self.qapp.setStyleSheet(open(stylesheet, "r", encoding="utf8").read())
        else:
            # remove theme
            self.qapp.setStyleSheet("")

        # reformat table
        self.main_widget.main_table.set_colors(config.use_theme)
        self.main_widget.main_table.resize()
