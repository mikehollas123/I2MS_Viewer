from I2MS_Viewer_cmd import *
from appJar import gui

# Global Variables to store spectral data
X_mem = []
Y_mem = []
ave_noise_mem = 1
Xscalar_mem = 1
XFilter = (1,0)
YFilter = 1
loaded_file =""


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
    app.refreshPlot("p1")


"""
controls the file menu functions
"""
def file_press(menu):

    global XFilter
    global YFilter

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

            openplot(X,Y,ave_noise,Xscalar,XFilter,YFilter)

        elif filetoopen.split(".")[-1].upper() == "MZML":
            "currently not supported"
            app.errorBox("Open Error","Sorry mzML files are currently not supported for reading")
        elif filetoopen.split(".")[-1].upper() == "TXT" or filetoopen.split(".")[-1].upper() == "CSV":

            """
            load data from CSV file
            """
            try:
                X, Y, ave_noise, Xscalar = opencsv(filetoopen)


                X_mem = X
                Y_mem = Y
                ave_noise_mem = ave_noise
                Xscalar_mem = Xscalar

                # Update Status Bar


                if XFilter[1] == 0:
                    X_Filter_status = "Mass Filter (Da): {0}-".format(XFilter[0])
                else:
                    X_Filter_status = "Mass Filter (Da): {0}-{1}".format(XFilter[0], XFilter[1])

                app.setStatusbar("Intensity Filter: {0}".format(YFilter), 0)
                app.setStatusbar(X_Filter_status, 1)

                app.setStatusbarWidth(len("Intensity Filter: 1"), field=0)
                app.setStatusbarWidth(len(X_Filter_status), field=1)



                app.setStatusbar("Loaded file: {0}".format(filetoopen), 2)

                app.setStatusbarWidth(len("Loaded file: {0}".format(filetoopen)), field=2)

                openplot(X,Y,ave_noise,Xscalar,XFilter,YFilter)
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

def about_press(menu):
    if menu == "help":
        print("help")

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

if __name__ == '__main__':
    #Create app - name and size
    app = gui("I2MS Viewer 0.1", "800x600",showIcon=False)

    #build menus
    file_menus = ["Open","Save as","Add from Clipboard"]
    about_menu = ["Version","help"]
    view_menu = ["Change Filters"]
    app.addMenuList("file",file_menus,file_press)
    app.addMenuList("About", about_menu, about_press)
    app.addMenuList("View", view_menu, view_press)

    #Create starting StatusBar
    app.addStatusbar(fields=3,side="RIGHT")
    app.setStatusbar("Loaded file: None", 2)
    app.setStatusbar("Mass Filter (Da): 1", 1)
    app.setStatusbar("Intensity Filter: 1", 0)
    app.setStatusbarWidth(len("Mass Filter (Da): 1"), field=1)
    app.setStatusbarWidth(len("Intensity Filter: 1"), field=0)
    app.setStatusbarWidth(len("Loaded file: None"), field=2)

    #Create Empty matplotlib plot
    fig = app.addPlotFig("p1",showNav=True)

    #Build add from clipboard subwindow
    app.startSubWindow("clipadd", "Add From Clipboard")
    app.addScrolledTextArea("txtarea1")
    app.addButtons(["add from clipboard","Save"],clipboardwin)
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