# -*- coding: utf-8 -*-
"""
QGIS plugin: ParallelLineConstruction

This plugin constructs parallel lines based on a given base line

copyright            : (C) 2018 by Stephan Donndorf
email                : stephan@donndorf.info

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import math
from typing import Any, List

from PyQt5.QtCore import QAbstractTableModel, QModelIndex, QRect, QRectF, QSize, QVariant, Qt
from PyQt5.QtGui import QBrush, QColor, QPainter, QPen
from PyQt5.QtWidgets import QCheckBox, QLabel, QStyledItemDelegate, QStyleOptionViewItem, QWidget
from qgis.gui import QgsColorButton


class UnitConstructionData:
    """
    Data storage class for a single unit to be constructed
    """

    # define header name class wide
    __header_names = [
        "construct unit",
        "base unit",
        "name",
        "distance",
        "color"
    ]

    def __init__(self, construct_unit: bool = True, base_unit: bool = False, name: str = "unknown",
                 distance: float = 1, color: QColor = QColor(255, 255, 255)) -> None:
        """
        Initialize the object
        :param construct_unit: Should the unit be constructed?
        :param base_unit: Is this unit the base for further constructions?
        :param name: The unit name
        :param distance: distance to the upper unit
        :param color: color for unit construction
        """
        self.__data = [None, None, None, None, None]
        self.construct_unit = construct_unit
        self.base_unit = base_unit
        self.name = name
        self.distance = distance
        self.color = color

    def __repr__(self) -> str:
        """
        returns a string representation of the object
        :return: returns a string representation of the object
        """
        return "UnitConstructionData <{}, {}, {}, {}, {}>".format(self.name, self.construct_unit, self.base_unit,
                                                                  self.distance, self.color.name())

    def __str__(self) -> str:
        """
        returns a string representation of the object
        :return: returns a string representation of the object
        """
        return "{}\n\tconstruct: {}\n\tbase: {}\n\tdistance: {}\n\tcolor: {}".format(self.name, self.construct_unit,
                                                                                     self.base_unit, self.distance,
                                                                                     self.color.name())

    def __getitem__(self, item: int or List[int]) -> object or List:
        """
        returns the item at position item or a list of items if a slice is requested
        :param item: index of the item(s)
        :return: returns the item at position item or a list of items if a slice is requested
        """
        return self.__data[item]

    def __setitem__(self, index: int, value: Any) -> None:
        """
        Sets the item at position index to the given value
        :param index: index of the item to be changed
        :param value: new value of the item at position index
        :return: Nothing
        :raises IndexError: if index is not between 0 and len(self.__data)
        :raises TypeError: if value type doesn't fit to the requested type (id 0 and 1: bool, 2: str, 3: int, 4: QColor
        """
        if not (0 <= index < len(self.__data)):
            raise IndexError("Wrong key used")
        if index in (0, 1) and not isinstance(value, bool):
            raise TypeError("value must be of type bool")
        if index == 2 and not isinstance(value, str):
            raise TypeError("value must be of type str")
        if index == 3 and not isinstance(value, int):
            raise TypeError("value must be of type int")
        if index == 4 and not isinstance(value, QColor):
            raise TypeError("value must be of type QColor")
        self.__data[index] = value

    # setter and getter
    @property
    def base_unit(self) -> bool:
        """
        returns if the unit is the base unit
        :return: returns if the unit is the base unit
        """
        # noinspection PyTypeChecker
        return self.__data[1]

    @base_unit.setter
    def base_unit(self, value: bool) -> None:
        """
        Sets if the unit is the base unit
        :param value: is the unit the base unit?
        :return: Nothing
        :raises ValueError: if value cannot be converted to type bool
        """
        self.__data[1] = bool(value)

    @property
    def color(self) -> QColor:
        """
        returns the current color of the object
        :return: returns the current color of the object
        """
        # noinspection PyTypeChecker
        return self.__data[4]

    @color.setter
    def color(self, value: QColor) -> None:
        """
        Creates a new QColor object from the given value
        :param value: new color of the object
        :return: Nothing
        """
        self.__data[4] = QColor(value)

    @property
    def construct_unit(self) -> bool:
        """
        returns, if the unit should be constructed
        :return: returns, if the unit should be constructed
        """
        # noinspection PyTypeChecker
        return self.__data[0]

    @construct_unit.setter
    def construct_unit(self, value: bool) -> None:
        """
        Sets the construct unit to the given value
        :param value: should the unit be constructed?
        :return: Nothing
        :raises ValueError: if value cannot be converted to bool
        """
        self.__data[0] = bool(value)

    @property
    def distance(self) -> int:
        """
        returns the distance to the next upper unit
        :return: returns the distance to the next upper unit
        """
        # noinspection PyTypeChecker
        return self.__data[3]

    @distance.setter
    def distance(self, value: int) -> None:
        """
        Sets the distance to the next upper unit
        :param value: distance to the next upper unit
        :return: Northing
        """
        self.__data[3] = int(value)

    @property
    def name(self) -> str:
        """
        returns the current name of the object
        :return: returns the current name of the object
        """
        # noinspection PyTypeChecker
        return self.__data[2]

    @name.setter
    def name(self, value: str) -> None:
        """
        Sets the current name of the object to value
        :param value: new name of the object
        :return: Nothing
        """
        self.__data[2] = str(value)

    # class methods
    @classmethod
    def get_header_index(cls, value: str) -> int:
        """
        returns the index of the field with the given name
        :param value: name of the requested field
        :return: returns the index of the field with the given name
        """
        return cls.__header_names.index(value)

    @classmethod
    def get_header_name(cls, index: int) -> str:
        """
        returns the name of the field at the given index
        :param index: index of the requested field name
        :return: returns the name of name of the field at the given index
        """
        if 0 <= index < len(cls.__header_names):
            return cls.__header_names[index]
        return ""


class UnitConstructionModel(QAbstractTableModel):
    """
    Derived Table Model for the storage of UnitConstructionData
    """

    def __init__(self, data: List[UnitConstructionData] = list(), parent: QWidget = None, *args) -> None:
        """
        Initialize the object
        :param data: import data
        """
        # noinspection PyArgumentList
        QAbstractTableModel.__init__(self, parent, *args)
        self.__data_list = data
        bases = [x.base_unit for x in data]
        if True not in bases and len(data) > 0:
            self.__data_list[0][1] = True
            self.__base_item = 0
        elif len(data) > 0:
            first = bases.index(True)
            for dat in self.__data_list:
                dat.base_unit = False
            self.__data_list[first].base_unit = True
            self.__base_item = first
        else:
            self.__base_item = -1

        self.__header_labels = ["build", "base", "unit name", "distance", "color"]

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> str:
        """
        Derived functions which returns the header data for the given section, orientation and role
        :param section: section of the requested header data
        :param orientation: orientation of the requested header data
        :param role: role of the requested header data
        :return: returns the header data for the given section, orientation and role
        """
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if -1 < section < len(self.__header_labels):
                return self.__header_labels[section]
        return super(QAbstractTableModel, self).headerData(section, orientation, role)

    @property
    def base_item_index(self) -> int:
        """
        returns the index of the base item
        :return: index of the base item
        """
        return self.__base_item

    def columnCount(self, parent: QModelIndex = ...) -> int:
        """
        returns the current column count of the table model
        :param parent: redundant parameter as this derived class isn't a tree model
        :return: returns the current column count of the table model
        """
        return len(self.__header_labels)

    # noinspection PyMethodOverriding
    def data(self, index, role):
        """
        returns the data at the given index and the given role. Derived function.
        :param index: index of the requested data
        :param role: role of the requested data
        :return: returns the data at the given index and the given role
        """
        if not index.isValid():
            return QVariant()
        elif role in (Qt.DisplayRole, Qt.EditRole):
            return QVariant(self.__data_list[index.row()][index.column()])
        elif index.column() == 3 and role == Qt.TextAlignmentRole:
            return Qt.AlignRight
        return QVariant()

    # noinspection PyTypeChecker
    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        """
        Set the editable flag for the given model index. Derived function
        :param index: model index for which the flags are requested
        :return: Qt.ItemFlags
        """
        if not index.isValid():
            return Qt.ItemIsEnabled
        return Qt.ItemIsEditable | super(QAbstractTableModel, self).flags(index)

    # noinspection PyMethodOverriding
    def insertRow(self, row: int, data: UnitConstructionData) -> bool:
        """
        inserts a new row into the model. Derived and adapted function.
        :param row: row index where to insert the new row
        :param data: data to be insert
        :return: if the insert was performed successfully
        """
        self.beginInsertRows(QModelIndex(), row, row)
        if row < 0:
            self.endInsertRows()
            return False
        self.__data_list.insert(row, data)
        self.__check_base(row)
        self.endInsertRows()
        return True

    def move_row_up(self, row: int) -> None:
        """
        Moves the row at index row up, if possible.
        :param row: row index to move up
        :return: Nothing
        """
        if 0 < row < self.rowCount():
            self.beginMoveRows(QModelIndex(), row, row, QModelIndex(), row - 1)
            item = self.__data_list.pop(row)
            self.__data_list.insert(row - 1, item)
            self.endMoveRows()

    def move_row_down(self, row: int) -> None:
        """
        Moves the row at index row down, if possible.
        :param row: row index to move down
        :return: Nothing
        """
        if 0 <= row < self.rowCount() - 1:
            self.beginMoveRows(QModelIndex(), row, row, QModelIndex(), row + 2)
            item = self.__data_list.pop(row)
            self.__data_list.insert(row + 1, item)
            self.endMoveRows()

    def row(self, index: int) -> UnitConstructionData or None:
        """
        returns UnitConstructionData-item at given index
        :param index: index of requested UnitConstructionData-item
        :return: returns the item at given index
        """
        if 0 <= index < self.rowCount():
            return self.__data_list[index]
        return None

    def rowCount(self, parent: QModelIndex = ...) -> Any:
        """
        returns the current row count of the table model
        :param parent: redundant parameter as this derived class isn't a tree model
        :return: returns the current row count of the table model
        """
        return len(self.__data_list)

    # noinspection PyMethodOverriding
    def removeRow(self, row: int) -> bool:
        """
        Removes the row at the given index "row".
        :param row: index of the row to be removed
        :return: True, if the row was removed successfully, else False
        """
        self.beginRemoveRows(QModelIndex(), row, row)
        if 0 <= row < self.rowCount():
            del self.__data_list[row]
            self.__check_base()
            self.endRemoveRows()
            return True
        self.endRemoveRows()
        return False

    def setData(self, index: QModelIndex, value: Any, role: int = Qt.EditRole) -> bool:
        """
        Sets the current data at the given model index and role to value
        :param index: model index to be changed
        :param value: new value to be set
        :param role: role of data
        :return: True, if the data was set successfully, else False
        """
        if not index.isValid():
            return False
        if role == Qt.EditRole:
            self.__data_list[index.row()][index.column()] = value
            if index.column() == 1:
                self.__check_base(index.row())
            # noinspection PyUnresolvedReferences
            self.dataChanged.emit(index, index, [Qt.EditRole])
        return True

    def __check_base(self, row: int = -1) -> None:
        """
        Ensures, that exactly one unit is a base unit. If more than one row is set, the given row index is preferred,
        else the first set value. If now row is set as a base unit, the first unit will be set as base
        :param row: last changed row index
        :return: Nothing
        """
        if self.rowCount() == 0 or not (0 <= row < self.rowCount()):
            return

        found = list()
        for i in range(self.rowCount()):
            if self.__data_list[i].base_unit:
                found.append(i)
                self.__data_list[i].base_unit = False

        if len(found) == 0:
            self.__data_list[0].base_unit = True
            self.__base_item = 0
            return
        index = row if row in found else found[0]
        self.__data_list[index].base_unit = True
        self.__base_item = index


class UnitConstructionDelegate(QStyledItemDelegate):
    """
    Derived delegate class for drawing the UnitConstructionModel
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize the object
        :param args: arguments for initialization of the base class
        :param kwargs: arguments for initialization of the base class
        """
        super(UnitConstructionDelegate, self).__init__(*args, **kwargs)
        self.__checkbox_size = QSize(15, 15)
        self.__color_size = QSize(40, 20)
        self.__label_tmp = QLabel("")

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
        """
        Creates an editor widget for the given index. Derived function.
        :param parent: parent QWidget
        :param option: QStyleOptionViewItem
        :param index: model index for editor creation
        :return: QWidget which represents the editor for the given model index
        """
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

    def setEditorData(self, editor: QWidget, index: QModelIndex) -> None:
        """
        sets the data to the given editor widget based on the model index. Derived function.
        :param editor: editor widget for which the data has to be set
        :param index: model index from which the editor data has to be set
        :return: Nothing
        """
        if index.isValid():
            if index.column() in (0, 1) and isinstance(index.data(), bool):
                editor.setChecked(index.data())
                return
            if index.column() == 4 and isinstance(index.data(), QColor):
                editor.setColor(index.data())
                return
        super().setEditorData(editor, index)

    def setModelData(self, editor: QWidget, model: QAbstractTableModel, index: QModelIndex) -> None:
        """
        Update the model data at the given index from the editor value. Derived function.
        :param editor: data provider
        :param model: data storage
        :param index: index where data has to be updated
        :return: Nothing
        """
        if index.isValid():
            if index.column() in (0, 1):
                model.setData(index, editor.isChecked())
                return
            if index.column() == 4:
                model.setData(index, editor.color())
                return
        super().setModelData(editor, model, index)

    def updateEditorGeometry(self, editor: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """
        update the editor geometry. Derived function.
        :param editor:
        :param option:
        :param index:
        :return: Nothing
        """
        if index.isValid():
            if isinstance(editor, QCheckBox):
                pos_x = int(option.rect.x() + option.rect.width() / 2 - editor.sizeHint().width() / 2)
                pos_y = int(option.rect.y() + option.rect.height() / 2 - editor.sizeHint().height() / 2)
                editor.setGeometry(QRect(pos_x, pos_y, editor.sizeHint().width(), editor.sizeHint().height()))
                return
            if index.column() == 4:
                editor.setGeometry(option.rect)
        super().updateEditorGeometry(editor, option, index)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """
        paint event for drawing the model data
        :param painter: QPainter for the drawing
        :param option: QStyleOptionViewItem
        :param index: model index to be drawn
        :return: Nothing
        """
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

            x = math.trunc(option.rect.x() + option.rect.width() / 2.0 - width / 2.0 + 0.5)
            y = math.trunc(option.rect.y() + option.rect.height() / 2.0 - height / 2.0 + 0.5)

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

            x = math.trunc(option.rect.x() + option.rect.width() / 2.0 - width / 2.0 + 0.5)
            y = math.trunc(option.rect.y() + option.rect.height() / 2.0 - height / 2.0 + 0.5)

            painter.drawRect(x, y, width, height)
            painter.restore()

        # set the distance label
        elif isinstance(index_data, int):
            text = "{:,} m".format(index_data).replace(',', ' ')
            rect = QRectF(option.rect)
            rect.setWidth(rect.width() - 5)
            painter.drawText(rect, Qt.AlignRight | Qt.AlignVCenter, text)

        else:
            super(UnitConstructionDelegate, self).paint(painter, option, index)

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        """
        Returns a size hint for the object at the given index
        :param option: QStyleOptionViewItem
        :param index: model index for the requested size hint
        :return: a QSize object with given hint
        """
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
