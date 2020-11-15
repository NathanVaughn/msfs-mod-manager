import PySide2.QtCore as QtCore
import PySide2.QtWidgets as QtWidgets


class progress_widget(QtWidgets.QDialog):
    def __init__(self, parent=None, appctxt=None):
        """Progress bar dialog."""
        QtWidgets.QDialog.__init__(self)
        self.parent = parent
        self.appctxt = appctxt

        # enum types
        self.INFINITE = 0
        self.PERCENT = 1

        self.mode = self.INFINITE

        self.setWindowTitle("Progress")
        self.setWindowFlags(
            QtCore.Qt.WindowSystemMenuHint
            | QtCore.Qt.WindowTitleHint
            #    | QtCore.Qt.WindowCloseButtonHint
        )
        self.setWindowModality(QtCore.Qt.ApplicationModal)

        self.layout = QtWidgets.QVBoxLayout()

        self.activity = QtWidgets.QLabel(parent=self)
        self.activity.setWordWrap(True)
        self.layout.addWidget(self.activity)

        self.bar = QtWidgets.QProgressBar(self)
        self.layout.addWidget(self.bar)

        self.setLayout(self.layout)

        self.show()
        self.raise_()

        self.setFixedSize(500, 100)

    def set_mode(self, mode):
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

    def set_activity(self, message):
        """Update the displayed message."""
        self.activity.setText(message)

    def set_percent(self, percent, total=None):
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
