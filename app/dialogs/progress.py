from pathlib import Path
from typing import Any, Tuple, Union

import PySide6.QtCore as QtCore
import PySide6.QtGui as QtGui
import PySide6.QtWidgets as QtWidgets

from ..lib import helpers


class ProgressDialog(QtWidgets.QDialog):
    """
    Progress bar dialog.
    """

    def __init__(self, parent: QtWidgets.QWidget, qapp: QtWidgets.QApplication) -> None:
        super().__init__()
        self.parent_ = parent
        self.qapp = qapp

        # enum types
        self.INFINITE = 0
        self.PERCENT = 1

        self.mode = self.INFINITE

        self.setWindowTitle("Progress")
        self.setWindowIcon(QtGui.QIcon(str(helpers.resource_path(Path("icon.png")))))
        self.setWindowFlags(
            QtCore.Qt.WindowSystemMenuHint
            | QtCore.Qt.WindowTitleHint
            #    | QtCore.Qt.WindowCloseButtonHint
        )
        self.setWindowModality(QtCore.Qt.ApplicationModal)

        layout = QtWidgets.QVBoxLayout()

        self.activity = QtWidgets.QLabel(parent=self)
        self.activity.setWordWrap(True)
        layout.addWidget(self.activity)

        self.sub_activity = QtWidgets.QLabel(parent=self)
        self.sub_activity.setWordWrap(True)
        layout.addWidget(self.sub_activity)

        self.progbar = QtWidgets.QProgressBar(self)
        layout.addWidget(self.progbar)

        self.setLayout(layout)

        self.show()
        self.raise_()

        self.setFixedSize(550, 150)

    def set_mode(self, mode: Any) -> None:
        """
        Sets the mode of the progress bar.
        """

        if mode == self.INFINITE:
            # Set the progress bar to be infinite
            self.progbar.setMaximum(0)
            self.progbar.setMinimum(0)
            self.progbar.setValue(0)
            self.mode = self.INFINITE
        elif mode == self.PERCENT:
            # Set the progress bar to be percentage
            self.progbar.setMaximum(100)
            self.progbar.setMinimum(0)
            self.progbar.setValue(0)
            self.mode = self.PERCENT

    def set_activity(self, message: Union[Tuple[str, str], str]) -> None:
        """
        Update the displayed message.
        If the given message is a Tuple, the first value is the main activity
        and the second value is the sub activity.
        """
        # extract values from tuple
        if isinstance(message, tuple):
            activity_message = message[0]
            sub_activity_message = message[1]
        else:
            activity_message = message
            sub_activity_message = None

        # only display anything that was set
        if activity_message:
            self.activity.setText(f"<b>{activity_message}</b>")
        if sub_activity_message:
            self.sub_activity.setText(sub_activity_message)

        self.qapp.processEvents()

    def set_percent(
        self, percent: Union[Tuple[int, int], int], total: int = None
    ) -> None:
        """
        Update the progress percent.
        If the given percent is a Tuple, the first value is the current index
        and the second value is the total number of items.
        """
        # first, if not in percent mode, set us there
        if self.mode != self.PERCENT:
            self.set_mode(self.PERCENT)

        # extract values from tuple
        if isinstance(percent, tuple):
            percent_value = percent[0]
            total_value = percent[1]
        else:
            percent_value = percent
            total_value = None

        # set the percent value
        self.progbar.setValue(percent_value)

        # if the total value was provided, set that
        if total_value is not None:
            self.progbar.setMaximum(total_value)

        self.qapp.processEvents()
