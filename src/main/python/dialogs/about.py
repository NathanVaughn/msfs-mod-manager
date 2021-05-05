from pathlib import Path

from fbs_runtime.application_context.PySide2 import ApplicationContext
from PySide2 import QtCore, QtGui, QtWidgets


class AboutDialog(QtWidgets.QDialog):
    """
    Application about widget.
    """

    def __init__(self, parent: QtWidgets.QWidget, appctxt: ApplicationContext) -> None:
        QtWidgets.QDialog.__init__(self)
        self.parent = parent  # type: ignore
        self.appctxt = appctxt

        self.setWindowTitle("About MSFS Mod Manager")
        self.setWindowFlags(
            QtCore.Qt.WindowSystemMenuHint  # type: ignore
            | QtCore.Qt.WindowTitleHint  # type: ignore
            | QtCore.Qt.WindowCloseButtonHint
        )
        self.setWindowModality(QtCore.Qt.ApplicationModal)  # type: ignore

        layout = QtWidgets.QVBoxLayout()  # type: ignore
        big_font = QtGui.QFont("Arial", 16)  # type: ignore
        small_font = QtGui.QFont("Arial", 10)  # type: ignore

        icon = QtWidgets.QLabel(parent=self)  # type: ignore
        icon.setPixmap(
            QtGui.QPixmap(self.appctxt.get_resource(Path("icons", "icon.png")))
        )
        layout.addWidget(icon)

        name = QtWidgets.QLabel("Microsoft Flight Simulator Mod Manager", self)
        name.setFont(big_font)
        name.setAlignment(QtCore.Qt.AlignCenter)  # type: ignore
        layout.addWidget(name)

        author = QtWidgets.QLabel(
            "Developed by <a href='https://lksg.me/u/nathan'><span style='color:LightSkyBlue;'>Nathan Vaughn</span></a>",
            self,
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
