# -*- coding: utf-8 -*-

#All project-specific changes should be made in frontend.py, backend.py and main.py,
#while frontend_subclasses.py and backend_subclasses.py should not be modified.abs
#this way, future updates to the application framework can be applied to existing projects
#by exchanging all files but frontend.py, backend.py and main.py in the project (and project-specific resources)

VERSION = "2018a"   #The backed.py file NEEDS! to define this variable in order for the autobuild process to work!

import os.path as op
import os
import webbrowser
import backend_subclasses as bs
from PyQt5.QtCore import QThread, QObject, pyqtSignal

def runDoxygen(parent, doxypath, inputs, outputs, showResult, logger = None, nomultithread = False):

    #sanitize/check parameters
    if not op.isfile(op.join(doxypath, "doxyhome", "doxy.bat")):
        if logger is not None: logger.error("The specified doxygen portable path is invalid. Please re-extract doxygen or select a valid path.")
        return

    inputs = inputs.replace("\n", ";")
    inputs = [x.strip() for x in inputs.split(";")]
    inputs = [x for x in inputs if x != ""]
    for x in inputs:
        if not op.exists(x):
            if logger is not None: logger.error("Input '%s' does not exist.", x)
            return
    input = " ".join(inputs)
    
    outputs = outputs.replace("\n", ";")
    outputs = [x.strip() for x in outputs.split(";")]
    if len(outputs)>1:
        if logger is not None: logger.error("More than one output path specified.", x)
        return
    outputfolder = outputs[0]

    if outputfolder == "":
        if logger is not None: logger.error("No output path specified.")
        return

    if not op.isdir(outputfolder):
        os.makedirs(outputfolder, exist_ok=True)
        if logger is not None: logger.info("created output directory %s", op.abspath(outputfolder))

    #run doxygen
    cfgIN       =   open(op.join(doxypath, "doxyhome", "Doxyfile"), 'r').readlines()
    cfgOUT      =   []

    for line in cfgIN:

        if line.startswith("OUTPUT_DIRECTORY       = "):
            line = "OUTPUT_DIRECTORY       = " + outputfolder + "\n"

        if line.startswith("PROJECT_NAME           = "):
            line = "PROJECT_NAME           = QUICKDOXY\n"

        if line.startswith("INPUT                  = "):
            line = "INPUT                  = " +input +"\n"

        if line.startswith("DOT_PATH               = "):
            line = "DOT_PATH               = " +op.join(doxypath, "doxybin", "GraphvizPortable", "App", "graphviz", "bin", "dot.exe\n")
            
        cfgOUT.append(line)
        
    open(op.join(doxypath, "doxyhome", "Doxyfile"), 'w').writelines(cfgOUT)

    parent._doxyworker = doxyworker(logger)
    parent._doxyworker.prepare("starting background worker for doxygen...", op.join(doxypath, 'doxybin', 'doxygen', 'bin', 'doxygen'), [op.join(doxypath, 'doxyhome', 'Doxyfile')])
    if showResult: parent._doxyworker.done.connect(lambda: showHTML('file:///'+op.join(op.abspath(outputfolder),'html','index.html'), logger))

    if not nomultithread:
        parent._doxythread = QThread(parent)
        parent._doxyworker.moveToThread(parent._doxythread)
        parent._doxythread.started.connect(parent._doxyworker.run)
        parent._doxyworker.done.connect(parent._doxythread.quit)

        parent._doxythread.start()
    else:
        parent._doxyworker.run()

def showHTML(url, logger = None):
    url = url.replace("\\","/")
    if logger is not None: logger.info("opening %s", url)
    webbrowser.open(url)

class doxyworker(QObject):
    done = pyqtSignal()
    def __init__(self, logger):
        super().__init__()
        self.logger = logger
        self.proc = bs.logging_getLoggedQtProcess(self, logger)

    def prepare(self, desc, cmd, args):
        self.desc = desc
        self.cmd = cmd
        self.args = args
    
    def run(self):
        self.proc.start(self.desc, self.cmd , self.args)
        self.done.emit()

    