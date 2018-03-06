# -*- coding: utf-8 -*-

from typing import List

from PyQt5.QtCore import QAbstractTableModel, QModelIndex, QRectF, QSize, QVariant, Qt
from PyQt5.QtGui import QBrush, QColor, QPainter, QPen
from PyQt5.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem, QWidget

from qgis.core import QgsMessageLog


class HorizonConstructData:
    def __init__(self, construct_horizon=True, base_horizon=False, name="unknown", thickness=1,
                 color=QColor(255, 255, 255)):
        self.__data = [None, None, None, None, None]
        self.construct_horizon = construct_horizon
        self.base_horizon = base_horizon
        self.name = name
        self.thickness = thickness
        self.color = color

    def __repr__(self):
        return "HorizonConstructData <{}, {}, {}, {}, {}>".format(self.name, self.construct_horizon, self.base_horizon,
                                                                  self.thickness, self.color.name())

    def __str__(self):
        return "{}\n\tconstruct: {}\n\tbase: {}\n\tthickness: {}\n\tcolor: {}".format(self.name, self.construct_horizon,
                                                                                      self.base_horizon, self.thickness,
                                                                                      self.color.name())

    def __getitem__(self, item: int or List[int]) -> object or List:
        return self.__data[item]

    @property
    def base_horizon(self) -> bool:
        return self.__data[1]

    @base_horizon.setter
    def base_horizon(self, value: bool) -> None:
        self.__data[1] = bool(value)

    @property
    def color(self) -> QColor:
        return self.__data[4]

    @color.setter
    def color(self, value: QColor) -> None:
        self.__data[4] = QColor(value)

    @property
    def construct_horizon(self) -> bool:
        return self.__data[0]

    @construct_horizon.setter
    def construct_horizon(self, value: bool) -> None:
        self.__data[0] = bool(value)

    @property
    def name(self) -> str:
        return self.__data[2]

    @name.setter
    def name(self, value: str) -> None:
        self.__data[2] = str(value)

    @property
    def thickness(self) -> int:
        return self.__data[3]

    @thickness.setter
    def thickness(self, value: int) -> None:
        self.__data[3] = int(value)


class HorizonConstructModel(QAbstractTableModel):
    def __init__(self, data: List[HorizonConstructData], parent: QWidget = None, *args) -> None:
        """
        :param data: import data
        """
        QAbstractTableModel.__init__(self, parent, *args)
        self.listdata = data
        self.header_labels = ["build", "base", "unit name", "thickness", "color"]

    def headerData(self, section:int, orientation:Qt.Orientation, role:int=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if -1 < section < len(self.header_labels):
                return self.header_labels[section]
        return super(QAbstractTableModel, self).headerData(section, orientation, role)

    def columnCount(self, parent):
        return len(self.header_labels)

    def data(self, index, role):
        if not index.isValid():
            return QVariant()
        elif role == Qt.DisplayRole:
            return QVariant(self.listdata[index.row()][index.column()])
        elif index.column() == 3 and role == Qt.TextAlignmentRole:
            return Qt.AlignRight
        return QVariant()

    def insertRow(self, row: int, parent: QModelIndex = QModelIndex()) -> None:
        self.beginInsertRows(parent, row, row)
        self.endInsertRows()

    def rowCount(self, parent):
        return len(self.listdata)



class HorizonConstructDelegate(QStyledItemDelegate):
    def __init__(self, *args, **kwargs):
        super(HorizonConstructDelegate, self).__init__(*args, **kwargs)
        self.__checkbox_size = QSize(15, 15)
        self.__color_size = QSize(40, 20)

    def paint(self, painter, option, index):
        index_data = index.data()
        if isinstance(index_data, bool):
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing, True)

            pen = QPen(Qt.SolidLine)
            pen.setColor(Qt.black)
            pen.setWidth(1)
            painter.setPen(pen)

            brush = QBrush()
            if index_data:
                brush.setStyle(Qt.SolidPattern)
            else:
                brush.setStyle(Qt.NoBrush)
            brush.setColor(Qt.black)
            painter.setBrush(brush)

            width = self.__checkbox_size.width() - 5
            height = self.__checkbox_size.height() - 5

            x = option.rect.x() + option.rect.width() / 2.0 - width / 2.0
            y = option.rect.y() + option.rect.height() / 2.0 - height / 2.0

            painter.drawRect(x, y, width, height)
            painter.restore()

        elif isinstance(index_data, QColor):
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing, True)

            painter.setPen(Qt.NoPen)

            brush = QBrush(Qt.SolidPattern)
            brush.setColor(index_data)

            painter.setBrush(brush)

            width = self.__color_size.width() - 6
            height = self.__color_size.height() - 6

            x = option.rect.x() + option.rect.width() / 2.0 - width / 2.0
            y = option.rect.y() + option.rect.height() / 2.0 - height / 2.0

            painter.drawRect(x, y, width, height)
            painter.restore()

        elif isinstance(index_data, int):
            text = str(index_data) + " m"
            rect = QRectF(option.rect)
            rect.setWidth(rect.width() - 5)
            painter.drawText(rect, Qt.AlignRight | Qt.AlignVCenter, text)

        else:
            super(HorizonConstructDelegate, self).paint(painter, option, index)

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex):
        if isinstance(index.data(), bool):
            return self.__checkbox_size
        if isinstance(index.data(), QColor):
            return self.__color_size
        return super().sizeHint(option, index)
