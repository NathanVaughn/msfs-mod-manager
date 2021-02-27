import os
import webbrowser

import PySide2.QtGui as QtGui
import PySide2.QtWidgets as QtWidgets
from fbs_runtime.application_context.PySide2 import ApplicationContext

import lib.files as files
from lib.config import CONFIG_FILE, DEBUG_LOG
from lib.theme import get_theme, set_theme
from lib.version import get_version
from widgets.main_widget import main_widget


class main_window(QtWidgets.QMainWindow):
    def __init__(
        self, parent: QtWidgets.QWidget = None, appctxt: ApplicationContext = None
    ) -> None:
        """Main application window."""
        QtWidgets.QMainWindow.__init__(self)
        self.parent = parent  # type: ignore
        self.appctxt = appctxt

    def build(self) -> None:
        """Build window."""
        self.setWindowTitle("MSFS Mod Manager - {}".format(get_version(self.appctxt)))  # type: ignore
        self.setWindowIcon(
            QtGui.QIcon(self.appctxt.get_resource(os.path.join("icons", "icon.png")))
        )

        self.main_widget = main_widget(self, self.appctxt)
        self.main_widget.build()

        self.setCentralWidget(self.main_widget)

        main_menu = self.menuBar()
        file_menu = main_menu.addMenu("File")

        self.theme_menu_action = QtWidgets.QAction("FS Theme", self, checkable=True)  # type: ignore
        self.theme_menu_action.setChecked(get_theme())
        self.theme_menu_action.triggered.connect(self.set_theme)  # type: ignore
        file_menu.addAction(self.theme_menu_action)  # type: ignore

        file_menu.addSeparator()

        menu_action = QtWidgets.QAction("Install Mod(s) from Archive", self)
        menu_action.triggered.connect(self.main_widget.install_archive) # type: ignore
        file_menu.addAction(menu_action) # type: ignore

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

        menu_action = QtWidgets.QAction("Change Disabled Mod Folder", self)
        menu_action.triggered.connect(self.main_widget.select_mod_install)  # type: ignore
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
        menu_action.triggered.connect(lambda: os.startfile(DEBUG_LOG))  # type: ignore
        help_menu.addAction(menu_action)  # type: ignore

        menu_action = QtWidgets.QAction("Open Config File", self)
        menu_action.triggered.connect(lambda: os.startfile(CONFIG_FILE))  # type: ignore
        help_menu.addAction(menu_action)  # type: ignore

        help_menu.addSeparator()

        menu_action = QtWidgets.QAction("Open Community Folder", self)
        menu_action.triggered.connect(  # type: ignore
            lambda: os.startfile(self.main_widget.flight_sim.get_sim_mod_folder())
        )
        help_menu.addAction(menu_action)  # type: ignore

        menu_action = QtWidgets.QAction("Open Mod Install Folder", self)
        menu_action.triggered.connect(  # type: ignore
            lambda: os.startfile(files.get_mod_install_folder())
        )
        help_menu.addAction(menu_action)  # type: ignore

    def set_theme(self) -> None:
        """Apply theme to the window."""
        # apply theme
        set_theme(self.appctxt, self.theme_menu_action.isChecked())  # type: ignore
        # reformat table
        self.main_widget.main_table.set_colors(self.theme_menu_action.isChecked())
        self.main_widget.main_table.resize()
