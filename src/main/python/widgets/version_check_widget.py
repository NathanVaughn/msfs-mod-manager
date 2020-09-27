import PySide2.QtWidgets as QtWidgets


class version_check_widget:
    def __init__(self, parent=None, installed=False):
        """Version check widget."""
        self.parent = parent

        self.chkbox = QtWidgets.QCheckBox("Don't ask me again")

        self.msgbox = QtWidgets.QMessageBox(parent)
        self.msgbox.setIcon(QtWidgets.QMessageBox.Information)
        if installed:
            self.msgbox.setText(
                "A new version is available. "
                + "Would you like to automatically install it?"
            )
        else:
            self.msgbox.setText(
                "A new version is available. "
                + "Would you like to go to GitHub to download it?"
            )
        self.msgbox.setCheckBox(self.chkbox)

        self.msgbox.addButton(QtWidgets.QMessageBox.Yes)
        self.msgbox.addButton(QtWidgets.QMessageBox.No)
        self.msgbox.setDefaultButton(QtWidgets.QMessageBox.Yes)

    def exec_(self):
        """Executes the widget.
        Returns selected button and if the remember option was selected."""
        return (self.msgbox.exec_(), bool(self.chkbox.checkState()))
