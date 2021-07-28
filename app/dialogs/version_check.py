from typing import Tuple

import PySide6.QtWidgets as QtWidgets


class VersionCheckDialog:
    """
    Application version check dialog.
    """

    def __init__(self, parent: QtWidgets.QWidget, installed: bool = False) -> None:
        self.parent_ = parent

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

    def exec(self) -> Tuple[bool, bool]:
        """
        Executes the widget.
        Returns selected button and if the remember option was selected.
        """
        return (
            self.msgbox.exec() == QtWidgets.QMessageBox.Yes,
            bool(self.chkbox.checkState()),
        )
