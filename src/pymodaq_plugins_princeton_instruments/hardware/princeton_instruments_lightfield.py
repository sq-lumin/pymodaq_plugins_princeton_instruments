# -*- coding: utf-8 -*-
"""
Created on Mon Feb  5 17:09:01 2024
Sébastien Quistrebert
"""

import pyqtgraph as pg

# Import the .NET class library
import clr, ctypes

# Import python sys module
import sys, os

# numpy import
import numpy as np

# Import c compatible List and String
from System import String
from System.Collections.Generic import List
from System.Runtime.InteropServices import Marshal
from System.Runtime.InteropServices import GCHandle, GCHandleType

# Add needed dll references
sys.path.append(os.environ['LIGHTFIELD_ROOT'])
sys.path.append(os.environ['LIGHTFIELD_ROOT']+"\\AddInViews")
clr.AddReference('PrincetonInstruments.LightFieldViewV5')
clr.AddReference('PrincetonInstruments.LightField.AutomationV5')
clr.AddReference('PrincetonInstruments.LightFieldAddInSupportServices')

# PI imports
from PrincetonInstruments.LightField.Automation import *
from PrincetonInstruments.LightField.AddIns import *


class PILF():
    
    def __init__(self):
        self._auto = Automation(True, List[String]())

        # Get LightField Application object
        self._application = self._auto.LightFieldApplication

        # Get experiment object
        self._experiment = self._application.Experiment
        
        #Close the shutter for security
        self._experiment.SetValue(CameraSettings.ShutterTimingMode, 'AlwaysClosed')
        #Do stuff when lightfield is closed (event handler). Not sure if working properly
        self._auto.LightFieldClosing += self.lightField_closing  
        
    def err_init(self):
        camera = None
        err = False
        # Find connected device
        for device in self._experiment.ExperimentDevices:
            if (device.Type == DeviceType.Camera and self._experiment.IsReadyToRun):
                camera = device

        if (camera == None):
            err = "No camera detected."

        if (not self._experiment.IsReadyToRun):
            err = "Experiment not ready"
        
        return err
    
    def capture_spectra(self):
        if self._experiment.get_Name() == 'LABVIEW_20180912_64lignes_3kHz_1zone' and self._experiment.IsReadyToRun:
            frames = self._experiment.GetValue(ExperimentSettings.AcquisitionFramesToStore)
            image_array = np.zeros((1024,frames))
            dataset = self._experiment.Capture(frames)
            # Stop processing if we do not have all frames
            if (dataset.Frames != frames):
                # Clean up the image data set
                dataset.Dispose()
                raise Exception("Frames are not equal.")
            image_frame = dataset.GetFrame(0, frames - 1)
            image_array = np.frombuffer(dataset.GetDataBuffer(), dtype = 'uint16').reshape((image_frame.Width, frames), order = 'F')
            return image_array
    
    def lightField_closing(self, sender, event_args):
        #Close the shutter for security
        self._experiment.SetValue(CameraSettings.ShutterTimingMode, 'AlwaysClosed')
        self.unhook_events()       
        self.close()
    
    def open_shutter(self, openShutter = True):
        if openShutter:
            self._experiment.SetValue(CameraSettings.ShutterTimingMode, 'AlwaysOpen')
        else:
            self._experiment.SetValue(CameraSettings.ShutterTimingMode, 'AlwaysClosed')
    
    def setNframes(self, Nframes = 1000):
        self._experiment.SetValue(ExperimentSettings.AcquisitionFramesToStore, str(Nframes))
        
    def unhook_events(self):
        # Unhook the eventhandler for IsReadyToRunChanged
        # Will be called upon exiting
        self._auto.LightFieldClosing -= self.lightField_closing    
            
    def stop(self):
        pass
    
    def close(self):
        self._auto.Dispose()
    
    def get_x_axis(self):
        return np.arange(1024)
    
if __name__ == "__main__":
    pass
    #pilf = PILF()
    #pilf._experiment.SetValue(CameraSettings.ShutterTimingMode, 'AlwaysOpen')
    #image_array = pilf.capture_spectra()
    #pilf._experiment.SetValue(CameraSettings.ShutterTimingMode, 'AlwaysClosed')
    #pilf.lightField_closing(1,1)