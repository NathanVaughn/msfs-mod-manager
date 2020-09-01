import os

import PySide2.QtCore as QtCore
import PySide2.QtGui as QtGui
import PySide2.QtWidgets as QtWidgets


class about_widget(QtWidgets.QDialog):
    def __init__(self, parent=None, appctxt=None):
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
        self.font = QtGui.QFont('Arial', 16)

        self.icon = QtWidgets.QLabel()
        self.icon.setPixmap(QtGui.QPixmap(self.appctxt.get_resource(os.path.join("icons", "icon.png"))))
        self.layout.addWidget(self.icon)

        self.name = QtWidgets.QLabel("Microsoft Flight Simulator Mod Manager")
        self.name.setFont(self.font)
        self.name.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addWidget(self.name)

        self.author = QtWidgets.QLabel(
            "Developed by <a href='https://nathanv.me'><span style='color:LightSkyBlue;'>Nathan Vaughn</span></a>"
        )
        self.author.setFont(self.font)
        self.author.setOpenExternalLinks(True)
        self.author.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addWidget(self.author)

        self.license = QtWidgets.QLabel(
            "Copyright 2020 - Licensed under the GPL License"
        )
        self.license.setFont(self.font)
        self.license.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addWidget(self.license)

        self.setLayout(self.layout)

        self.show()
        self.setFixedSize(self.width(), self.height())
