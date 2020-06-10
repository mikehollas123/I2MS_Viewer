from appJar import gui
import os
import pickle as pkl
import numpy as np
from psims.mzml import MzMLWriter
import webbrowser
from pyteomics import mzml

# Global Variables to store spectral data
X_mem = []
Y_mem = []
ave_noise_mem = 1
Xscalar_mem = 1
XFilter = (1,0)
YFilter = 1
loaded_file =""
progress = 0




def CreateI2MS(data, file):
    if type(data) is tuple:
        with open(str(file), "wb") as pklout:
            print(len(data[0]))
            pkl.dump(data, pklout)
            return
    lines = data.split("\n")

    Xscalar = float(lines[1].split(",")[0]) - float(lines[0].split(",")[0])
    XY = [(float(lines[i].split(",")[0]) / Xscalar, int(lines[i].split(",")[1])) for i in range(len(lines)) if
          int(lines[i].split(",")[1]) > 0]

    X, Y = ([int(XY[x][0]) for x in range(len(XY))], [int(XY[x][1]) for x in range(len(XY))])
    ave_noise = np.average([float(XY[j][1]) for j in range(len(XY)) if int(XY[j][1]) <= 10])

    with open(str(file), "wb") as pklout:
        pkl.dump((X, Y, ave_noise, Xscalar), pklout)


def CreateMZML(data, file):
    if type(data) is tuple:
        X, Y, ave_noise, Xscalar = data
        X = [X[i] * Xscalar for i in range(len(X))]
    else:
        lines = data.split("\n")
        XY = [(float(lines[i].split(",")[0]), int(lines[i].split(",")[1])) for i in range(len(lines)) if
              int(lines[i].split(",")[1]) > 0]
        X, Y = ([int(XY[x][0]) for x in range(len(XY))], [int(XY[x][1]) for x in range(len(XY))])
        XY = [(float(lines[i].split(",")[0]), int(lines[i].split(",")[1])) for i in range(len(lines)) if
              int(lines[i].split(",")[1]) > 0]
        X, Y = ([int(XY[x][0]) for x in range(len(XY))], [int(XY[x][1]) for x in range(len(XY))])

    writer = MzMLWriter(file)
    with writer:
        writer.controlled_vocabularies()
        writer.file_description(["I2MS Spectrum"])
        writer.software_list([{
            "id": "I2MS to mzML",
            "veresion": "0.1.1", "params": ["python-psims"]}
        ])
        source = writer.Source(1, ["electrospray ionization", "electrospray inlet"])
        analyzer = writer.Analyzer(2, [
            "fourier transform ion cyclotron resonance mass spectrometer"
        ])
        detector = writer.Detector(3, ["inductive detector"])
        config = writer.InstrumentConfiguration(id="IC1", component_list=[source, analyzer, detector],
                                                params=["LTQ-FT"])
        writer.instrument_configuration_list([config])

        methods = []
        methods.append(
            writer.ProcessingMethod(order=1, software_reference="I2MS to mzML",
                                    params=["Removal of 0 intesity peaks", "Conversion to mzML"])
        )
        processing = writer.DataProcessing(methods, id='DP1')
        writer.data_processing_list([processing])
        with writer.run(id=1, instrument_configuration='IC1'):
            with writer.spectrum_list(count=1):
                writer.write_spectrum(
                    np.array(X), np.array(Y), id=str(1), centroided=True,
                    scan_start_time=1, scan_window_list=[(0, 500000.0)],
                    params=[{"ms levels": 1}, {"total ion current": sum(Y)}])
    writer.close()


"""
Button control for Add from Clipboard window
"""
def clipboardwin(button):


    if button == "add from clipboard":
        app.setTextArea("txtarea1",app.topLevel.clipboard_get() ) # add clipborad to textarea object
    elif button == "Load":
            data = app.getTextArea("txtarea1")
            app.setTextArea("txtarea1", "")
            app.hideSubWindow("clipadd")

            try:
                app.queueFunction(app.showSubWindow, "prog")
                app.threadCallback(openfromclip, load_file, data)

                # Update Status Bar

                if XFilter[1] == 0:
                    X_Filter_status = "Mass Filter (Da): {0}-".format(XFilter[0])
                else:
                    X_Filter_status = "Mass Filter (Da): {0}-{1}".format(XFilter[0], XFilter[1])

                app.setStatusbar("Intensity Filter: {0}".format(YFilter), 0)
                app.setStatusbar(X_Filter_status, 1)
                app.setStatusbarWidth(len("Intensity Filter: 1"), field=0)
                app.setStatusbarWidth(len(X_Filter_status), field=1)
                app.setStatusbar("Loaded file: from Clipboard", 2)
                app.setStatusbarWidth(len("Loaded file: from Clipboard"), field=2)

            except:
                app.errorBox("Parsing Error", "The csv file could no be parsed")



"""
Opens an I2MS file
"""
def openI2MS(filetoopen):
    app.queueFunction(app.setStatusbarWidth, len("Loading file..."), field=2)
    app.queueFunction(app.setStatusbar, "Loading file...", 2)
    with open(filetoopen, "rb") as pklin:
        X, Y, ave_noise, Xscalar =pkl.load(pklin)

        global progress
        progress = 50

        app.registerEvent(updatprogress)
        return (X, Y, ave_noise, Xscalar,filetoopen)


def mZML_reader(filetoopen):
    app.queueFunction(app.setStatusbarWidth, len("Loading file..."), field=2)
    app.queueFunction(app.setStatusbar, "Loading file...", 2)
    data = mzml.read(filetoopen)

    for scan in data:
        if scan['id'] == '1':
            X = scan['m/z array']
            Y = scan['intensity array']
            break

    Xscalar = np.around(min([X[i+1]-X[i] for i in range(0,len(X)-1) if X[i+1]-X[i] != 0.0]),2)
    XY = [(X[i]/Xscalar,Y[i]) for i in range(len(X)) if Y[i] > 0]  # remove 0 values and adjust for scalar

    X, Y = ([int(XY[x][0]) for x in range(len(XY))], [int(XY[x][1]) for x in range(len(XY))])
    ave_noise = np.average([float(XY[j][1]) for j in range(len(XY)) if int(XY[j][1]) <= 10])  # determine average noise
    global progress
    progress = 50
    app.registerEvent(updatprogress)
    return (X, Y, ave_noise, Xscalar, filetoopen)


def openfromclip(data):
    app.queueFunction(app.setStatusbarWidth, len("Loading file..."), field=2)
    app.queueFunction(app.setStatusbar, "Loading file...", 2)

    lines = data.split("\n")
    global progress
    progress = 50

    app.registerEvent(updatprogress)

    Xscalar = float(lines[1].split(",")[0]) - float(
        lines[0].split(",")[0])  # create a scalar so we can store X values as int
    XY = [(float(lines[i].split(",")[0]) / Xscalar, int(lines[i].split(",")[1])) for i in range(len(lines))
          if int(lines[i].split(",")[1]) > 0]  # remove 0 values and adjust for scalar

    X, Y = ([int(XY[x][0]) for x in range(len(XY))], [int(XY[x][1]) for x in range(len(XY))])
    ave_noise = np.average([float(XY[j][1]) for j in range(len(XY)) if int(XY[j][1]) <= 10])  # determine average noise
    return (X, Y, ave_noise, Xscalar, "fromclipboard")
"""
open and parse a csv/txt file of X,Y data
"""
def opencsv(filetoopen):


    app.queueFunction(app.setStatusbarWidth, len("Loading file..."), field=2)
    app.queueFunction(app.setStatusbar, "Loading file...", 2)
    with open(filetoopen, "r") as readfile:
        data = readfile.read()
        lines = data.split("\n")
        global progress
        progress = 50

        app.registerEvent(updatprogress)

        Xscalar = float(lines[1].split(",")[0]) - float(lines[0].split(",")[0]) # create a scalar so we can store X values as int
        XY = [(float(lines[i].split(",")[0]) / Xscalar, int(lines[i].split(",")[1])) for i in range(len(lines))
              if int(lines[i].split(",")[1]) > 0] # remove 0 values and adjust for scalar

        X, Y = ([int(XY[x][0]) for x in range(len(XY))], [int(XY[x][1]) for x in range(len(XY))])
        ave_noise = np.average([float(XY[j][1]) for j in range(len(XY)) if int(XY[j][1]) <= 10]) # determine average noise
        return (X,Y,ave_noise,Xscalar,filetoopen)


"""
open data and load it into plot window
"""
def openplot(X,Y,ave_noise,Xscalar,XFilter=(1,0),YFilter=1):

    min_X_Filter = XFilter[0]
    max_X_Filter = XFilter[1]

    if max_X_Filter == 0:

        X_filtered = [X[i] * Xscalar for i in range(len(X)) if
             X[i]*Xscalar >= min_X_Filter and Y[i] >= YFilter]  # remove values that dont make it through the filter
        Y_filtered = [Y[i] for i in range(len(Y)) if X[i]*Xscalar >= min_X_Filter and Y[i] >= YFilter]
    else:

        X_filtered = [X[i]*Xscalar for i in range(len(X)) if max_X_Filter >= X[i]*Xscalar >= min_X_Filter and Y[i] >= YFilter] # remove values that dont make it through the filter
        Y_filtered = [Y[i] for i in range(len(Y)) if max_X_Filter >= X[i]*Xscalar >= min_X_Filter and Y[i] >= YFilter]
    fig.clf()
    ax = fig.add_subplot()
    ax.vlines(X_filtered, 0, Y_filtered)
    ax.axhline(ave_noise, 0, 1, color="r") # add 'baseline'
    ax.set_xlim(0.0)
    ax.set_ylim(0.0)
    app.queueFunction(app.refreshPlot,"p1")
    global progress
    progress = 100

    app.registerEvent(updatprogress)
    app.queueFunction(app.hideSubWindow, "prog")

def load_file(input):
    X, Y, ave_noise, Xscalar,filetoopen = input
    global X_mem
    global Y_mem
    global ave_noise_mem
    global Xscalar_mem
    global XFilter
    global YFilter
    X_mem = X
    Y_mem = Y
    ave_noise_mem = ave_noise
    Xscalar_mem = Xscalar

    # Update Status Bar

    if XFilter[1] == 0:
        X_Filter_status = "Mass Filter (Da): {0}-".format(XFilter[0])
    else:
        X_Filter_status = "Mass Filter (Da): {0}-{1}".format(XFilter[0], XFilter[1])


    app.queueFunction(app.setStatusbar, X_Filter_status, 1)
    app.queueFunction(app.setStatusbar, "Intesity Filter: {0}".format(YFilter), 0)
    app.queueFunction(app.setStatusbarWidth, len(X_Filter_status), field=1)
    app.queueFunction(app.setStatusbarWidth, len("Intesity Filter: {0}".format(YFilter)), field=0)
    app.queueFunction(app.setStatusbarWidth, len("Loaded file: {0}".format(filetoopen)), field=2)
    app.queueFunction(app.setStatusbar, "Loaded file: {0}".format(filetoopen), 2)
    app.queueFunction(openplot,X, Y, ave_noise, Xscalar, XFilter, YFilter)



"""
controls the file menu functions
"""
def file_press(menu):

    global XFilter
    global YFilter
    global X_mem
    global Y_mem
    global ave_noise_mem
    global Xscalar_mem

    if menu == "Add from Clipboard":
        app.showSubWindow("clipadd")
    elif menu == "Open":
        filetoopen = app.openBox("openfile",fileTypes=[("compatible files",("*.I2MS","*.txt","*.csv")),("i2ms files","*.I2MS"),("mzML - not implemented yet","*.mzML"),("txt","*.txt"),("all file  types","*.*")])

        global loaded_file
        loaded_file = filetoopen

        if  filetoopen.split(".")[-1].upper() == "I2MS" :


            """
            load from I2MS file - save locally and globally - probably not the best way
            """

            app.queueFunction(app.showSubWindow,"prog")

            app.threadCallback(openI2MS,load_file,filetoopen)



        elif filetoopen.split(".")[-1].upper() == "MZML":

            app.queueFunction(app.showSubWindow, "prog")
            app.threadCallback(mZML_reader, load_file, filetoopen)

            "currently not supported"
            #app.errorBox("Open Error","Sorry mzML files are currently not supported for reading")




        elif filetoopen.split(".")[-1].upper() == "TXT" or filetoopen.split(".")[-1].upper() == "CSV":

            """
            load data from CSV file
            """
            try:
                app.queueFunction(app.showSubWindow, "prog")
                app.threadCallback(opencsv, load_file, filetoopen)


                # Update Status Bar


                if XFilter[1] == 0:
                    X_Filter_status = "Mass Filter (Da): {0}-".format(XFilter[0])
                else:
                    X_Filter_status = "Mass Filter (Da): {0}-{1}".format(XFilter[0], XFilter[1])

                app.setStatusbar("Intensity Filter: {0}".format(YFilter), 0)
                app.setStatusbar(X_Filter_status, 1)
                app.setStatusbarWidth(len("Intensity Filter: 1"), field=0)
                app.setStatusbarWidth(len(X_Filter_status), field=1)
                app.queueFunction(app.setStatusbar,"Loaded file: {0}".format(filetoopen), 2)
                app.queueFunction(app.setStatusbarWidth,len("Loaded file: {0}".format(filetoopen)), field=2)

            except:
                app.errorBox("Parsing Error","The csv file could no be parsed")

        elif filetoopen == "":
            return
        else:
            app.errorBox("Open Error","Selected File is not compatible")

    # Save currently loaded spectra
    elif menu == "Save as":
        current_file_name = loaded_file.split("/")[-1].split(".")[0]


        savefile = app.saveBox("save file", fileName=current_file_name,fileExt=".I2MS",fileTypes=[("i2ms files","*.I2MS"),("mzML","*.mzML")])
        if savefile.split(".")[-1] == "I2MS":
            CreateI2MS((X_mem,Y_mem,ave_noise_mem,Xscalar_mem),savefile)
        elif savefile.split(".")[-1] == "mzML":
            CreateMZML((X_mem,Y_mem,ave_noise_mem,Xscalar_mem),savefile)

def email():
    webbrowser.open('mailto:michael.hollas@northwestern.edu', new=1)

def about_press(menu):
    if menu == "Help":
        app.showSubWindow("help")
    if menu == "Source code":
        os.startfile(r'SourceCode.txt')
    if menu == "Version":
        app.showSubWindow("version")
def view_press(menu):
    if menu == "Change Filters":
             app.showSubWindow("Filters")
def update_filters(button):
    if button == "Update":

        min_X = app.getEntry("X_min_filter")
        max_X = app.getEntry("X_max_filter")

        if max_X == "":
            max_X = 0
        global XFilter
        global YFilter
        XFilter = (float(min_X),float(max_X))
        YFilter = int(app.getEntry("Y_filter"))

        global X_mem
        global Y_mem
        global ave_noise_mem
        global Xscalar_mem


        if XFilter[1] == 0:
            X_Filter_status = "Mass Filter (Da): {0}-".format(XFilter[0])
        else:
            X_Filter_status = "Mass Filter (Da): {0}-{1}".format(XFilter[0],XFilter[1])

        app.setStatusbar("Intensity Filter: {0}".format(YFilter), 0)
        app.setStatusbar(X_Filter_status, 1)

        app.setStatusbarWidth(len("Intensity Filter: 1"), field=0)
        app.setStatusbarWidth(len(X_Filter_status), field=1)

        openplot(X_mem, Y_mem, ave_noise_mem, Xscalar_mem, XFilter, YFilter)

def updatprogress():
    app.setMeter("progress",progress)

if __name__ == '__main__':

    with open("I2MS_Viewer_GUI.py","r") as source:
        with open("SourceCode.txt","w") as writefile:
            writefile.write(source.read().split("if __name__ == '__main__':")[0])


    version = "0.1 alpha build"

    #Create app - name and size
    app = gui("I2MS Viewer {0}".format(version), "1200x800",showIcon=False)

    #build menus
    file_menus = ["Open","Save as","Add from Clipboard"]
    view_menu = ["Change Filters"]
    about_menu = ["Version", "Help", "Source code"]
    app.addMenuList("file",file_menus,file_press)
    app.addMenuList("View", view_menu, view_press)
    app.addMenuList("About", about_menu, about_press)

    #Create starting StatusBar
    app.addStatusbar(fields=3,side="RIGHT")
    app.setStatusbar("Loaded file: None", 2)
    app.setStatusbar("Mass Filter (Da): 1-", 1)
    app.setStatusbar("Intensity Filter: 1", 0)
    app.setStatusbarWidth(len("Mass Filter (Da): 1"), field=1)
    app.setStatusbarWidth(len("Intensity Filter: 1"), field=0)
    app.setStatusbarWidth(len("Loaded file: None"), field=2)


    #Create Empty matplotlib plot
    fig = app.addPlotFig("p1",showNav=True)

    #Version Window
    app.startSubWindow("version","Version")
    app.setSize(300, 200)
    app.label("I2MS Viewer {0}".format(version))
    app.label("Created by Mike Hollas")
    app.stopSubWindow()

    #help window
    app.startSubWindow("help","Help")
    app.setSize(300, 200)
    app.startFrame("1")

    app.message("\nFor any help please email michael.hollas@northwestern.edu\n")
    app.addButton("email",email)
    app.stopFrame()
    app.stopSubWindow()

    #progress window
    app.startSubWindow("prog","progress")
    app.setTransparency(50)

    app.addMeter("progress")
    app.stopSubWindow()

    #Build add from clipboard subwindow
    app.startSubWindow("clipadd", "Add From Clipboard")
    app.addScrolledTextArea("txtarea1")
    app.addButtons(["add from clipboard","Load"],clipboardwin)
    app.stopSubWindow()

    #Build Filter subwindow
    app.startSubWindow("Filters","Adjust Filters")
    app.addLabel("Mass Filter range (Da)",row=0, column=0)
    app.addLabel("Intensity Filter", row=1, column=0)
    app.addEntry("X_min_filter", row=0, column=1)
    app.addEntry("X_max_filter", row=0, column=2)
    app.addEntry("Y_filter", row=1, column=1)
    app.addButton("Update",update_filters)



    app.setEntry("Y_filter",YFilter)
    app.setEntry("X_min_filter", XFilter[0])
    app.stopSubWindow()

    #Initialize the app
    app.go()