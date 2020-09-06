import os

import PySide2.QtGui as QtGui
import PySide2.QtWidgets as QtWidgets

from widgets.main_widget import main_widget
from lib.version import get_version
from lib.theme import set_theme, get_theme


class main_window(QtWidgets.QMainWindow):
    def __init__(self, parent=None, appctxt=None):
        QtWidgets.QMainWindow.__init__(self)
        self.parent = parent
        self.appctxt = appctxt

    def build(self):
        """Build widget"""
        self.setWindowTitle("MSFS Mod Manager - {}".format(get_version(self.appctxt)))
        self.setWindowIcon(
            QtGui.QIcon(self.appctxt.get_resource(os.path.join("icons", "icon.png")))
        )

        self.main_widget = main_widget(self, self.appctxt)
        self.main_widget.build()

        self.setCentralWidget(self.main_widget)

        main_menu = self.menuBar()
        file_menu = main_menu.addMenu("File")

        self.theme_menu_action = QtWidgets.QAction("FS Theme", self, checkable=True)
        self.theme_menu_action.setChecked(get_theme())
        self.theme_menu_action.triggered.connect(self.set_theme)
        file_menu.addAction(self.theme_menu_action)

        file_menu.addSeparator()

        menu_action = QtWidgets.QAction("Create Backup", self)
        menu_action.triggered.connect(self.main_widget.create_backup)
        file_menu.addAction(menu_action)

        file_menu.addSeparator()

        menu_action = QtWidgets.QAction("Exit", self)
        menu_action.triggered.connect(self.parent.quit)
        file_menu.addAction(menu_action)

        edit_menu = main_menu.addMenu("Edit")

        menu_action = QtWidgets.QAction("Install Mods", self)
        menu_action.triggered.connect(self.main_widget.install)
        edit_menu.addAction(menu_action)

        menu_action = QtWidgets.QAction("Uninstall Mods", self)
        menu_action.triggered.connect(self.main_widget.uninstall)
        edit_menu.addAction(menu_action)

        edit_menu.addSeparator()

        menu_action = QtWidgets.QAction("Enable Selected Mods", self)
        menu_action.triggered.connect(self.main_widget.enable)
        edit_menu.addAction(menu_action)

        menu_action = QtWidgets.QAction("Disable Selected Mods", self)
        menu_action.triggered.connect(self.main_widget.disable)
        edit_menu.addAction(menu_action)

        edit_menu.addSeparator()

        menu_action = QtWidgets.QAction("Refresh Mods", self)
        menu_action.triggered.connect(self.main_widget.refresh)
        edit_menu.addAction(menu_action)

        menu_action = QtWidgets.QAction("Mod Info", self)
        menu_action.triggered.connect(self.main_widget.info)
        edit_menu.addAction(menu_action)

        info_menu = main_menu.addMenu("Info")

        menu_action = QtWidgets.QAction("About", self)
        menu_action.triggered.connect(self.main_widget.about)
        info_menu.addAction(menu_action)

    def set_theme(self):
        # apply theme
        set_theme(self.appctxt, self.theme_menu_action.isChecked())
        # reformat table
        self.main_widget.main_table.set_colors(self.theme_menu_action.isChecked())
        self.main_widget.main_table.resize()
