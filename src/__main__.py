from frontend import *
from backend import *
from backend_subclasses import logging_getLogger,PermanentSettings
import configargparse

cfgObj = configargparse.ArgParser(default_config_files=["quickdoxy.ini"])

cfgObj.add('--logfile', help='logfile name.', default = None)
cfgObj.add_argument('--input', help='input files/directories (seperated by ";")', default = "")
cfgObj.add_argument('--output', help='output directory', default = "")
cfgObj.add_argument('--batchmode', help='pass this flag to skip the gui', action="store_true")

cfg = vars(cfgObj.parse_args())

if cfg["batchmode"]:
    cli = buildCLI(cfg)
    cli.run()
else:
    win = buildGUI(cfg)
    win.run()