from PyQt5 import QtCore, QtGui, QtWidgets
from functools import partial
from collections import OrderedDict
from datetime import datetime
import configargparse
import sys
import os
import os.path as op
from backend_subclasses import *
from tempfile import gettempdir

# parameter tree (non-gui-components) =============================================================
DATA_PARAM = QtCore.Qt.UserRole+1
DATA_TREE = DATA_PARAM+1

class paramTree():
    @staticmethod
    def createTree(name, children):
        PG = parameter(name = name, children = children, type = parameter.types.group)
        return PG

    @staticmethod
    def createExampleTree():
        PT = paramTree.createTree(name='params', children= [])
        testchildren = [
            parameter(name = "examples", type = parameter.types.group, children = [
                parameter(name = "str", type = parameter.types.group, children = 
                [
                parameter(name = 'string, readonly',        type = parameter.types.str, value = "", flags = parameter.FLAG_READONLY),
                parameter(name = 'string, writable',        type = parameter.types.str, value = ""),
                parameter(name = 'string, dropdown',        type = parameter.types.str, value = "", choices = ["a", "b", "c"]),
                parameter(name = 'string, radiobuttons',    type = parameter.types.str, value = "", choices = ["d", "e", "f"], flags = parameter.FLAG_RADIOBUTTONCHOICES),
                parameter(name = 'string, path',            type = parameter.types.str, value = "", flags = parameter.FLAG_BROWSEPATH),
                ]),
            parameter(name = "bool", type = parameter.types.group, children = 
                [
                parameter(name = 'bool, readonly',          type = parameter.types.bool, value = False, flags = parameter.FLAG_READONLY),
                parameter(name = 'bool',                    type = parameter.types.bool, value = True),
                ]),
            parameter(name = "int", type = parameter.types.group, children = 
                [
                parameter(name = 'int, readonly',           type = parameter.types.int, value = 0, flags = parameter.FLAG_READONLY),
                parameter(name = 'int',                     type = parameter.types.int, value = 1),
                parameter(name = 'int, limited',            type = parameter.types.int, value = 0, limits = [-10,10]),
                parameter(name = 'int, dropdown',           type = parameter.types.int, value = -1, choices = [1,2,3,4]),
                parameter(name = 'int, radiobuttons',       type = parameter.types.int, value = -2, choices = [5,6,7,8], flags = parameter.FLAG_RADIOBUTTONCHOICES),
                ]),
            parameter(name = "float", type = parameter.types.group, children = 
                [
                parameter(name = 'float, readonly',           type = parameter.types.float, value = 0, flags = parameter.FLAG_READONLY),
                parameter(name = 'float',                     type = parameter.types.float, value = 1),
                parameter(name = 'float, limited',            type = parameter.types.float, value = 0, limits = [-10,10]),
                parameter(name = 'float, dropdown',           type = parameter.types.float, value = -1.0, choices = [1.0,2.0,3.0,4.0]),
                parameter(name = 'float, radiobuttons',       type = parameter.types.float, value = -2.0, choices = [5.0,6.0,7.0,8.0], flags = parameter.FLAG_RADIOBUTTONCHOICES),
                ]),
            parameter(name = "action", type = parameter.types.group, children = 
                [
                parameter(name = 'pushbutton',        type = parameter.types.function, value = ("print values to stdout", lambda: print(PT.getValues()) )),
                ])
            ])
        ]
        PT.timer = QtCore.QTimer()
        PT.timer.t0 = datetime.now().timestamp()
        def timefcn1():
            fTime = datetime.now().timestamp()-PT.timer.t0
            iTime = round(fTime)
            PT["examples"]["str"]['string, readonly'].value = "{} seconds since init".format(iTime)
            PT["examples"]["bool"]['bool, readonly'].value = (iTime % 2) >0
            PT["examples"]["int"]['int, readonly'].value = iTime
            PT["examples"]["float"]['float, readonly'].value = iTime
        PT.timer.timeout.connect(timefcn1)
        #PT.connect(lambda: print(PT.getValues()))
        PT.timer.start(1)
        for tc in testchildren: PT.appendChild(tc)
        return PT

    @staticmethod
    def createWidget(name, children):
        pw = parameterWidget()
        pw.setParameters(paramTree.createTree(name, children))
        return pw

    @staticmethod
    def createExampleWidget():
        pw = parameterWidget()
        pw.setParameters(paramTree.createExampleTree())
        return pw

    @staticmethod
    def createItem(param, tree):
        if      param.type == parameter.types.group:    return QtTreeWidgetParameter(param, tree)
        elif    param.type == parameter.types.str:      return QtTreeWidgetStringParameter(param, tree)
        elif    param.type == parameter.types.function: return QtTreeWidgetFunctionParameter(param, tree)
        elif    param.type == parameter.types.bool:     return QtTreeWidgetBoolParameter(param, tree)
        elif    param.type == parameter.types.int:      return QtTreeWidgetIntParameter(param, tree)
        elif    param.type == parameter.types.float:    return QtTreeWidgetFloatParameter(param, tree)
        else:   raise ValueError("Invalid parameter type")
# widget-based parameter tree implementation ======================================================
class parameterTypes():
    int         = int
    str         = str
    float       = float
    bool        = bool
    group       = "group"
    function    = "fcn"

class parameter(OrderedDict, object):
    types = parameterTypes()

    FLAG_READONLY = 1<<0
    FLAG_RADIOBUTTONCHOICES = 1<<1
    FLAG_BROWSEPATH = 1<<2

    def __init__(self, name, type, value = None, children = [], choices = [], flags = 0, limits = []):
        super().__init__()
        self.name = name
        self.type = type
        self.flags = flags
        self.choices = choices
        self._setterCallbackList = []
        self.limits = limits
        if choices != []:
            if value not in choices: self._value = choices[0]
            else: self.value = value
        else:
            self.value = value
        for child in children: self.appendChild(child)

    #value getter/setter
    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, newVal):
        if self.type == parameter.types.int: newVal = int(newVal)
        if self.type == parameter.types.float: newVal = float(newVal)
        if len(self.limits)==2:
            if newVal<self.limits[0]: newVal = self.limits[0] 
            if newVal>self.limits[1]: newVal = self.limits[1] 
        self._value = newVal
        self.valueChanged()

    def setValue(self, value):
        #we need this function, so that we can set the value using lambdas
        self.value = value

    def connect(self, fcn):
        #connect given fcn to the setter callbacks
        self._setterCallbackList.append(fcn)

    def appendChild(self, child):
        if self.type == parameter.types.group:
            self[child.name] = child
            child.connect(self.valueChanged)

    def getValues(self):
        if self.type == parameter.types.group:
            ret = OrderedDict()
            for k,v in self.items():
                ret[k] = v.getValues()
            return ret
        else:
            return self.value

    def valueChanged(self, val = None):
        #call all functions in the setter callback list
        for fcn in self._setterCallbackList: fcn(self._value)

class QtTreeWidgetParameter(QtWidgets.QTreeWidgetItem):
    """
    the purpose of this class and all derived classesis to seperate QT-gui logic from the underlying parameter logic,
    just in case we ever switch back to model/view based parameter trees....

    The base class defines common functions and can only be used to build parameter groups.
    All other parameter types use derived classes
    """
    def __init__(self, param, tree):
        super().__init__()
        self.setData(0, DATA_PARAM, param)
        self.setData(0, DATA_TREE, tree)
        self.setText(0, param.name)
        tree._paramWidgetList.append(self)

    def setupWidget(self):
        font = QtGui.QFont()
        font.setBold(True)
        self.setFont(0,font)
        param = self.data(0, DATA_PARAM)
        tree = self.data(0, DATA_TREE)
        self.addChildren((paramTree.createItem(x, tree) for x in param.values()))
        #we need this for the minimum size
        W = QtWidgets.QWidget()
        W.setMinimumHeight(20)
        tree.setItemWidget(self, 1, W)

class QtTreeWidgetStringParameter(QtTreeWidgetParameter):
    SUBTYPE_DEFAULT = 0
    SUBTYPE_READONLY = 1
    SUBTYPE_DROPDOWN = 2
    SUBTYPE_RADIOBUTTONS = 3
    SUBTYPE_PATH = 4

    def __init__(self, param, tree):
        super().__init__(param, tree)
        self._editorOpen = [False]

    def setupWidget(self):
        param = self.data(0, DATA_PARAM)
        tree = self.data(0, DATA_TREE)

        if      param.flags & parameter.FLAG_READONLY:                                          self.subtype = QtTreeWidgetStringParameter.SUBTYPE_READONLY
        elif    param.choices != [] and param.flags & parameter.FLAG_RADIOBUTTONCHOICES:        self.subtype = QtTreeWidgetStringParameter.SUBTYPE_RADIOBUTTONS
        elif    param.choices != [] and not (param.flags & parameter.FLAG_RADIOBUTTONCHOICES):  self.subtype = QtTreeWidgetStringParameter.SUBTYPE_DROPDOWN
        elif    (param.flags & parameter.FLAG_BROWSEPATH):                                      self.subtype = QtTreeWidgetStringParameter.SUBTYPE_PATH
        else:                                                                                   self.subtype = QtTreeWidgetStringParameter.SUBTYPE_DEFAULT

        param.connect(self.updateText)

        if      self.subtype == QtTreeWidgetStringParameter.SUBTYPE_READONLY:       W = self._setupReadonlyWidget(param)
        elif    self.subtype == QtTreeWidgetStringParameter.SUBTYPE_RADIOBUTTONS:
            W = self._setupRadioButtonWidget(param)
            self.setTextAlignment(0,QtCore.Qt.AlignTop)
        elif    self.subtype == QtTreeWidgetStringParameter.SUBTYPE_DROPDOWN:       W = self._setupDropdownWidget(param)
        elif    self.subtype == QtTreeWidgetStringParameter.SUBTYPE_DEFAULT or \
                self.subtype == QtTreeWidgetStringParameter.SUBTYPE_PATH:           W = self._setupDefaultWidget(param)

        P = QtGui.QPalette()
        P.setColor(QtGui.QPalette.Active, QtGui.QPalette.Base, QtCore.Qt.transparent)
        P.setColor(QtGui.QPalette.Inactive, QtGui.QPalette.Base, QtCore.Qt.transparent)
        W.setPalette(P)
        W.setMinimumHeight(20)
        
        tree.setItemWidget(self, 1, W)

    def _setupReadonlyWidget(self, param):
        W = QtWidgets.QLabel()
        W.setText(param.value)
        return W

    def _setupRadioButtonWidget(self, param):
        W = QtWidgets.QWidget()
        L = QtWidgets.QVBoxLayout()
        L.setSpacing(0)
        L.setContentsMargins(5,0,5,0)
        W.setLayout(L)
        def selectionChangedFcn(button, choice, param):
            if button.isChecked(): param.setValue(choice)
        for choice in param.choices:
            RB = QtWidgets.QRadioButton(W)
            if param.value == choice: RB.setChecked(True)
            RB.setText(choice)
            p = partial(selectionChangedFcn, RB, choice, param)
            RB.toggled.connect(p)
            L.addWidget(RB)
        return W

    def _setupDropdownWidget(self, param):
        W = QtWidgets.QComboBox()
        W.addItems(param.choices)
        W.setFrame(False)
        W.currentTextChanged.connect(param.setValue)
        return W

    def _setupDefaultWidget(self, param):
        W = QtWidgets.QWidget()
        L = QtWidgets.QHBoxLayout()
        L.setSpacing(0)
        L.setContentsMargins(5,0,5,0)
        W.setLayout(L)
        LE = QtWidgets.QLineEdit()
        LE.setClearButtonEnabled(True)
        LE.setFrame(False)
        P = QtGui.QPalette()
        P.setColor(QtGui.QPalette.Active, QtGui.QPalette.Base, QtCore.Qt.transparent)
        P.setColor(QtGui.QPalette.Inactive, QtGui.QPalette.Base, QtCore.Qt.transparent)
        LE.setPalette(P)
        B = QtWidgets.QPushButton("Browse.." if self.subtype == QtTreeWidgetStringParameter.SUBTYPE_PATH else "Editor ...")
        B.clicked.connect(lambda: self._showTextEditor(LE, param.name))
        W.setText = LE.setText #what you gonna do about it?
        W.setText(param.value)
        LE.textEdited.connect(param.setValue)
        L.addWidget(LE)
        L.addWidget(B)
        return W

    def _showTextEditor(self, correspondingLineEdit, paramName):
        if self._editorOpen[0]: return
        if self.subtype == QtTreeWidgetStringParameter.SUBTYPE_PATH:
            D = BrowseDialog(correspondingLineEdit, self._editorOpen, paramName)
        else:
            D = TextEditDialog(correspondingLineEdit, self._editorOpen, paramName)
        D.exec()

    def updateText(self, value = None):
        param = self.data(0, DATA_PARAM)
        tree = self.data(0, DATA_TREE)

        if      self.subtype == QtTreeWidgetStringParameter.SUBTYPE_READONLY or \
                self.subtype == QtTreeWidgetStringParameter.SUBTYPE_DEFAULT: tree.itemWidget(self, 1).setText(str(param.value))
        elif    self.subtype == QtTreeWidgetStringParameter.SUBTYPE_DROPDOWN: tree.itemWidget(self, 1).setCurrentText(str(param.value))
        elif    self.subtype == QtTreeWidgetStringParameter.SUBTYPE_RADIOBUTTONS:
            children = [tree.itemWidget(self, 1).layout().itemAt(x).widget() for x in range(len(param.choices))]
            for child in children:
                child.setChecked(child.text() == param.value)

class QtTreeWidgetFunctionParameter(QtTreeWidgetParameter):

    def __init__(self, param, tree):
        super().__init__(param, tree)

    def setupWidget(self):
        param = self.data(0, DATA_PARAM)
        tree = self.data(0, DATA_TREE)
        W = QtWidgets.QWidget()
        L = QtWidgets.QHBoxLayout()
        L.setSpacing(0)
        L.setContentsMargins(5,0,5,0)
        W.setLayout(L)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        L.addItem(spacerItem)
        B = QtWidgets.QPushButton(param.value[0])
        B.clicked.connect(param.value[1])
        L.addWidget(B)
        tree.setItemWidget(self, 1, W)

class QtTreeWidgetBoolParameter(QtTreeWidgetParameter):
    SUBTYPE_DEFAULT = 0
    SUBTYPE_READONLY = 1

    def __init__(self, param, tree):
        super().__init__(param, tree)

    def setupWidget(self):
        param = self.data(0, DATA_PARAM)
        tree = self.data(0, DATA_TREE)

        if      param.flags & parameter.FLAG_READONLY:  self.subtype = QtTreeWidgetBoolParameter.SUBTYPE_READONLY
        else:                                           self.subtype = QtTreeWidgetBoolParameter.SUBTYPE_DEFAULT
        param.connect(self.updateText)
        W = QtWidgets.QCheckBox()
        W.setChecked(param.value)
        W.setEnabled(self.subtype !=  QtTreeWidgetBoolParameter.SUBTYPE_READONLY)
        W.setMinimumHeight(20)
        W.toggled.connect(param.setValue)
        tree.setItemWidget(self, 1, W)

    def updateText(self, value = None):
        param = self.data(0, DATA_PARAM)
        tree = self.data(0, DATA_TREE)
        tree.itemWidget(self, 1).setChecked(param.value)

class QtTreeWidgetIntParameter(QtTreeWidgetParameter):
    SUBTYPE_DEFAULT = 0
    SUBTYPE_READONLY = 1
    SUBTYPE_DROPDOWN = 2
    SUBTYPE_RADIOBUTTONS = 3
    SUBTYPE_LIMITED = 4

    def __init__(self, param, tree):
        super().__init__(param, tree)

    def setupWidget(self):
        param = self.data(0, DATA_PARAM)
        tree = self.data(0, DATA_TREE)

        if      param.flags & parameter.FLAG_READONLY:                                          self.subtype = QtTreeWidgetIntParameter.SUBTYPE_READONLY
        elif    param.choices != [] and param.flags & parameter.FLAG_RADIOBUTTONCHOICES:        self.subtype = QtTreeWidgetIntParameter.SUBTYPE_RADIOBUTTONS
        elif    param.choices != [] and not (param.flags & parameter.FLAG_RADIOBUTTONCHOICES):  self.subtype = QtTreeWidgetIntParameter.SUBTYPE_DROPDOWN
        elif    param.limits != []:                                                             self.subtype = QtTreeWidgetIntParameter.SUBTYPE_LIMITED
        else:                                                                                   self.subtype = QtTreeWidgetIntParameter.SUBTYPE_DEFAULT

        param.connect(self.updateText)

        if      self.subtype == QtTreeWidgetIntParameter.SUBTYPE_READONLY:        W = self._setupReadonlyWidget(param)
        elif    self.subtype == QtTreeWidgetIntParameter.SUBTYPE_RADIOBUTTONS:    
            W = self._setupRadioButtonWidget(param)
            self.setTextAlignment(0,QtCore.Qt.AlignTop)
        elif    self.subtype == QtTreeWidgetIntParameter.SUBTYPE_DROPDOWN:        W = self._setupDropdownWidget(param)
        elif    self.subtype == QtTreeWidgetIntParameter.SUBTYPE_LIMITED:         W = self._setupLimitedWidget(param)
        elif    self.subtype == QtTreeWidgetIntParameter.SUBTYPE_DEFAULT:         W = self._setupDefaultWidget(param)

        P = QtGui.QPalette()
        P.setColor(QtGui.QPalette.Active, QtGui.QPalette.Base, QtCore.Qt.transparent)
        P.setColor(QtGui.QPalette.Inactive, QtGui.QPalette.Base, QtCore.Qt.transparent)
        W.setPalette(P)
        W.setMinimumHeight(20)
        
        tree.setItemWidget(self, 1, W)

    def _setupReadonlyWidget(self, param):
        W = QtWidgets.QLabel()
        
        W.setContentsMargins(2,0,0,0)
        W.setValue = lambda x: W.setText(str(x)) #what you gonna do about it?
        W.setValue(param.value)
        return W

    def _setupRadioButtonWidget(self, param):
        W = QtWidgets.QWidget()
        L = QtWidgets.QVBoxLayout()
        L.setSpacing(0)
        L.setContentsMargins(5,0,5,0)
        W.setLayout(L)
        def selectionChangedFcn(button, choice, param):
            if button.isChecked(): param.setValue(choice)
        for choice in param.choices:
            RB = QtWidgets.QRadioButton(W)
            if param.value == choice: RB.setChecked(True)
            RB.setText(str(choice))
            p = partial(selectionChangedFcn, RB, choice, param)
            RB.toggled.connect(p)
            L.addWidget(RB)
        return W

    def _setupDropdownWidget(self, param):
        W = QtWidgets.QComboBox()
        W.addItems((str(x) for x in param.choices))
        W.setFrame(False)
        W.currentTextChanged.connect(lambda x: param.setValue(int(x)))
        return W

    def _setupDefaultWidget(self, param):
        SB = QtWidgets.QSpinBox()
        SB.setFrame(False)
        SB.valueChanged.connect(param.setValue)
        SB.setRange(-(2**31),(2**31)-1)
        P = QtGui.QPalette()
        P.setColor(QtGui.QPalette.Active, QtGui.QPalette.Base, QtCore.Qt.transparent)
        P.setColor(QtGui.QPalette.Inactive, QtGui.QPalette.Base, QtCore.Qt.transparent)
        SB.setPalette(P)
        return SB

    def _setupLimitedWidget(self, param):
        SB = QtWidgets.QSpinBox()
        SB.setFrame(False)
        SB.setRange(-(2**31),(2**31)-1)
        P = QtGui.QPalette()
        P.setColor(QtGui.QPalette.Active, QtGui.QPalette.Base, QtCore.Qt.transparent)
        P.setColor(QtGui.QPalette.Inactive, QtGui.QPalette.Base, QtCore.Qt.transparent)
        SB.setPalette(P)
        S = QtWidgets.QSlider()
        S.setRange(*param.limits)
        S.setOrientation(QtCore.Qt.Horizontal)

        SB.valueChanged.connect(param.setValue)
        SB.valueChanged.connect(S.setValue)
        S.valueChanged.connect(SB.setValue)

        W = QtWidgets.QWidget()
        L = QtWidgets.QHBoxLayout()
        L.setSpacing(0)
        L.setContentsMargins(0,0,5,0)
        W.setLayout(L)
        W.setValue = SB.setValue
        L.addWidget(SB)
        L.addWidget(S)
        return W


    def updateText(self, value = None):
        param = self.data(0, DATA_PARAM)
        tree = self.data(0, DATA_TREE)

        if      self.subtype == QtTreeWidgetIntParameter.SUBTYPE_READONLY or \
                self.subtype == QtTreeWidgetIntParameter.SUBTYPE_DEFAULT or \
                self.subtype == QtTreeWidgetIntParameter.SUBTYPE_LIMITED: tree.itemWidget(self, 1).setValue(param.value)
        elif    self.subtype == QtTreeWidgetIntParameter.SUBTYPE_DROPDOWN: tree.itemWidget(self, 1).setCurrentText(str(param.value))
        elif    self.subtype == QtTreeWidgetIntParameter.SUBTYPE_RADIOBUTTONS:
            children = [tree.itemWidget(self, 1).layout().itemAt(x).widget() for x in range(len(param.choices))]
            for child in children:
                child.setChecked(child.text() == str(param.value))

class QtTreeWidgetFloatParameter(QtTreeWidgetParameter):
    SUBTYPE_DEFAULT = 0
    SUBTYPE_READONLY = 1
    SUBTYPE_DROPDOWN = 2
    SUBTYPE_RADIOBUTTONS = 3
    SUBTYPE_LIMITED = 4

    def __init__(self, param, tree):
        super().__init__(param, tree)

    def setupWidget(self):
        param = self.data(0, DATA_PARAM)
        tree = self.data(0, DATA_TREE)

        if      param.flags & parameter.FLAG_READONLY:                                          self.subtype = QtTreeWidgetFloatParameter.SUBTYPE_READONLY
        elif    param.choices != [] and param.flags & parameter.FLAG_RADIOBUTTONCHOICES:        self.subtype = QtTreeWidgetFloatParameter.SUBTYPE_RADIOBUTTONS
        elif    param.choices != [] and not (param.flags & parameter.FLAG_RADIOBUTTONCHOICES):  self.subtype = QtTreeWidgetFloatParameter.SUBTYPE_DROPDOWN
        elif    param.limits != []:                                                             self.subtype = QtTreeWidgetFloatParameter.SUBTYPE_LIMITED
        else:                                                                                   self.subtype = QtTreeWidgetFloatParameter.SUBTYPE_DEFAULT

        param.connect(self.updateText)

        if      self.subtype == QtTreeWidgetFloatParameter.SUBTYPE_READONLY:        W = self._setupReadonlyWidget(param)
        elif    self.subtype == QtTreeWidgetFloatParameter.SUBTYPE_RADIOBUTTONS:    
            W = self._setupRadioButtonWidget(param)
            self.setTextAlignment(0,QtCore.Qt.AlignTop)
        elif    self.subtype == QtTreeWidgetFloatParameter.SUBTYPE_DROPDOWN:        W = self._setupDropdownWidget(param)
        elif    self.subtype == QtTreeWidgetFloatParameter.SUBTYPE_LIMITED:         W = self._setupLimitedWidget(param)
        elif    self.subtype == QtTreeWidgetFloatParameter.SUBTYPE_DEFAULT:         W = self._setupDefaultWidget(param)

        P = QtGui.QPalette()
        P.setColor(QtGui.QPalette.Active, QtGui.QPalette.Base, QtCore.Qt.transparent)
        P.setColor(QtGui.QPalette.Inactive, QtGui.QPalette.Base, QtCore.Qt.transparent)
        W.setPalette(P)
        W.setMinimumHeight(20)
        
        tree.setItemWidget(self, 1, W)

    def _setupReadonlyWidget(self, param):
        W = QtWidgets.QLabel()
        
        W.setContentsMargins(2,0,0,0)
        W.setValue = lambda x: W.setText(str(x)) #what you gonna do about it?
        W.setValue(param.value)
        return W

    def _setupRadioButtonWidget(self, param):
        W = QtWidgets.QWidget()
        L = QtWidgets.QVBoxLayout()
        L.setSpacing(0)
        L.setContentsMargins(5,0,5,0)
        W.setLayout(L)
        def selectionChangedFcn(button, choice, param):
            if button.isChecked(): param.setValue(choice)
        for choice in param.choices:
            RB = QtWidgets.QRadioButton(W)
            if param.value == choice: RB.setChecked(True)
            RB.setText(str(choice))
            p = partial(selectionChangedFcn, RB, choice, param)
            RB.toggled.connect(p)
            L.addWidget(RB)
        return W

    def _setupDropdownWidget(self, param):
        W = QtWidgets.QComboBox()
        W.addItems((str(x) for x in param.choices))
        W.setFrame(False)
        W.currentTextChanged.connect(lambda x: param.setValue(float(x)))
        return W

    def _setupDefaultWidget(self, param):
        SB = QtWidgets.QDoubleSpinBox()
        SB.setFrame(False)
        SB.valueChanged.connect(param.setValue)
        SB.setRange(-(2**31),(2**31)-1)
        P = QtGui.QPalette()
        P.setColor(QtGui.QPalette.Active, QtGui.QPalette.Base, QtCore.Qt.transparent)
        P.setColor(QtGui.QPalette.Inactive, QtGui.QPalette.Base, QtCore.Qt.transparent)
        SB.setPalette(P)
        return SB

    def _setupLimitedWidget(self, param):
        SB = QtWidgets.QDoubleSpinBox()
        SB.setFrame(False)
        SB.setRange(-1.7976931348623157E308,1.7976931348623157E308)
        P = QtGui.QPalette()
        P.setColor(QtGui.QPalette.Active, QtGui.QPalette.Base, QtCore.Qt.transparent)
        P.setColor(QtGui.QPalette.Inactive, QtGui.QPalette.Base, QtCore.Qt.transparent)
        SB.setPalette(P)
        S = QtWidgets.QSlider()
        S.setRange(*param.limits)
        S.setOrientation(QtCore.Qt.Horizontal)

        SB.valueChanged.connect(param.setValue)
        SB.valueChanged.connect(S.setValue)
        S.valueChanged.connect(SB.setValue)

        W = QtWidgets.QWidget()
        L = QtWidgets.QHBoxLayout()
        L.setSpacing(0)
        L.setContentsMargins(0,0,5,0)
        W.setLayout(L)
        W.setValue = SB.setValue
        L.addWidget(SB)
        L.addWidget(S)
        return W

    def updateText(self, value = None):
        param = self.data(0, DATA_PARAM)
        tree = self.data(0, DATA_TREE)

        if      self.subtype == QtTreeWidgetFloatParameter.SUBTYPE_READONLY or \
                self.subtype == QtTreeWidgetFloatParameter.SUBTYPE_DEFAULT or \
                self.subtype == QtTreeWidgetFloatParameter.SUBTYPE_LIMITED: tree.itemWidget(self, 1).setValue(param.value)
        elif    self.subtype == QtTreeWidgetFloatParameter.SUBTYPE_DROPDOWN: tree.itemWidget(self, 1).setCurrentText(str(param.value))
        elif    self.subtype == QtTreeWidgetFloatParameter.SUBTYPE_RADIOBUTTONS:
            children = [tree.itemWidget(self, 1).layout().itemAt(x).widget() for x in range(len(param.choices))]
            for child in children:
                child.setChecked(child.text() == str(param.value))

class parameterWidget(QtWidgets.QTreeWidget):
    def setParameters(self, params):
        self._paramWidgetList = []
        self._params = params

        self.addTopLevelItems((paramTree.createItem(x, self) for x in params.values()))
        self.setHeaderHidden(True)
        for param in self._paramWidgetList: param.setupWidget()
        self.setHeaderLabels(["Parameter", "Value"])
        
        self.expandAll()
        self.resizeColumnToContents(0)
        self.header().setSectionResizeMode(0,QtWidgets.QHeaderView.ResizeToContents)
        self.header().setSectionResizeMode(1,QtWidgets.QHeaderView.Stretch)
        self.header().setStretchLastSection(False)
        #self.setUniformRowHeights(True)
        self.setAlternatingRowColors(True)

# simple text editors =============================================================================
class TextEditDialog(QtWidgets.QDialog):
    def __init__(self, lineEdit, mutex, name):
        super().__init__()
        self.line = lineEdit
        self.mutex = mutex #not really a mutex, just a blockin var
        self.mutex[0] = True
        self.setWindowTitle("Text editor for '{}'".format(name))
        layout = QtWidgets.QHBoxLayout()
        editor = QtWidgets.QTextEdit()
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(editor)
        self.setLayout(layout)
        lineEdit.setEnabled(False)
        editor.setText(lineEdit.text())
        editor.textChanged.connect(lambda:lineEdit.setText(editor.toPlainText()))

    def closeEvent(self, event):
        self.mutex[0] = False
        self.line.setEnabled(True)

class BrowseDialog(QtWidgets.QDialog):
    def __init__(self, lineEdit, mutex, name):
        super().__init__()
        self.line = lineEdit
        self.mutex = mutex #not really a mutex, just a blockin var
        self.mutex[0] = True
        self.setWindowTitle("File/Folder path editor for '{}'".format(name))
        layout = QtWidgets.QVBoxLayout()
        self.editor = QtWidgets.QTextEdit()
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self.editor)
        Hlayout = QtWidgets.QHBoxLayout()
        B1 = QtWidgets.QPushButton("Browse files (read)")
        B1.clicked.connect(lambda :self.getPath(1))
        Hlayout.addWidget(B1)

        B2 = QtWidgets.QPushButton("Browse files (write)")
        B2.clicked.connect(lambda :self.getPath(2))
        Hlayout.addWidget(B2)

        B3 = QtWidgets.QPushButton("Browse directories")
        B3.clicked.connect(lambda :self.getPath(3))
        Hlayout.addWidget(B3)

        layout.addLayout(Hlayout)
        self.setLayout(layout)
        lineEdit.setEnabled(False)
        self.editor.setText(lineEdit.text())
        self.editor.textChanged.connect(lambda:lineEdit.setText(self.editor.toPlainText()))

    def getPath(self, type):
        if type == 1:   tmp = QtWidgets.QFileDialog.getOpenFileName()[0]
        elif type == 2: tmp = QtWidgets.QFileDialog.getSaveFileName()[0]
        elif type == 3: tmp = QtWidgets.QFileDialog.getExistingDirectory()
        self.editor.append(tmp)

    def closeEvent(self, event):
        self.mutex[0] = False
        self.line.setEnabled(True)

# gui classes & functions =========================================================================
class quickdoxyGUI(QtWidgets.QMainWindow):
    def __init__(self, cfg, app):
        super().__init__()
        self.cfg = cfg
        from  frontendUI import Ui_quickdoxy #this is to avoid circular dependencies
        self.ui = Ui_quickdoxy()
        self.ui.setupUi(self)
        self.setupLogging()
        self.ui.actionDoc.triggered.connect(self.showDocu)
        self.ui.actionAbout.triggered.connect(self.showAbout)
        self.dataManager = DataManager(self.logger)
        self._app = app

    def showDocu(self):
        HF = QtCore.QFile(":/docupdf")
        tmpfile = op.join(gettempdir(),"quickdoxydocu.pdf")
        try:
            os.chmod(tmpfile, 0o777)
            os.remove(tmpfile)
        except FileNotFoundError: pass
        HF.copy(tmpfile)
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(tmpfile))

    def showAbout(self):
        File        = QtCore.QFile(":/about")
        File.open(QtCore.QFile.ReadOnly)
        lines = str(File.readAll(),'utf-8').split("\n")
        File.close()
        self.logger.info(" ABOUT | "+" | ".join((x.strip().replace("\t"," ") for x in lines)))

    def setupLogging(self):
        self.logger = logging_getLogger()
        self.logger.setLevel(DEBUG)
        self.logger.debug("started logging to stdout")
        
        self.ui.logging = QtWidgets.QTextEdit()
        self.ui.logging.setReadOnly(True)
        self.ui.logging.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui.logging.customContextMenuRequested.connect(lambda x:logging_LogContextMenu(self.ui.logging, x))

        self.ui.loggingDock = QtWidgets.QDockWidget(self)
        self.ui.loggingDock.hide()
        self.ui.loggingDock.setWidget(self.ui.logging)
        self.ui.loggingDock.setFloating(True)
        self.ui.loggingDock.resize(800,200)
        self.ui.loggingDock.setWindowTitle("quickdoxy log")
        self.ui.actionToggle_log.triggered.connect(lambda: self.ui.loggingDock.setVisible(self.ui.loggingDock.isHidden()))

        logging_log2statusbar(self.ui.statusBar, self.logger, self.logger._fmt )
        logging_log2TextEdit(self.ui.logging, self.logger, self.logger._fmt )
        logging_log2Textfile(self.cfg["logfile"], self.logger, self.logger._fmt )        

    def run(self):
        self.show()
        sys.exit(self._app.exec_())

def buildGUI(cfg):

    GUIapp      = QtWidgets.QApplication(sys.argv)
    win         = quickdoxyGUI(cfg, GUIapp)
    return win

def EXAMPLES(window):
    window.ui.verticalLayout.setContentsMargins(0, 0, 0, 0)
    window.ui.verticalLayout.setSpacing(0)
    window.ui.verticalLayout.setObjectName("verticalLayout")
    window.ui.params = paramTree.createExampleWidget()
    window.ui.params.setObjectName("params")
    window.ui.params.setAlternatingRowColors(True)
    window.ui.verticalLayout.addWidget(window.ui.params)

def buildEXAMPLEGUI():
    win = buildGUI()
    EXAMPLES(win)
    return win
