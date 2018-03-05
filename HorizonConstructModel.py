# -*- coding: utf-8 -*-

from typing import List

from PyQt5.QtCore import QAbstractTableModel, QVariant, Qt
from PyQt5.QtWidgets import QWidget

from HorizonConstructData import HorizonConstructData


class HorizonConstructModel(QAbstractTableModel):
    def __init__(self, data: List[HorizonConstructData], parent: QWidget = None, *args) -> None:
        """
        :param data: import data
        """
        QAbstractTableModel.__init__(self, parent, *args)
        self.listdata = data

    def rowCount(self, parent):
        return len(self.listdata)

    def columnCount(self, parent):
        return 5

    def data(self, index, role):
        if not index.isValid():
            return QVariant()
        elif role != Qt.DisplayRole:
            return QVariant()
        # print("Returning:\n{}".format(self.listdata[index.row()]))
        return QVariant(self.listdata[index.row()].data[index.column()])
