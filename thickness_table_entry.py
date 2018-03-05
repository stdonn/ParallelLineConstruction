# -*- coding: utf-8 -*-

import os

from PyQt5 import QtWidgets, uic

from HorizonConstructData import HorizonConstructData

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'thickness_table_entry_base.ui'))


class ParallelLineConstructionDockWidget(QtWidgets.QListWidgetItem, FORM_CLASS):
    def __init__(self, parent=None):
        super(ParallelLineConstructionDockWidget, self).__init__(parent)
        self.setupUi(self)

    def closeEvent(self, event):
        event.accept()

    def get_data(self) -> HorizonConstructData:
        construct = self.construct.checked()
        base = self.base.checked()
        name = self.name.text()
        thickness = self.thickness.value()
        color = self.color.color()
        return HorizonConstructData(construct, base, name, thickness, color)

    def set_data(self, data: HorizonConstructData) -> None:
        self.construct.setChecked(data.construct_horizon)
        self.base.setChecked(data.base_horizon)
        self.name.setText(data.name)
        self.thickness.setValue(data.thickness)
        self.color.setColor(data.color)