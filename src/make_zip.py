import zipfile
import os


def getFileList(path):
    lst = []
    for root, dirs, files in os.walk(path):
        for file in files:
            lst.append(os.path.join(root, file))
    return lst

zip = zipfile.ZipFile("quickdoxy.zip", "w")
files = [
"__main__.py",
"frontend.py", 
"frontend_subclasses.py", 
"frontendUI.py", 
"frontendRC.py",
"backend.py",
"backend_subclasses.py",
]
dirs = [
"data"
]
for file in files:
    zip.write(file, os.path.basename(file), zipfile.ZIP_DEFLATED)
for dir in dirs:
    for file in getFileList(dir):
        zip.write(os.path.abspath(file), file, zipfile.ZIP_DEFLATED)
zip.close()

#not strictly zip-related: add all stuff in all data dirs to the "datas" list 
#of the pyinstaller-spec:

dataList = []
for dir in dirs:
    for file in getFileList(dir):
        file = file.replace("\\","/")
        dataList.append((file, os.path.dirname(file)))
IN = open("__main__.spec","r").read()
OUT = IN.replace("datas=[]", "datas="+str(dataList))
open("__main__.spec","w").write(OUT)