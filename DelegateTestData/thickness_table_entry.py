# -*- coding: utf-8 -*-

import os

from PyQt5 import QtWidgets, uic

from DelegateTestData.HorizonConstructData import HorizonConstructData

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'thickness_table_entry_base.ui'))


class ThicknessTableEntry(QtWidgets.QWidget, FORM_CLASS):
    def __init__(self, data: HorizonConstructData, parent:QtWidgets=None) -> None:
        super(ThicknessTableEntry, self).__init__(parent)
        self.setupUi(self)
        self.set_data(data)
        self.__color = data.color

    def closeEvent(self, event):
        event.accept()

    def get_data(self) -> HorizonConstructData:
        construct = self.construct.checked()
        base = self.base.checked()
        name = self.name.text()
        thickness = int(self.thickness.text()[:-2])
        # color = self.color.color()
        color = self.__color
        return HorizonConstructData(construct, base, name, thickness, color)

    def set_data(self, data: HorizonConstructData) -> None:
        self.construct.setChecked(data.construct_horizon)
        self.base.setChecked(data.base_horizon)
        self.name.setText(data.name)
        self.thickness.setText("{} m".format(data.thickness))
        self.color.setStyleSheet("background: {}".format(data.color.name()))