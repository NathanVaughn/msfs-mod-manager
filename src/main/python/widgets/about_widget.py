import os

import PySide2.QtCore as QtCore
import PySide2.QtGui as QtGui
import PySide2.QtWidgets as QtWidgets


class about_widget(QtWidgets.QDialog):
    def __init__(self, parent=None, appctxt=None):
        """Application about widget."""
        QtWidgets.QDialog.__init__(self)
        self.parent = parent
        self.appctxt = appctxt

        self.setWindowTitle("About MSFS Mod Manager")
        self.setWindowFlags(
            QtCore.Qt.WindowSystemMenuHint
            | QtCore.Qt.WindowTitleHint
            | QtCore.Qt.WindowCloseButtonHint
        )
        self.setWindowModality(QtCore.Qt.ApplicationModal)

        self.layout = QtWidgets.QVBoxLayout()
        self.big_font = QtGui.QFont("Arial", 16)
        self.small_font = QtGui.QFont("Arial", 10)

        self.icon = QtWidgets.QLabel(parent=self)
        self.icon.setPixmap(
            QtGui.QPixmap(self.appctxt.get_resource(os.path.join("icons", "icon.png")))
        )
        self.layout.addWidget(self.icon)

        self.name = QtWidgets.QLabel("Microsoft Flight Simulator Mod Manager", self)
        self.name.setFont(self.big_font)
        self.name.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addWidget(self.name)

        self.author = QtWidgets.QLabel(
            "Developed by <a href='https://nathanv.me'><span style='color:LightSkyBlue;'>Nathan Vaughn</span></a>",
            self,
        )
        self.author.setFont(self.big_font)
        self.author.setOpenExternalLinks(True)
        self.author.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addWidget(self.author)

        self.license = QtWidgets.QLabel(
            "Copyright 2020 - Licensed under the GPLv3 License", self
        )
        self.license.setFont(self.small_font)
        self.license.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addWidget(self.license)

        self.no_redistrib = QtWidgets.QLabel(
            "Please do not redistribute without permission", self
        )
        self.no_redistrib.setFont(self.small_font)
        self.no_redistrib.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addWidget(self.no_redistrib)

        self.setLayout(self.layout)

        self.show()
        self.setFixedSize(self.width(), self.height())
