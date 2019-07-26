import subprocess
import os
import shutil
from lxml import etree

def main():
    if os.path.exists("cli_help.txt"): os.remove("cli_help.txt")
    subprocess.call(["python", "../__main__.py", "--help", ">>", "cli_help.txt"], shell = True)
    
    IN = open("cli_help.txt","r").read()
    OUT = IN.replace("__main__", "quickdoxy")
    open("cli_help.txt","w").write(OUT)

    makefile = etree.parse("docu.tco").getroot()
    OP = [x for x in makefile.iter("outputProfile")][0]

    PPs = OP.find("preProcessors")
    for PP in PPs.iter("processor"):
        path = PP.attrib["path"]
        args = PP.attrib["arguments"]
        subprocess.call([path, args], shell = True)

    TEXCMD = OP.find("texCommand")
    path = TEXCMD.attrib["path"]
    args = TEXCMD.attrib["arguments"].replace("&quot;",'"').replace("%wm", "docu.tex").split(" ")
    print(" ".join([path]+args))
    subprocess.call([path] + args, shell = True)

    BIBCMD = OP.find("bibTexCommand")
    path = BIBCMD.attrib["path"]
    args = BIBCMD.attrib["arguments"].replace("&quot;",'"').replace("%tm", "docu").split(" ")
    print(" ".join([path]+args))
    subprocess.call([path] + args, shell = True)

    IDXCMD = OP.find("makeIndexCommand")
    path = IDXCMD.attrib["path"]
    args = IDXCMD.attrib["arguments"].replace("&quot;",'"').replace("%tm", "docu").split(" ")
    print(" ".join([path]+args))
    subprocess.call([path] + args, shell = True)

    PPs = OP.find("postProcessors")
    for PP in PPs.iter("processor"):
        path = PP.attrib["path"]
        args = PP.attrib["arguments"]
        subprocess.call([path, args], shell = True)

    if os.path.exists("cli_help.txt"): shutil.copy("out/docu.pdf", "../docu.pdf")

if __name__ == "__main__":
    main()