from pathlib import Path

import PySide6.QtCore as QtCore
import PySide6.QtGui as QtGui
import PySide6.QtWidgets as QtWidgets

from ..lib import helpers, versions
from ..lib.flightsim import flightsim


class VersionsInfoDialog(QtWidgets.QDialog):
    """
    Application versions dialog.
    """

    def __init__(self, parent: QtWidgets.QWidget, qapp: QtWidgets.QApplication) -> None:
        super().__init__()
        self.parent_ = parent
        self.qapp = qapp

        self.setWindowTitle("Versions")
        self.setWindowIcon(QtGui.QIcon(str(helpers.resource_path(Path("icon.png")))))
        self.setWindowFlags(
            QtCore.Qt.WindowSystemMenuHint
            | QtCore.Qt.WindowTitleHint
            | QtCore.Qt.WindowCloseButtonHint
        )
        self.setWindowModality(QtCore.Qt.ApplicationModal)

        layout = QtWidgets.QFormLayout()

        self.app_version_field = QtWidgets.QLineEdit(self)
        self.app_version_field.setReadOnly(True)
        layout.addRow("Application Version:", self.app_version_field)

        self.game_version_field = QtWidgets.QLineEdit(self)
        self.game_version_field.setReadOnly(True)
        layout.addRow("Game Version:", self.game_version_field)

        self.setLayout(layout)

        # get data
        self.app_version_field.setText(versions.get_app_version())
        self.game_version_field.setText(flightsim.get_game_version())

        self.show()
        self.setFixedSize(self.width(), self.height())
