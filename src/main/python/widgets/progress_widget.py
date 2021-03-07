from typing import Any, Tuple, Union

import PySide2.QtCore as QtCore
import PySide2.QtWidgets as QtWidgets
from fbs_runtime.application_context.PySide2 import ApplicationContext


class progress_widget(QtWidgets.QDialog):
    def __init__(
        self, parent: QtWidgets.QWidget = None, appctxt: ApplicationContext = None
    ) -> None:
        """Progress bar dialog."""
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

        self.layout = QtWidgets.QVBoxLayout()  # type: ignore

        self.activity = QtWidgets.QLabel(parent=self)  # type: ignore
        self.activity.setWordWrap(True)
        self.layout.addWidget(self.activity)

        self.bar = QtWidgets.QProgressBar(self)
        self.layout.addWidget(self.bar)

        self.setLayout(self.layout)

        self.show()
        self.raise_()

        self.setFixedSize(500, 100)

    def set_mode(self, mode: Any) -> None:
        """Sets the mode of the progress bar."""

        if mode == self.INFINITE:
            # Set the progress bar to be infinite
            self.bar.setMaximum(0)
            self.bar.setMinimum(0)
            self.bar.setValue(0)
            self.mode = self.INFINITE
        elif mode == self.PERCENT:
            # Set the progress bar to be percentage
            self.bar.setMaximum(100)
            self.bar.setMinimum(0)
            self.bar.setValue(0)
            self.mode = self.PERCENT

    def set_activity(self, message: str) -> None:
        """Update the displayed message."""
        self.activity.setText(message)

    def set_percent(self, percent: Union[Tuple[int, int], int], total=None) -> None:
        """Update the progress percent."""
        if self.mode != self.PERCENT:
            self.set_mode(self.PERCENT)

        if total:
            self.bar.setMaximum(total)

        if isinstance(percent, tuple):
            self.bar.setMaximum(percent[1])
            self.bar.setValue(percent[0])
        else:
            self.bar.setValue(percent)
