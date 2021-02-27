import os

import PySide2.QtCore as QtCore
import PySide2.QtGui as QtGui
import PySide2.QtWidgets as QtWidgets
from fbs_runtime.application_context.PySide2 import ApplicationContext


class about_widget(QtWidgets.QDialog):
    def __init__(
        self,
        parent: QtWidgets.QWidget = None,
        appctxt: ApplicationContext = None,
    ) -> None:
        """Application about widget."""
        QtWidgets.QDialog.__init__(self)
        self.parent = parent # type: ignore
        self.appctxt = appctxt

        self.setWindowTitle("About MSFS Mod Manager")
        self.setWindowFlags(
            QtCore.Qt.WindowSystemMenuHint # type: ignore
            | QtCore.Qt.WindowTitleHint # type: ignore
            | QtCore.Qt.WindowCloseButtonHint
        )
        self.setWindowModality(QtCore.Qt.ApplicationModal) # type: ignore

        self.layout = QtWidgets.QVBoxLayout() # type: ignore
        self.big_font = QtGui.QFont("Arial", 16) # type: ignore
        self.small_font = QtGui.QFont("Arial", 10) # type: ignore

        self.icon = QtWidgets.QLabel(parent=self) # type: ignore
        self.icon.setPixmap(
            QtGui.QPixmap(self.appctxt.get_resource(os.path.join("icons", "icon.png")))
        )
        self.layout.addWidget(self.icon)

        self.name = QtWidgets.QLabel("Microsoft Flight Simulator Mod Manager", self)
        self.name.setFont(self.big_font)
        self.name.setAlignment(QtCore.Qt.AlignCenter) # type: ignore
        self.layout.addWidget(self.name)

        self.author = QtWidgets.QLabel(
            "Developed by <a href='https://nathanv.me'><span style='color:LightSkyBlue;'>Nathan Vaughn</span></a>",
            self,
        )
        self.author.setFont(self.big_font)
        self.author.setOpenExternalLinks(True)
        self.author.setAlignment(QtCore.Qt.AlignCenter) # type: ignore
        self.layout.addWidget(self.author)

        self.license = QtWidgets.QLabel(
            "Copyright 2021 - Licensed under the GPLv3 License", self
        )
        self.license.setFont(self.small_font)
        self.license.setAlignment(QtCore.Qt.AlignCenter) # type: ignore
        self.layout.addWidget(self.license)

        self.no_redistrib = QtWidgets.QLabel(
            "Please do not redistribute without permission", self
        )
        self.no_redistrib.setFont(self.small_font)
        self.no_redistrib.setAlignment(QtCore.Qt.AlignCenter) # type: ignore
        self.layout.addWidget(self.no_redistrib)

        self.setLayout(self.layout)

        self.show()
        self.setFixedSize(self.width(), self.height())
