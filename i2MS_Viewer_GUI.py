from I2MS_Viewer_cmd import *
from appJar import gui

# Global Variables to store spectral data
X_mem = []
Y_mem = []
ave_noise_mem = 1
Xscalar_mem = 1

"""
Button control for Add from Clipboard window
"""
def clipboardwin(button):


    if button == "add from clipboard":
        app.setTextArea("txtarea1",app.topLevel.clipboard_get() ) # add clipborad to textarea object
    elif button == "Save":


            save_file = app.saveBox("clipsave",fileName="i2ms_spec",fileExt=".I2MS",fileTypes=[("i2ms files","*.I2MS"),("mzML","*.mzML")],parent="clipadd")
            if save_file.split(".")[-1] == "I2MS":
                CreateI2MS(app.getTextArea("txtarea1"),save_file)
            elif save_file.split(".")[-1] == "mzML":
                CreateMZML(app.getTextArea("txtarea1"),save_file)
            app.setTextArea("txtarea1","" )
            app.hideSubWindow("clipadd")


"""
Opens an I2MS file
"""
def openI2MS(filetoopen):
    with open(filetoopen, "rb") as pklin:
        return pkl.load(pklin)
"""
open and parse a csv/txt file of X,Y data
"""
def opencsv(filetoopen):

    with open(filetoopen, "r") as readfile:
        data = readfile.read()
        lines = data.split("\n")
        Xscalar = float(lines[1].split(",")[0]) - float(lines[0].split(",")[0]) # create a scalar so we can store X values as int
        XY = [(float(lines[i].split(",")[0]) / Xscalar, int(lines[i].split(",")[1])) for i in range(len(lines))
              if int(lines[i].split(",")[1]) > 0] # remove 0 values and adjust for scalar

        X, Y = ([int(XY[x][0]) for x in range(len(XY))], [int(XY[x][1]) for x in range(len(XY))])
        ave_noise = np.average([float(XY[j][1]) for j in range(len(XY)) if int(XY[j][1]) <= 10]) # determine average noise
        return (X,Y,ave_noise,Xscalar)


"""
open data and load it into plot window
"""
def openplot(X,Y,ave_noise,Xscalar,XFilter=1,YFilter=0):
    X = [X[i]*Xscalar for i in range(len(X)) if X[i] >= XFilter and Y[i] >= YFilter] # remove values that dont make it through the filter
    Y = [Y[i] for i in range(len(X)) if X[i] >= XFilter and Y[i] >= YFilter]
    ax = fig.add_subplot()
    ax.vlines(X, 0, Y)
    ax.axhline(ave_noise, 0, 1, color="r") # add 'baseline'
    ax.set_xlim(0.0)
    ax.set_ylim(0.0)
    app.refreshPlot("p1")


"""
controls the file menu functions
"""
def file_press(menu):
    if menu == "Add from Clipboard":
        app.showSubWindow("clipadd")
    elif menu == "Open":
        filetoopen = app.openBox("openfile",fileTypes=[("compatible files",("*.I2MS","*.txt")),("i2ms files","*.I2MS"),("mzML","*.mzML"),("txt","*.txt"),("all file  types","*.*")])

        if  filetoopen.split(".")[-1].upper() == "I2MS" :


            """
            load from I2MS file - save locally and globally - probably not the best way
            """
            X, Y, ave_noise, Xscalar = openI2MS(filetoopen)
            global X_mem
            global Y_mem
            global ave_noise_mem
            global Xscalar_mem
            X_mem = X
            Y_mem = Y
            ave_noise_mem = ave_noise
            Xscalar_mem = Xscalar


            #Update Status Bar
            app.setStatusbar("Loaded file: {0}".format(filetoopen), 2)
            app.setStatusbar("Mass Filter (Da): 1", 1)
            app.setStatusbar("Intesity Filter: 1", 0)
            app.setStatusbarWidth(len("Mass Filter (Da): 1"), field=1)
            app.setStatusbarWidth(len("Intesity Filter: 1"), field=0)
            app.setStatusbarWidth(len("Loaded file: {0}".format(filetoopen)), field=2)

            openplot(X,Y,ave_noise,Xscalar)

        elif filetoopen.split(".")[-1].upper() == "MZML":
            "currently not supported"
        elif filetoopen.split(".")[-1].upper() == "TXT" or filetoopen.split(".")[-1].upper() == "CSV":

            """
            load data from CSV file
            """
            X, Y, ave_noise, Xscalar = opencsv(filetoopen)


            X_mem = X
            Y_mem = Y
            ave_noise_mem = ave_noise
            Xscalar_mem = Xscalar

            # Update Status Bar
            app.setStatusbar("Loaded file: {0}".format(filetoopen), 2)
            app.setStatusbar("Mass Filter (Da): 1", 1)
            app.setStatusbar("Intesity Filter: 1", 0)
            app.setStatusbarWidth(len("Mass Filter (Da): 1"), field=1)
            app.setStatusbarWidth(len("Intesity Filter: 1"), field=0)
            app.setStatusbarWidth(len("Loaded file: {0}".format(filetoopen)), field=2)

            openplot(X,Y,ave_noise,Xscalar)

        elif filetoopen == "":
            return
        else:
            app.warningBox("warn","Selected File is not compatable")

    # Save currently loaded spectra
    elif menu == "Save as":
        savefile = app.saveBox("save file", fileName="i2ms_spec",fileExt=".I2MS",fileTypes=[("i2ms files","*.I2MS"),("mzML","*.mzML")])
        if savefile.split(".")[-1] == "I2MS":
            CreateI2MS((X_mem,Y_mem,ave_noise_mem,Xscalar_mem),savefile)
        elif savefile.split(".")[-1] == "mzML":
            CreateMZML((X_mem,Y_mem,ave_noise_mem,Xscalar_mem),savefile)

def about_press(menu):
    if menu == "help":
        print("help")

if __name__ == '__main__':
    #Create app - name and size
    app = gui("I2MS Viewer 0.1", "800x600")

    #build menus
    file_menus = ["Open","Save as","Add from Clipboard"]
    about_menu = ["Version","help"]
    app.addMenuList("file",file_menus,file_press)
    app.addMenuList("About", about_menu, about_press)

    #Create starting StatusBar
    app.addStatusbar(fields=3,side="RIGHT")
    app.setStatusbar("Loaded file: None", 2)
    app.setStatusbar("Mass Filter (Da): 1", 1)
    app.setStatusbar("Intesity Filter: 1", 0)
    app.setStatusbarWidth(len("Mass Filter (Da): 1"), field=1)
    app.setStatusbarWidth(len("Intesity Filter: 1"), field=0)
    app.setStatusbarWidth(len("Loaded file: None"), field=2)

    #Create Empty matplotlib plot
    fig = app.addPlotFig("p1",showNav=True)

    #Build add from clipboard subwindow
    app.startSubWindow("clipadd", "Add From Clipboard")
    app.addScrolledTextArea("txtarea1")
    app.addButtons(["add from clipboard","Save"],clipboardwin)
    app.stopSubWindow()

    #Initialize the app
    app.go()