# -*- coding: utf-8 -*-

#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2015 Pierre Vacher <prrvchr@gmail.com>                  *
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   This program is distributed in the hope that it will be useful,       *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Library General Public License for more details.                  *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with this program; if not, write to the Free Software   *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************
""" TinyG2 panel Plugin object """
from __future__ import unicode_literals

from PySide import QtCore, QtGui
import FreeCADGui
from App import Script as AppScript
from Gui import UsbPoolPanel, TinyG2Model, Script as GuiScript


class PoolTaskPanel(UsbPoolPanel.PoolTaskPanel):

    def __init__(self, obj):
        view = PoolPanel()
        model = obj.ViewObject.Proxy.Model
        if model.obj is None: model.obj = obj
        view.setModel(model)
        self.form = [view]


class SettingTabBar(QtGui.QTabBar):

    tabIndex = QtCore.Signal(unicode)

    def __init__(self, parent):
        QtGui.QTabBar.__init__(self, parent)
        self.setShape(QtGui.QTabBar.RoundedWest)
        self.setDocumentMode(True)
        self.setTabData(self.addTab("All"), "r")
        self.setTabData(self.addTab("Axis"), "q")
        self.setTabData(self.addTab("Home"), "o")
        self.setTabData(self.addTab("Motor"), "m")
        self.setTabData(self.addTab("Power"), "p1")
        self.setTabData(self.addTab("System"), "sys")
        self.currentChanged.connect(self.onTabIndex)

    @QtCore.Slot(int)
    def onTabIndex(self, index):
        self.tabIndex.emit(self.tabData(index))


class PoolPanel(QtGui.QTabWidget):

    def __init__(self):
        QtGui.QTabWidget.__init__(self)
        self.setWindowIcon(QtGui.QIcon("icons:Usb-Pool.xpm"))
        setting = QtGui.QWidget()
        setting.setLayout(QtGui.QHBoxLayout())
        self.tabbar = SettingTabBar(self)
        setting.layout().addWidget(self.tabbar)
        #model.state.connect(tabbar.on_state)
        self.tableview = UsbPoolView(self)
        setting.layout().addWidget(self.tableview)
        self.addTab(setting, "Current settings")
        monitor = QtGui.QWidget()
        monitor.setLayout(QtGui.QGridLayout())
        monitor.layout().addWidget(QtGui.QLabel("Line/N:"), 0, 0, 1, 1)
        line = QtGui.QLabel()
        monitor.layout().addWidget(line, 0, 1, 1, 1)
        monitor.layout().addWidget(QtGui.QLabel("/"), 0, 2, 1, 1)
        nline = QtGui.QLabel()
        monitor.layout().addWidget(nline, 0, 3, 1, 1)
        #model.nline.connect(nline.setText)
        monitor.layout().addWidget(QtGui.QLabel("GCode:"), 1, 0, 1, 1)
        gcode = QtGui.QLabel()
        monitor.layout().addWidget(gcode, 1, 1, 1, 3)
        monitor.layout().addWidget(QtGui.QLabel("Buffers:"), 2, 0, 1, 1)
        buffers = QtGui.QLabel()
        monitor.layout().addWidget(buffers, 2, 1, 1, 3)
        #model.buffers.connect(buffers.setText)
        monitor.layout().addWidget(QtGui.QLabel("PosX:"), 3, 0, 1, 1)
        posx = QtGui.QLabel()
        monitor.layout().addWidget(posx, 3, 1, 1, 3)
        #model.posx.connect(posx.setText)
        monitor.layout().addWidget(QtGui.QLabel("PosY:"), 4, 0, 1, 1)
        posy = QtGui.QLabel()
        monitor.layout().addWidget(posy, 4, 1, 1, 3)
        #model.posy.connect(posy.setText)
        monitor.layout().addWidget(QtGui.QLabel("PosZ:"), 5, 0, 1, 1)
        posz = QtGui.QLabel()
        monitor.layout().addWidget(posz, 5, 1, 1, 3)
        #model.posz.connect(posz.setText)
        monitor.layout().addWidget(QtGui.QLabel("Vel:"), 6, 0, 1, 1)
        vel = QtGui.QLabel()
        monitor.layout().addWidget(vel, 6, 1, 1, 3)
        #model.vel.connect(vel.setText)
        monitor.layout().addWidget(QtGui.QLabel("Feed:"), 7, 0, 1, 1)
        feed = QtGui.QLabel()
        monitor.layout().addWidget(feed, 7, 1, 1, 3)
        #model.feed.connect(feed.setText)
        monitor.layout().addWidget(QtGui.QLabel("Status:"), 8, 0, 1, 1)
        stat = QtGui.QLabel()
        monitor.layout().addWidget(stat, 8, 1, 1, 3)
        #model.stat.connect(stat.setText)
        self.addTab(monitor, "Upload monitor")

    def setModel(self, model):
        self.tabbar.tabIndex.connect(model.setRootIndex)
        model.title.connect(self.onTitle)
        model.title.emit("test")
        self.tableview.setModel(model)

    @QtCore.Slot(unicode)
    def onTitle(self, title):
        self.setWindowTitle(title)


class UsbPoolView(QtGui.QTreeView):
    
    unit = QtCore.Signal(QtCore.QPoint, int)

    def __init__(self, parent):
        QtGui.QTreeView.__init__(self, parent)
        model = TinyG2Model.PoolBaseModel()
        i = model._header.index("Value")
        self.setItemDelegateForColumn(i, PoolDelegate(self))        
        self.header().setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.header().customContextMenuRequested.connect(self.onUnit)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

    def setModel(self, model):
        model.rootIndex.connect(self.setRootIndex)
        self.unit.connect(model.onUnit)
        QtGui.QTreeView.setModel(self, model)

    @QtCore.Slot(int)
    def onUnit(self, pos):
        self.unit.emit(self.mapToGlobal(pos), self.header().logicalIndexAt(pos))


class PoolDelegate(QtGui.QStyledItemDelegate):

    def __init__(self, parent):
        QtGui.QStyledItemDelegate.__init__(self, parent)

    def createEditor(self, parent, option, index):
        node = index.internalPointer()
        key = node.key
        if key in ["m48e", "saf", "lim", "mfoe", "sl"]:
            menus = ("disable", "enable")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif key == "ej":
            menus = ("text", "JSON")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif key == "js":
            menus = ("relaxed", "strict")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif key == "gdi":
            menus = ("G90", "G91")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif key == "gun":
            menus = ("G20 inches", "G21 mm")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif key == "gpl":
            menus = ("G17", "G18", "G19")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif key == "gpa":
            menus = ("G61", "G61.1", "G64")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif key in ["cofp", "comp"]:
            menus = ("low is ON", "high is ON")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif key in ["unit"]:
            menus = ("Inches", "Metric")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo        
        elif key in ["coph", "spph"]:
            menus = ("no", "pause_on_hold")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif key == "tv":
            menus = ("silent", "verbose")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif key == "sv" and node.parent.key == "sv":
            menus = ("off", "filtered", "verbose")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif key == "spep":
            menus = ("active_low", "active_high")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif key == "spdp":
            menus = ("CW_low", "CW_high")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif key == "jv":
            menus = ("silent", "footer", "messages", "configs", "linenum", "verbose")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif key == "am":
            menus = ("disabled", "standard", "inhibited", "radius")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif key == "hi":
            menus = ("disable homing", "x axis", "y axis", "z axis", "a axis", "b axis", "c axis")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif key == "hd":
            menus = ("search-to-negative", "search-to-positive")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif key == "ma":
            menus = ("X", "Y", "Z", "A", "B", "C")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif key == "po":
            menus = ("normal", "reverse")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif key == "qv":
            menus = ("off", "single", "triple")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif key == "pm":
            menus = ("disabled", "always on", "in cycle", "when moving")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i)
            return combo
        elif key == "gco":
            menus = ("G54", "G55", "G56", "G57", "G58", "G59")
            combo = QtGui.QComboBox(parent)
            for i, m in enumerate(menus):
                combo.addItem(m, i+1)
            return combo
        elif key == "mi":
            menus = ("1", "2", "4", "8", "16", "32")
            combo = QtGui.QComboBox(parent)
            for i in menus:
                combo.addItem(i, i)
            return combo
        elif key == "sv" and node.parent.key != "sv":
            spin = QtGui.QSpinBox(parent)
            spin.setRange(0, 50000)
            return spin
        elif key in ["fr", "vm", "jm", "csl", "csh", "wsh", "wsl", "frq"]:
            spin = QtGui.QSpinBox(parent)
            spin.setRange(0, 50000)
            return spin
        elif key == "jh":
            spin = QtGui.QSpinBox(parent)
            spin.setRange(0, 1000000)
            return spin
        elif key == "si":
            spin = QtGui.QSpinBox(parent)
            spin.setRange(100, 50000)
            return spin
        elif key == "spdw":
            spin = QtGui.QDoubleSpinBox(parent)
            spin.setRange(0, 10000)
            spin.setDecimals(1)
            return spin
        elif key in ["lv", "mt"]:
            spin = QtGui.QDoubleSpinBox(parent)
            spin.setRange(0, 10000)
            spin.setDecimals(2)
            return spin
        elif key == "ja":
            spin = QtGui.QDoubleSpinBox(parent)
            spin.setRange(0, 1000)
            spin.setDecimals(2)
            return spin
        elif key == "mfo":
            spin = QtGui.QDoubleSpinBox(parent)
            spin.setRange(0.05, 2)
            spin.setDecimals(3)
            return spin
        elif key in ["cph", "cpl", "pl", "wpl", "wph", "pof"]:
            spin = QtGui.QDoubleSpinBox(parent)
            spin.setRange(0, 1)
            spin.setDecimals(3)
            return spin
        elif key == "sa":
            spin = QtGui.QDoubleSpinBox(parent)
            spin.setRange(0, 10000)
            spin.setDecimals(3)
            return spin
        elif key in ["lb", "zb", "tn", "tm", "x", "y", "z", "a", "b", "c"]:
            spin = QtGui.QDoubleSpinBox(parent)
            spin.setRange(-10000, 10000)
            spin.setDecimals(3)
            return spin
        elif key in ["tr", "ct"]: #"jd"
            spin = QtGui.QDoubleSpinBox(parent)
            spin.setRange(-10000, 10000)
            spin.setDecimals(4)
            return spin
        return QtGui.QStyledItemDelegate.createEditor(self, parent, option, index)

    def setEditorData(self, editor, index):
        if isinstance(editor, QtGui.QComboBox):
            editor.setCurrentIndex(editor.findData(index.model().data(index)))
        elif isinstance(editor, QtGui.QSpinBox):
            editor.setValue(int(index.model().data(index)))
        elif isinstance(editor, QtGui.QDoubleSpinBox):
            editor.setValue(float(index.model().data(index)))
        elif isinstance(editor, QtGui.QLineEdit):
            editor.setText(index.model().data(index).strip())

    def setModelData(self, editor, model, index):
        if isinstance(editor, QtGui.QComboBox):
            model.setData(index, editor.itemData(editor.currentIndex()), QtCore.Qt.EditRole)
        elif isinstance(editor, QtGui.QSpinBox):
            model.setData(index, editor.value(), QtCore.Qt.EditRole)
        elif isinstance(editor, QtGui.QDoubleSpinBox):
            model.setData(index, editor.value(), QtCore.Qt.EditRole)
        elif isinstance(editor, QtGui.QLineEdit):
            model.setData(index, editor.text(), QtCore.Qt.EditRole)


class TaskWatcher:

    def __init__(self):
        self.title = b"TinyG2 monitor"
        self.icon = b"icons:Usb-Pool.xpm"
        self.model = TinyG2Model.PoolBaseModel()
        self.view = PoolPanel()
        self.widgets = [self.view]

    def shouldShow(self):
        for obj in FreeCADGui.Selection.getSelection():
            if AppScript.getObjectType(obj) == "App::UsbPool" and\
               GuiScript.getObjectViewType(obj.ViewObject) == "Gui::UsbTinyG2":
                self.view.setModel(obj.ViewObject.Proxy.Model)
                return True
        self.view.setModel(self.model)
        return False
