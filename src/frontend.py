# -*- coding: utf-8 -*-

#All project-specific changes should be made in frontend.py, backend.py and main.py,
#while frontend_subclasses.py and backend_subclasses.py should not be modified.
#this way, future updates to the application framework can be applied to existing projects
#by simply exchanging all files but frontend.py, backend.py and main.py in the project (and project-specific resources)

import frontend_subclasses as fs
import backend_subclasses as bs
import backend as b
from  PyQt5.QtCore import QTimer, pyqtSignal, QObject
from PyQt5.QtWidgets import QApplication
import sys
from logging import DEBUG

def buildGUI(cfg):
    win = fs.buildGUI(cfg)

    win.permanentsettings = bs.PermanentSettings("HDRD", "quickdoxy")
    dppath = fs.parameter(name = 'DP path', type = fs.parameter.types.str, value = win.permanentsettings.getValue("doxygenportablepath", type=str) , flags = fs.parameter.FLAG_BROWSEPATH)
    dppath.connect(lambda x: win.permanentsettings.setValue("doxygenportablepath",x))

    params = fs.parameter("params", type = fs.parameter.types.group, children = [
        fs.parameter(name = "Doxygen portable (DP) config", type = fs.parameter.types.group, children = [
            dppath,
            fs.parameter(name = 'Extract DP to path',  type = fs.parameter.types.function, value = ("Extract", lambda: win.dataManager.storeData("", dppath.value, True))),
            ]),
        fs.parameter(name = "Input", type = fs.parameter.types.group, children = 
            [
            fs.parameter(name = 'Input files and directories', type = fs.parameter.types.str, value = win.cfg["input"], flags = fs.parameter.FLAG_BROWSEPATH),
            ]),
        fs.parameter(name = "Output", type = fs.parameter.types.group, children = 
            [
            fs.parameter(name = 'Output directory',                type = fs.parameter.types.str, value = win.cfg["output"], flags = fs.parameter.FLAG_BROWSEPATH),
            fs.parameter(name = 'Open HTML output after creation', type = fs.parameter.types.bool, value = True),
            ])
    ])
    win.ui.paramTree.setParameters(params)
    win.ui.runbutton.clicked.connect(win.ui.actionRunDoxygen.trigger)
    win.ui.actionRunDoxygen.triggered.connect(lambda: runDoxygen(params.getValues(),win))
    return win

def runDoxygen(params, win):
    doxypath = params['Doxygen portable (DP) config']['DP path']
    inputs = params['Input']['Input files and directories']
    outputs = params['Output']['Output directory']
    showResult = params['Output']['Open HTML output after creation']
    b.runDoxygen(win, doxypath, inputs, outputs, showResult, win.logger)

class quickdoxyCLI(QObject):
    done = pyqtSignal()

    def __init__(self, app):
        super().__init__()
        self._app = app

    def prepare(self, doxypath, input, output, showResult, logger):
        self.doxypath = doxypath
        self.input = input
        self.output = output
        self.showResult = showResult
        self.logger = logger

    def runDoxygen(self):
        b.runDoxygen(self, self.doxypath , self.input, self.output, self.showResult, self.logger, nomultithread = True)
        self.done.emit()

    def run(self):
        sys.exit(self._app.exec_())



def buildCLI(cfg):
    logger = bs.logging_getLogger()
    logger.setLevel(DEBUG)
    logger.debug("started logging to stdout")
    permanentsettings = fs.PermanentSettings("HDRD", "quickdoxy")
    doxypath = permanentsettings.getValue("doxygenportablepath", type=str)
    GUIapp      = QApplication(sys.argv)
    cli         = quickdoxyCLI(GUIapp)
    cli.prepare(doxypath, cfg["input"], cfg["output"], True, logger)
    cli.done.connect(GUIapp.quit)
    QTimer.singleShot(0, cli.runDoxygen)
    return cli