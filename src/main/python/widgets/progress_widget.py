import PySide2.QtCore as QtCore
import PySide2.QtWidgets as QtWidgets


class progress_widget(QtWidgets.QDialog):
    def __init__(self, parent=None, appctxt=None):
        """Progress bar dialog."""
        QtWidgets.QDialog.__init__(self)
        self.parent = parent
        self.appctxt = appctxt

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
        self.setFixedSize(500, 100)

    def set_infinite(self):
        """Set the progress bar to be infinite."""
        self.bar.setMaximum(0)
        self.bar.setMinimum(0)
        self.bar.setValue(0)

    def set_percent(self):
        """Set the progress bar to be percentage."""
        self.bar.setMaximum(100)
        self.bar.setMinimum(0)
        self.bar.setValue(0)

    def set_activity(self, message):
        """Update the displayed message."""
        self.activity.setText(message)

    def set_percentage(self, percent):
        """Update the progress percent."""
        self.bar.setValue(percent)
