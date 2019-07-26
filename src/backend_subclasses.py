from logging import *
from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5 import QtGui
import os.path as op
import os
from shutil import copy, rmtree
from distutils.dir_util import copy_tree
import sys
import glob
import zipfile
from tempfile import gettempdir
from time import time

CONSOLE = INFO+1 
addLevelName(CONSOLE, "CONSOLE")
def console(self, message, *args, **kws):
    if self.isEnabledFor(CONSOLE):
        self._log(CONSOLE, message, args, **kws) 
Logger.console = console

def logging_getLogger():
    logger = getLogger("quickdoxy")
    logger._fmt = Formatter('%(relativeCreated)09d | %(levelname)s | %(message)s',"%Y-%m-%d %H:%M:%S")
    logHandler = StreamHandler()
    logHandler.setFormatter(logger._fmt)
    logger.addHandler(logHandler)
    return logger

def logging_log2statusbar(statusbar, logger, formatter):
    QtHandler = _QtLog2StatusBarHandler()
    QtHandler.setFormatter(formatter)
    QtHandler.sig.connect(lambda x: statusbar.showMessage(x, 0))
    logger.addHandler(QtHandler)
    logger.debug("started logging into statusbar")

def logging_log2Textfile(filename, logger, formatter):
    if filename is not None:
        fileHandler = FileHandler(filename)
        fileHandler.setFormatter(formatter)
        logger.addHandler(fileHandler)
        logger.debug("started logging into %s", op.abspath(filename))

def logging_log2TextEdit(widget, logger, formatter):
    QtHandler = _QtLog2TextEditHandler()
    QtHandler.setFormatter(formatter)
    QtHandler.sig.connect(widget.append)
    logger.addHandler(QtHandler)
    logger.debug("started logging into text widget")

def logging_LogContextMenu(widget, pos):
    menu = QtWidgets.QMenu()
    clearAction = QtWidgets.QAction("clear",widget)
    clearAction.triggered.connect(widget.clear)
    saveAction = QtWidgets.QAction("save to file",widget)
    saveAction.triggered.connect(lambda: logging_savelog(widget))
    menu.addAction(clearAction)
    menu.addAction(saveAction)
    menu.exec(widget.viewport().mapToGlobal(pos))

def logging_savelog(widget):
    filename = QtWidgets.QFileDialog.getSaveFileName(None, "Save log to ...", "","*.*")
    if filename[0] != "": open(filename[0],"w").write(widget.toPlainText())

def logging_getLoggedQtProcess(parent, logger):
    
    P = _loggedProcess(parent,logger)
    P.readyRead.connect(P._logConsoleOutput)
    return P


class _QtLog2StatusBarHandler(QtCore.QObject,StreamHandler):
    sig = QtCore.pyqtSignal(str)
    def __init__(self):
        super().__init__()

    def emit(self, logRecord):
        msg = self.format(logRecord)
        self.sig.emit(msg)

class _QtLog2TextEditHandler(QtCore.QObject,StreamHandler):
    sig = QtCore.pyqtSignal(str)
    def __init__(self):
        super().__init__()

    def emit(self, logRecord):
        msg = self.format(logRecord)
        self.sig.emit(msg)

class _loggedProcess(QtCore.QProcess):
    def __init__(self, parent, logger, *args, **kwargs):
        super().__init__(parent,*args,**kwargs)
        self.logger = logger
        self.textbuffer = ""
        self.errbuffer = ""

    def _logConsoleOutput(self):
        txt = bytes(self.readAll()).decode("cp437")
        if txt.endswith("\r\n"):
            self.textbuffer+=txt.strip("\r\n")

            for line in self.textbuffer.split("\r\n"):
                self.logger.console(line); 

            self.textbuffer = ""
        elif txt.startswith("\r\n"):
            if self.textbuffer != "":
                
                for line in self.textbuffer.split("\r\n"):
                    self.logger.console(line); 

            self.textbuffer += txt.strip("\r\n")
        else: 
            self.textbuffer += txt

    def start(self, CMDdescription,*args, **kwargs):
        if CMDdescription is not None:
            self.logger.console(CMDdescription)
        super().start(*args, **kwargs)
        self.waitForFinished()
        if self.exitCode != 0:
            txt = bytes(self.readAllStandardError()).decode("cp437")
            if txt.endswith("\r\n"):
                self.errbuffer+=txt.strip("\r\n")

                for line in self.errbuffer.split("\r\n"):
                    self.logger.error(line); 

                self.errbuffer = ""
            elif txt.startswith("\r\n"):
                if self.errbuffer != "":
                    
                    for line in self.errbuffer.split("\r\n"):
                        self.logger.error(line); 

                self.errbuffer += txt.strip("\r\n")
            else: 
                self.errbuffer += txt

class DataManager():
    def __init__(self, logger):
        dataprefix = "data"
        basepath = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        fullpath = op.join(basepath,dataprefix).replace("\\","/")
        self.logger = logger
        names = []
        if op.isfile(basepath):
            with zipfile.ZipFile(basepath) as archive:
                for name in archive.namelist():
                    #in this case, the relevant stuff is located under /data/...
                    name = name.replace("\\","/")
                    if name.startswith(dataprefix+"/"): names.append(name)
        else:
            for name in glob.glob(fullpath+"/**/*.*",recursive = True): 
                names.append(name.replace("\\","/"))
        if not op.isfile(basepath): names = [x for x in names if op.isfile(x)]
        names = [x.replace(fullpath+"/", "").replace(dataprefix+"/", "") for x in names]
        dirnames = sorted(list(set([op.dirname(x) for x in names])))
        while True:
            L0 = len(dirnames)
            newDirnames = sorted(list(set([op.dirname(x) for x in dirnames]+dirnames)))
            L1 = len(newDirnames)
            if L0 == L1: break
            dirnames = newDirnames
        self._fileList = names
        self._dirList = dirnames
        self.path = fullpath
        self._basepath = basepath
        self._dataprefix = dataprefix
    
    def getDataPath(self): return self.path
    def getFileList(self, returnHandles = False): return self._fileList
    def getFileContent(self, filepath):
        filepath = filepath.replace("\\", "/")
        if filepath not in self._fileList: return None
        if op.isfile(self._basepath):
            # in this case, we need to access a zip-archive
            with zipfile.ZipFile(self._basepath) as archive:
                return archive.open(self._dataprefix+"/"+filepath)
        else:
            #this is easier: just return the stuff
            return open(op.join(self.path, filepath), "r")
    def storeData(self, srcPath, dstPath, createFolder = False):
        TYPE_FILE = 1
        TYPE_DIR = 2
        type = 0
        nrOfFilesCopied = 0

        if srcPath.replace("\\","/") in self._fileList: type = TYPE_FILE
        elif srcPath.replace("\\","/") in self._dirList: type = TYPE_DIR
        else: 
            self.logger.error("data source '{}' could not be found. No data was copied.".format(srcPath))
            return -1
        self.logger.info("started copying data to {}.".format(dstPath))
        if not op.isfile(self._basepath): dstDir = op.dirname(dstPath)
        else:                             dstDir = dstPath
        if not op.exists(dstDir): os.makedirs(dstDir, exist_ok=True)
        if type == TYPE_FILE:
            if op.isfile(self._basepath):
                # in this case, we need to access a zip-archive
                #in order to do this properly, we need a temp dir...
                with tempWorkingDir("quickdoxy_tmpdir") as tmpdst:
                    with zipfile.ZipFile(self._basepath) as archive:
                        src = op.join(self._dataprefix, srcPath).replace("\\","/")
                        #dst = dstDir
                        dst = tmpdst
                        path = archive.extract(src, dst)
                    #after the file has been copied to tmp/data/whatever, , copy it to the actual target dir
                    copy(path, op.join(dstDir, op.basename(path)))
                    nrOfFilesCopied = 1
            else:
                #this is easier: just return the stuff
                copy(op.join(self.path, srcPath), dstPath)
                nrOfFilesCopied = 1
        elif type == TYPE_DIR:
            if op.isfile(self._basepath):
                # in this case, we need to access a zip-archive
                #in order to do this properly, we need a temp dir...
                with tempWorkingDir("quickdoxy_tmpdir") as tmpdst:
                    paths = []
                    with zipfile.ZipFile(self._basepath) as archive:
                        prefix = op.join(self._dataprefix,srcPath).replace("\\","/")
                        for file in archive.namelist():
                            if file.startswith(prefix):
                                paths.append(archive.extract(file, tmpdst))
                    #after the file has been copied to tmp/data/whatever, , copy it to the actual target dir
                    res = copy_tree(op.join(tmpdst, self._dataprefix), dstDir, update=1, verbose=1)
                    nrOfFilesCopied += len(paths)
            else:
                #this is easier: just return the stuff
                srcDir = op.join(self.path, srcPath)
                res = copy_tree(srcDir, dstPath, update=1)
                for root, dirs, files in os.walk(srcDir):
                    nrOfFilesCopied += 1
        self.logger.info("{} files copied.".format(nrOfFilesCopied))
        return nrOfFilesCopied

class PermanentSettings(QtCore.QSettings):
    def __init__(self, creator, applicationName):
        super().__init__(creator, applicationName)
    def getValue(self, name, type = str):
        val = self.value(name,type = type)
        return val
    def setValue(self, name, value):
        super().setValue(name, value)

class tempWorkingDir():
    def __init__(self, descr):
        self.descr = descr

    def __enter__(self):
        self._abspath  = op.abspath(op.join(gettempdir(), self.descr+str(int(time()))))
        if op.exists(self._abspath): return None
        os.makedirs(self._abspath)
        return self._abspath

    def __exit__(self, type, value, traceback):
        rmtree(self._abspath)
