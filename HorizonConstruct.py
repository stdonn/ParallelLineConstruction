# -*- coding: utf-8 -*-

from typing import Any, List

from PyQt5.QtCore import QAbstractTableModel, QModelIndex, QRect, QRectF, QSize, QVariant, Qt
from PyQt5.QtGui import QBrush, QColor, QPainter, QPen
from PyQt5.QtWidgets import QCheckBox, QLabel, QStyledItemDelegate, QStyleOptionViewItem, QWidget

from qgis.core import QgsMessageLog
from qgis.gui import QgsColorButton


class HorizonConstructData:
    # define header name class wide
    __header_names = [
        "contruct unit",
        "base unit",
        "name",
        "thickness",
        "color"
    ]

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

    def __setitem__(self, key: int, value: Any) -> None:
        if not (0 <= key < len(self.__data)):
            raise IndexError("Wrong key used")
        if key in (0, 1) and not isinstance(value, bool):
            raise TypeError("value must be of type bool")
        if key == 2 and not isinstance(value, str):
            raise TypeError("value must be of type str")
        if key == 3 and not isinstance(value, int):
            raise TypeError("value must be of type int")
        if key == 4 and not isinstance(value, QColor):
            raise TypeError("value must be of type QColor")
        self.__data[key] = value

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

    @classmethod
    def get_header_index(cls, value: str) -> int:
        return cls.__header_names.index(value)

    @classmethod
    def get_header_name(cls, value: int) -> str:
        if 0 <= value < len(cls.__header_names):
            return cls.__header_names[value]
        return ""


class HorizonConstructModel(QAbstractTableModel):
    def __init__(self, data: List[HorizonConstructData], parent: QWidget = None, *args) -> None:
        """
        :param data: import data
        """
        QAbstractTableModel.__init__(self, parent, *args)
        self.__listdata = data
        bases = [x.base_horizon for x in data]
        if not True in bases and len(data) > 0:
            self.__listdata[0][1] = True
        elif len(data) > 0:
            first = bases.index(True)
            for dat in self.__listdata:
                dat.base_horizon = False
            self.__listdata[first].base_horizon = True

        self.__header_labels = ["build", "base", "unit name", "thickness", "color"]

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if -1 < section < len(self.__header_labels):
                return self.__header_labels[section]
        return super(QAbstractTableModel, self).headerData(section, orientation, role)

    def columnCount(self, parent: QModelIndex = ...):
        return len(self.__header_labels)

    def data(self, index, role):
        if not index.isValid():
            return QVariant()
        elif role in (Qt.DisplayRole, Qt.EditRole):
            return QVariant(self.__listdata[index.row()][index.column()])
        elif index.column() == 3 and role == Qt.TextAlignmentRole:
            return Qt.AlignRight
        return QVariant()

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if not index.isValid():
            return Qt.ItemIsEnabled
        return Qt.ItemIsEditable | super(QAbstractTableModel, self).flags(index)

    def insertRow(self, row: int, data: HorizonConstructData) -> bool:
        self.beginInsertRows(QModelIndex(), row, row)
        if row < 0:
            self.endInsertRows()
            return False
        self.__listdata.insert(row, data)
        self.__check_base(row)
        self.endInsertRows()
        return True

    def moveRowUp(self, row: int):
        if 0 < row < self.rowCount():
            self.beginMoveRows(QModelIndex(), row, row, QModelIndex(), row - 1)
            item = self.__listdata.pop(row)
            self.__listdata.insert(row - 1, item)
            self.endMoveRows()

    def moveRowDown(self, row: int):
        if 0 <= row < self.rowCount() - 1:
            self.beginMoveRows(QModelIndex(), row, row, QModelIndex(), row + 2)
            item = self.__listdata.pop(row)
            self.__listdata.insert(row + 1, item)
            self.endMoveRows()

    def rowCount(self, parent: QModelIndex = ...) -> Any:
        return len(self.__listdata)

    def removeRow(self, row: int) -> bool:
        self.beginRemoveRows(QModelIndex(), row, row)
        if 0 <= row < self.rowCount():
            del self.__listdata[row]
            self.__check_base()
            self.endRemoveRows()
            return True
        self.endRemoveRows()
        return False

    def setData(self, index: QModelIndex, value: Any, role: int = Qt.EditRole) -> bool:
        if not index.isValid():
            return False
        if role == Qt.EditRole:
            self.__listdata[index.row()][index.column()] = value
            if index.column() == 1:
                self.__check_base(index.row())
            self.dataChanged.emit(index, index, [Qt.EditRole])
        return True

    def __check_base(self, row: int = -1) -> None:
        if self.rowCount() == 0 or not (0 <= row < self.rowCount()):
            return

        found = list()
        for i in range(self.rowCount()):
            if self.__listdata[i].base_horizon:
                found.append(i)
                self.__listdata[i].base_horizon = False

        if len(found) == 0:
            self.__listdata[0].base_horizon = True
            return
        index = row if row in found else found[0]
        self.__listdata[index].base_horizon = True


class HorizonConstructDelegate(QStyledItemDelegate):
    def __init__(self, *args, **kwargs):
        super(HorizonConstructDelegate, self).__init__(*args, **kwargs)
        self.__checkbox_size = QSize(15, 15)
        self.__color_size = QSize(40, 20)
        self.__label_tmp = QLabel("")

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
        if index.isValid():
            if index.column() in (0, 1):
                checkbox = QCheckBox(parent)
                checkbox.setFocusPolicy(Qt.StrongFocus)
                return checkbox
            if index.column() == 4:
                color_button = QgsColorButton(parent)
                color_button.setFocusPolicy(Qt.StrongFocus)
                return color_button
        return super().createEditor(parent, option, index)

    def setEditorData(self, editor: QWidget, index: QModelIndex):
        if index.isValid():
            if index.column() in (0, 1) and isinstance(index.data(), bool):
                editor.setChecked(index.data())
                return
            if index.column() == 4 and isinstance(index.data(), QColor):
                editor.setColor(index.data())
                return
        super().setEditorData(editor, index)

    def setModelData(self, editor: QWidget, model: QAbstractTableModel, index: QModelIndex) -> None:
        if index.isValid():
            if index.column() in (0, 1):
                model.setData(index, editor.isChecked())
                return
            if index.column() == 4:
                model.setData(index, editor.color())
                return
        super().setModelData(editor, model, index)

    def updateEditorGeometry(self, editor: QWidget, option: QStyleOptionViewItem, index: QModelIndex):
        if index.isValid():
            if isinstance(editor, QCheckBox):
                posx = int(option.rect.x() + option.rect.width() / 2 - editor.sizeHint().width() / 2)
                posy = int(option.rect.y() + option.rect.height() / 2 - editor.sizeHint().height() / 2)
                editor.setGeometry(QRect(posx, posy, editor.sizeHint().width(), editor.sizeHint().height()))
                return
            if index.column() == 4:
                editor.setGeometry(option.rect)
        super().updateEditorGeometry(editor, option, index)

    def paint(self, painter, option, index):
        index_data = index.data()

        # set the checkboxes for the boolean values
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

        # set the color rect
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

        # set the thickness label
        elif isinstance(index_data, int):
            text = "{:,} m".format(index_data).replace(',', ' ')
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
        if isinstance(index.data(), int):
            self.__label_tmp.setText("{:,} m".format(index.data()).replace(',', ' '))
            size = self.__label_tmp.sizeHint()
            size.setWidth(size.width() + 5)
            return size
        return super().sizeHint(option, index)
