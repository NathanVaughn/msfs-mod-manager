import PySide2.QtCore as QtCore
import PySide2.QtWidgets as QtWidgets
from fbs_runtime.application_context.PySide2 import ApplicationContext

from lib import versions
from lib.flightsim import flightsim


class VersionsInfoDialog(QtWidgets.QDialog):
    """
    Application versions dialog.
    """

    def __init__(self, parent: QtWidgets.QWidget, appctxt: ApplicationContext) -> None:
        QtWidgets.QDialog.__init__(self)
        self.parent = parent  # type: ignore
        self.appctxt = appctxt

        self.setWindowTitle("Versions")
        self.setWindowFlags(
            QtCore.Qt.WindowSystemMenuHint  # type: ignore
            | QtCore.Qt.WindowTitleHint  # type: ignore
            | QtCore.Qt.WindowCloseButtonHint
        )
        self.setWindowModality(QtCore.Qt.ApplicationModal)  # type: ignore

        layout = QtWidgets.QFormLayout()  # type: ignore

        self.app_version_field = QtWidgets.QLineEdit(self)
        self.app_version_field.setReadOnly(True)
        layout.addRow("Application Version:", self.app_version_field)  # type: ignore

        self.game_version_field = QtWidgets.QLineEdit(self)
        self.game_version_field.setReadOnly(True)
        layout.addRow("Game Version:", self.game_version_field)  # type: ignore

        self.setLayout(layout)

        # get data
        self.app_version_field.setText(versions.get_app_version(self.appctxt))
        self.game_version_field.setText(flightsim.get_game_version())

        self.show()
        self.setFixedSize(self.width(), self.height())
