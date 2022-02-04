from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

from ..lib import helpers


class AboutDialog(QtWidgets.QDialog):
    """
    Application about dialog.
    """

    def __init__(self, parent: QtWidgets.QWidget, qapp: QtWidgets.QApplication) -> None:
        super().__init__()

        self.parent_ = parent
        self.qapp = qapp

        self.setWindowTitle("About MSFS Mod Manager")
        self.setWindowIcon(QtGui.QIcon(str(helpers.resource_path(Path("icon.png")))))
        self.setWindowFlags(
            QtCore.Qt.WindowSystemMenuHint
            | QtCore.Qt.WindowTitleHint  # type: ignore
            | QtCore.Qt.WindowCloseButtonHint
        )
        self.setWindowModality(QtCore.Qt.ApplicationModal)

        layout = QtWidgets.QVBoxLayout()
        big_font = QtGui.QFont("Arial", 16)
        small_font = QtGui.QFont("Arial", 10)

        icon = QtWidgets.QLabel(parent=self)
        icon.setPixmap(
            QtGui.QPixmap.scaledToHeight(
                QtGui.QPixmap(str(helpers.resource_path(Path("icon.png")))), 512
            )
        )
        layout.addWidget(icon)

        name = QtWidgets.QLabel("Microsoft Flight Simulator Mod Manager", parent=self)
        name.setFont(big_font)
        name.setAlignment(QtCore.Qt.AlignCenter)  # type: ignore
        layout.addWidget(name)

        author = QtWidgets.QLabel(
            "Developed by <a href='https://lksg.me/u/nathan'><span style='color:LightSkyBlue;'>Nathan Vaughn</span></a>",
            parent=self,
        )
        author.setFont(big_font)
        author.setOpenExternalLinks(True)
        author.setAlignment(QtCore.Qt.AlignCenter)  # type: ignore
        layout.addWidget(author)

        license_ = QtWidgets.QLabel(
            "Copyright 2021 - Licensed under the GPLv3 License", self
        )
        license_.setFont(small_font)
        license_.setAlignment(QtCore.Qt.AlignCenter)  # type: ignore
        layout.addWidget(license_)

        no_redistrib = QtWidgets.QLabel(
            "Please do not redistribute without permission", self
        )
        no_redistrib.setFont(small_font)
        no_redistrib.setAlignment(QtCore.Qt.AlignCenter)  # type: ignore
        layout.addWidget(no_redistrib)

        self.setLayout(layout)

        self.show()
        self.setFixedSize(self.width(), self.height())