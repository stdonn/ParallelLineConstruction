# -*- coding: utf-8 -*-

from PyQt5 import QtCore
from PyQt5.QtCore import QVariant
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QApplication, QListView, QStyledItemDelegate

import sys

from HorizonConstructData import HorizonConstructData
from HorizonConstructModel import HorizonConstructModel

class HorizonConstructDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        index_data = index.data()
        if isinstance(index_data, HorizonConstructData):
            if option.state & QStyle.State_Selected:
                painter.fillRect(option.rect, option.palette.highlight())

            starRating.paint(painter, option.rect, option.palette,
                    StarRating.ReadOnly)
        else:
            super(StarDelegate, self).paint(painter, option, index)

    def sizeHint(self, option, index):
        starRating = index.data()
        if isinstance(starRating, StarRating):
            return starRating.sizeHint()
        else:
            return super(StarDelegate, self).sizeHint(option, index)

    def createEditor(self, parent, option, index):
        starRating = index.data()
        if isinstance(starRating, StarRating):
            editor = StarEditor(parent)
            editor.editingFinished.connect(self.commitAndCloseEditor)
            return editor
        else:
            return super(StarDelegate, self).createEditor(parent, option, index)

    def setEditorData(self, editor, index):
        starRating = index.data()
        if isinstance(starRating, StarRating):
            editor.setStarRating(starRating)
        else:
            super(StarDelegate, self).setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        starRating = index.data()
        if isinstance(starRating, StarRating):
            model.setData(index, editor.starRating())
        else:
            super(StarDelegate, self).setModelData(editor, model, index)

    def commitAndCloseEditor(self):
        editor = self.sender()
        self.commitData.emit(editor)
        self.closeEditor.emit(editor)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    data = list()
    data.append(HorizonConstructData(True, False, "mo", 70, QColor(10, 255, 20, 0)))
    data.append(HorizonConstructData(True, False, "mm", 100, QColor(10, 150, 20, 0)))
    data.append(HorizonConstructData(True, False, "mu", 110, QColor(10, 100, 20, 0)))
    data.append(HorizonConstructData(True, False, "so", 150, QColor(255, 255, 20, 0)))

    model = HorizonConstructModel(data)

    v = QListView()
    v.setModel(model)
    v.show()

    sys.exit(app.exec_())

    var = QVariant(data)
    for val in var.value():
        print(str(val))
