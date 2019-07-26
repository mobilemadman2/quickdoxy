from backend import VERSION
from datetime import datetime
import subprocess
from lxml import etree
from docu.make import main as mkdocu
import os
from PIL import Image
import re
import sys
import os.path as op
import string

def main():
    if len(sys.argv)>1 and bool(sys.argv[1]): makeAbout()
    makeShortcutList()
    #makeAnnotatedGraphics()
    makeLaTeX()

def makeAbout():
    aboutlinesIN = open("docu/about.info","r").readlines()
    BuildNo = int(aboutlinesIN[1].split(":")[-1]) + 1
    Version = VERSION
    date    = datetime.strftime(datetime.now(),"%Y-%m-%d")                  
    open("docu/about.info","w").write("Version:\t{}\nBuild #:\t{}\nBuild date:\t{}".format(Version,BuildNo,date))

def makeShortcutList():
    UIfile = etree.parse("frontend.ui")
    QRCfile = etree.parse("frontend.qrc")
    UserActions = UIfile.iter("action")
    UserActionsForLatex = []

    for action in UserActions:
        actionName = ""
        names = action.xpath(".//property[@name = 'text']")
        for name in names: actionName = re.sub("([^a-zA-Z]|^)[0-9]","[0-9]",name[0].text)

        actionShortcut = ""
        shortcuts = action.xpath(".//property[@name = 'shortcut']")
        for shortcut in shortcuts: actionShortcut = re.sub("([^a-zA-Z]|^)[0-9]","[0-9]",shortcut[0].text)

        actionTooltip = actionName
        tooltips = action.xpath(".//property[@name = 'toolTip']")
        for tooltip in tooltips: actionTooltip = re.sub("([^a-zA-Z]|^)[0-9]","[0-9]",tooltip[0].text)

        actionIcon = ""
        icons = action.xpath(".//property/iconset")
        for icon in icons: 
            set = icon.attrib["resource"]
            file = icon[0].text
            actionIcon = file

        if actionIcon != "":
            #find icon in qrc file
            actionIcon = actionIcon.replace(":/","")
            path = QRCfile.xpath("//file[@alias='{}']".format(actionIcon))[0].text
            actionIcon = path
        
        if len(UserActionsForLatex)== 0 or actionName not in [x[0] for x in UserActionsForLatex]:
            UserActionsForLatex.append([actionName, actionShortcut, actionTooltip, actionIcon])
    UserActionsForLatex.sort(key=lambda x:x[0])

    lines = []

    lines.append(r"\begin{flushleft}\tiny\begin{longtabu} to \textwidth {|X[1,c,m]|X[8,l,m]|X[3,c,m]|X[12,c,m]|}")
    lines.append(r"\caption{quickdoxy shortcuts}\label{tab:shortcuts}\endfirsthead")
    lines.append(r"\caption*{Table \ref{tab:shortcuts} (continued)}\endhead")
    lines.append(r"\hline")
    lines.append(r"&\textbf{Name}&\textbf{Shortcut}&\textbf{Description}\\")
    lines.append(r"\hline")
    for action in UserActionsForLatex:
        if action[1] != "":
            line = "&".join(action[:-1])+r"\\"
            pic = "\\tikz[baseline=-0.1cm]{{\\node at (0,0) {{\\includegraphics[height=0.25cm]{{{}}}}}}}&".format("../"+action[-1]) if action[-1] != "" else "&"
            line = pic+line.replace("_",r"\_")
            lines.append(line)
            lines.append(r"\hline")
    lines.append(r"\end{longtabu}\end{flushleft}")

    open("docu/shortcutTable.tex","w").write("\n".join(lines))

def makeAnnotatedGraphics():
    lines = []
    xml = etree.parse("includes/annotatedGraphics.xml")
    lines.append(r"\documentclass[10pt,a5paper,english,hidelinks]{article}")
    lines.append(r"\usepackage{graphicx}")
    lines.append(r"\usepackage{capt-of}")
    lines.append(r"\usepackage{tikz}")
    lines.append(r"\begin{document}")
    for figure in xml.iter("figure"):
        lines.extend(makeAnnotatedGraphic(figure))
    lines.append(r"\end{document}")
    open("docu/annotatedgraphics.tex","w").write("\n".join(lines))

def makeAnnotatedGraphic(srcxml):
    tagname = srcxml.find("tagname").text
    filename = srcxml.find("file").text
    figurename = srcxml.find("figurename").text
    figurepath = op.abspath(op.join("includes", filename)).replace("\\","/")
    width, height = Image.open(figurepath).size
    pixelsize = 1/width
    lines = []
    lines.append(r"%<*{}>".format(tagname))
    lines.append(r"\begin{center}")
    lines.append(r"\captionof{{figure}}{{{}}}".format(figurename))
    lines.append(r"\begin{{tikzpicture}}[x={0}\textwidth, y=-{0}\textwidth]".format(pixelsize))
    lines.append(r"\node at (0,0) {{ \includegraphics[width=\textwidth]{{{}}} }};".format(figurepath))
    lines.append(r"\begin{{scope}}[shift={{(-{},-{})}}]".format(width/2, height/2))

    for idx,label in enumerate(srcxml.iter("label")):
        letter = string.ascii_uppercase[idx]
        X = [float(x) for x in label.find("X").text.split(";")]
        Y = [float(y) for y in label.find("Y").text.split(";")]
        if len(X) == 1:
            lines.append(r"\node[draw, line width = .025cm, fill=gray!55, inner sep = .075cm] at ({},{}) {{\tiny {}}};".format(X[0],Y[0],letter))
        elif len(X) == 2:
            lines.append(r"\draw[line width = .025cm] ({},{}) rectangle ({},{});".format(X[0],Y[0],X[0]+X[1],Y[0]+Y[1],letter))
            lines.append(r"\node[draw, line width = .025cm, fill=gray!55, inner sep = .075cm] at ({},{}) {{\tiny {}}};".format(X[0],Y[0],letter))


    lines.append(r"\end{scope}")
    lines.append(r"\end{tikzpicture}")

    lines.append(r"\begin{flushleft}\tiny\begin{longtabu} to \textwidth {|X[1,c,m]|X[9,l,m]|}")
    lines.append(r"\caption{{Marked items in {0}}}\label{{tab:{0}_items}}\endfirsthead".format(figurename))
    lines.append(r"\caption*{{Table \ref{{tab:{0}_items}} (continued)}}\endhead".format(figurename))
    lines.append(r"\hline")
    lines.append(r"\textbf{Label}&\textbf{Description}\\")
    lines.append(r"\hline")
    for idx,label in enumerate(srcxml.iter("label")):
        desc = label.find("description").text.replace("_", "\\_").replace("&", "\\&")
        letter = string.ascii_uppercase[idx]
        lines.append(r"{0}&{1}\\".format(letter,desc,figurename))
        lines.append(r"\hline")
    lines.append(r"\end{longtabu}\end{flushleft}")

    lines.append(r"\end{center}")
    lines.append(r"%</{}>".format(tagname))
    return lines
    
def makeLaTeX():
    os.chdir("docu")
    mkdocu()

if __name__ == "__main__": main()