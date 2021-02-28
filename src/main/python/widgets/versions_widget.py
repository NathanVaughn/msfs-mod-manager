import PySide2.QtCore as QtCore
import PySide2.QtWidgets as QtWidgets
from fbs_runtime.application_context.PySide2 import ApplicationContext

from lib.flight_sim import flight_sim
from lib.version import get_version


class versions_widget(QtWidgets.QDialog):
    def __init__(
        self,
        flight_sim_handle: flight_sim,
        parent: QtWidgets.QWidget = None,
        appctxt: ApplicationContext = None,
    ) -> None:
        """Game and application versions widget."""
        QtWidgets.QDialog.__init__(self)
        self.flight_sim = flight_sim_handle
        self.parent = parent  # type: ignore
        self.appctxt = appctxt

        self.setWindowTitle("Versions")
        self.setWindowFlags(
            QtCore.Qt.WindowSystemMenuHint  # type: ignore
            | QtCore.Qt.WindowTitleHint  # type: ignore
            | QtCore.Qt.WindowCloseButtonHint
        )
        self.setWindowModality(QtCore.Qt.ApplicationModal)  # type: ignore

        self.layout = QtWidgets.QFormLayout()  # type: ignore

        self.app_version_field = QtWidgets.QLineEdit(self)
        self.app_version_field.setReadOnly(True)
        self.layout.addRow("Application Version:", self.app_version_field)  # type: ignore

        self.game_version_field = QtWidgets.QLineEdit(self)
        self.game_version_field.setReadOnly(True)
        self.layout.addRow("Game Version:", self.game_version_field)  # type: ignore

        self.setLayout(self.layout)
        self.get_versions()

        self.show()
        self.setFixedSize(self.width(), self.height())

    def get_versions(self) -> None:
        self.app_version_field.setText(get_version(self.appctxt))  # type: ignore
        self.game_version_field.setText(self.flight_sim.get_game_version())
