import subprocess

subprocess.call(["pyrcc5 ", "frontend.qrc", "-o", "frontendRC.py"])
subprocess.call(["pyuic5 ", "frontend.ui", "--resource-suffix", "RC", "-o", "frontendUI.py"])