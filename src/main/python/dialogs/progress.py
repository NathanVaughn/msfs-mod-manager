from typing import Any, Tuple, Union

import PySide2.QtCore as QtCore
import PySide2.QtWidgets as QtWidgets
from fbs_runtime.application_context.PySide2 import ApplicationContext


class ProgressDialog(QtWidgets.QDialog):
    """
    Progress bar dialog.
    """

    def __init__(self, parent: QtWidgets.QWidget, appctxt: ApplicationContext) -> None:

        QtWidgets.QDialog.__init__(self)
        self.parent = parent  # type: ignore
        self.appctxt = appctxt

        # enum types
        self.INFINITE = 0
        self.PERCENT = 1

        self.mode = self.INFINITE

        self.setWindowTitle("Progress")
        self.setWindowFlags(
            QtCore.Qt.WindowSystemMenuHint  # type: ignore
            | QtCore.Qt.WindowTitleHint  # type: ignore
            #    | QtCore.Qt.WindowCloseButtonHint
        )
        self.setWindowModality(QtCore.Qt.ApplicationModal)  # type: ignore

        layout = QtWidgets.QVBoxLayout()  # type: ignore

        self.activity = QtWidgets.QLabel(parent=self)  # type: ignore
        self.activity.setWordWrap(True)
        layout.addWidget(self.activity)

        self.progbar = QtWidgets.QProgressBar(self)
        layout.addWidget(self.progbar)

        self.setLayout(layout)

        self.show()
        self.raise_()

        self.setFixedSize(500, 100)

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

    def set_activity(self, message: str) -> None:
        """
        Update the displayed message.
        """
        self.activity.setText(message)

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
            total = percent[1]
            percent = percent[0]

        # set the percent value
        self.progbar.setValue(percent)

        # if the total value was provided, set that
        if total is not None:
            self.progbar.setMaximum(total)
