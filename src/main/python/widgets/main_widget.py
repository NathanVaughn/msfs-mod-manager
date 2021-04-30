import PySide2.QtCore as QtCore
import PySide2.QtGui as QtGui
import PySide2.QtWidgets as QtWidgets
from fbs_runtime.application_context.PySide2 import ApplicationContext

from widgets.mod_table import ModTable

ARCHIVE_FILTER = "Archives (*.zip *.rar *.tar *.bz2 *.7z)"


class MainWidget(QtWidgets.QWidget):
    """
    Main application widget.
    """

    def __init__(
        self, parent: QtWidgets.QWidget = None, appctxt: ApplicationContext = None
    ) -> None:

        super().__init__(self)
        self.parent = parent  # type: ignore
        self.appctxt = appctxt

        self.layout = QtWidgets.QGridLayout(self)  # type: ignore

        self.install_button = QtWidgets.QPushButton("Install", self)
        self.layout.addWidget(self.install_button, 0, 0)  # type: ignore

        self.uninstall_button = QtWidgets.QPushButton("Uninstall", self)
        self.layout.addWidget(self.uninstall_button, 0, 1)  # type: ignore

        self.enable_button = QtWidgets.QPushButton("Enable", self)
        self.layout.addWidget(self.enable_button, 0, 4)  # type: ignore

        self.disable_button = QtWidgets.QPushButton("Disable", self)
        self.layout.addWidget(self.disable_button, 0, 5)  # type: ignore

        self.info_button = QtWidgets.QPushButton("Info", self)
        self.layout.addWidget(self.info_button, 0, 8)  # type: ignore

        self.refresh_button = QtWidgets.QPushButton("Refresh", self)
        self.layout.addWidget(self.refresh_button, 0, 9)  # type: ignore

        self.sublayout = QtWidgets.QHBoxLayout()  # type: ignore

        self.search_label = QtWidgets.QLabel("Search:", self)
        self.sublayout.addWidget(self.search_label)

        self.search_field = QtWidgets.QLineEdit(self)
        self.sublayout.addWidget(self.search_field)

        self.clear_button = QtWidgets.QPushButton("Clear", self)
        self.sublayout.addWidget(self.clear_button)

        self.layout.addLayout(self.sublayout, 1, 6, 1, 4)

        self.main_table = ModTable(self)
        self.layout.addWidget(self.main_table, 2, 0, 1, 10)  # type: ignore

        self.setLayout(self.layout)

        # buttons
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
        self.shortcut_delete = QtWidgets.QShortcut(
            QtGui.QKeySequence(QtCore.Qt.Key_Delete), self  # type: ignore
        )
        self.shortcut_delete.activated.connect(self.uninstall)  # type: ignore
