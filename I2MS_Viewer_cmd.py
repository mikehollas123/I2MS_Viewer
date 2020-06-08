
import pickle as pkl
import argparse
import numpy as np
from psims.mzml import MzMLWriter


def CreateI2MS(data,file):

    if type(data) is tuple:
        with open(str(file), "wb") as pklout:
            print(len(data[0]))
            pkl.dump(data, pklout)
            return
    lines = data.split("\n")

    Xscalar = float(lines[1].split(",")[0]) -float(lines[0].split(",")[0])
    XY = [(float(lines[i].split(",")[0])/Xscalar, int(lines[i].split(",")[1])) for i in range(len(lines)) if int(lines[i].split(",")[1]) > 0]

    X,Y = ([int(XY[x][0]) for x in range(len(XY))],[int(XY[x][1]) for x in range(len(XY))])
    ave_noise = np.average([float(XY[j][1]) for j in range(len(XY)) if  int(XY[j][1]) <= 10])

    with open(str(file), "wb") as pklout:

        pkl.dump((X, Y, ave_noise,Xscalar), pklout)
def CreateMZML(data,file):


    if type(data) is tuple:
        X, Y, ave_noise,Xscalar = data
        X = [X[i]*Xscalar for i in range(len(X))]
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
            "id":"I2MS to mzML",
        "veresion":"0.1.1","params":["python-psims"]}
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
            writer.ProcessingMethod(order=1,software_reference="I2MS to mzML",params=["Removal of 0 intesity peaks","Conversion to mzML"])
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

if __name__ == '__main__':
    """
        parser = argparse.ArgumentParser(description='Display I2MS data and creates a i2ms file', prog="I2MS_Viewer.exe")
        parser.add_argument("FilePath", type=str, help="The filepath of the desired i2ms file or csv file")
        parser.add_argument("XFilter", nargs='?',type=float, help="Filters out peaks below this Da mass - default is 1000",default=1000.0)
        parser.add_argument("YFilter", nargs='?',type=float, help="Filters out peaks below this intensity - default is 2",default=2.0)
        args = parser.parse_args()
    
        ViewI2MSData(args.FilePath,args.XFilter,args.YFilter)
    """