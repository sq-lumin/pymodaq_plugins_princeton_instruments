import numpy as np
from pymodaq.utils.daq_utils import ThreadCommand, get_plugins
from pymodaq.utils.data import DataFromPlugins, Axis, DataToExport
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, comon_parameters, main
from pymodaq.utils.parameter import Parameter

from pymodaq_plugins_princeton_instruments.hardware.princeton_instruments_lightfield import PILF



# TODO:
# (1) change the name of the following class to DAQ_1DViewer_TheNameOfYourChoice
# (2) change the name of this file to daq_1Dviewer_TheNameOfYourChoice ("TheNameOfYourChoice" should be the SAME
#     for the class name and the file name.)
# (3) this file should then be put into the right folder, namely IN THE FOLDER OF THE PLUGIN YOU ARE DEVELOPING:
#     pymodaq_plugins_my_plugin/daq_viewer_plugins/plugins_1D
class DAQ_1DViewer_Lightfield(DAQ_Viewer_base):
    """ Instrument plugin class for a 1D viewer.
    
    This object inherits all functionalities to communicate with PyMoDAQ’s DAQ_Viewer module through inheritance via
    DAQ_Viewer_base. It makes a bridge between the DAQ_Viewer module and the Python wrapper of a particular instrument.

    TODO Complete the docstring of your plugin with:
        * The set of instruments that should be compatible with this instrument plugin.
        * With which instrument it has actually been tested.
        * The version of PyMoDAQ during the test.
        * The version of the operating system.
        * Installation instructions: what manufacturer’s drivers should be installed to make it run?

    Attributes:
    -----------
    controller: object
        The particular object that allow the communication with the hardware, in general a python wrapper around the
         hardware library.
         
    # TODO add your particular attributes here if any

    """
    params = comon_parameters+[{'title' : 'Lightfield Params', 'name' : 'lightfield_params', 'type' : 'group', 'children' : [
            {'title' : 'Camera Shutter', 'name' : 'camera_shutter', 'type' : 'bool', 'value' : False},
            {'title' : 'Number of pairs of spectra', 'name' : 'kc_pairs', 'type' : 'int', 'value' : 500}
            ]}
        ]

    def ini_attributes(self):
        if self.controller is None:
            self.controller = {}
    
        self.x_axis = None

    def commit_settings(self, param: Parameter):
        """Apply the consequences of a change of value in the detector settings

        Parameters
        ----------
        param: Parameter
            A given parameter (within detector_settings) whose value has been changed by the user
        """
        if param.name() == "camera_shutter":
            self.controller['lightfield'].open_shutter(param.value())
        elif param.name() == "kc_pairs":
            self.controller['lightfield'].setNframes(param.value()*2)
        
    def ini_detector(self, controller=None):
        """Detector communication initialization

        Parameters
        ----------
        controller: (object)
            custom object of a PyMoDAQ plugin (Slave case). None if only one actuator/detector by controller
            (Master case)

        Returns
        -------
        info: str
        initialized: bool
            False if initialization failed otherwise True
        """
        if controller is None:
            controller = {}
        new_controller = controller.copy()
        new_controller['lightfield'] = PILF()
        self.ini_detector_init(old_controller=controller, new_controller=new_controller)
        
        ## TODO for your custom plugin
        # get the x_axis (you may want to to this also in the commit settings if x_axis may have changed
        data_x_axis = self.controller['lightfield'].get_x_axis()  # if possible
        self.x_axis = Axis(data=data_x_axis, label='', units='', index=0)

        # TODO for your custom plugin. Initialize viewers pannel with the future type of data
        data0 = np.zeros(1024)
        self.dte_signal_temp.emit(DataToExport(name='lightfield',
                                               data=[DataFromPlugins(name='Spectra',
                                                                     data=[data0, data0],
                                                                     dim='Data1D', labels=['TA', 'I_avg'],
                                                                     axes=[self.x_axis])]))
        err = self.controller['lightfield'].err_init()
        if not err:
            info = ""
            initialized = True
        else:
            info = err
            initialized = False
        return info, initialized

    def close(self):
        """Terminate the communication protocol"""
        self.controller['lightfield'].close()  # when writing your own plugin replace this line

    def grab_data(self, Naverage=1, **kwargs):
        """Start a grab from the detector

        Parameters
        ----------
        Naverage: int
            Number of hardware averaging (if hardware averaging is possible, self.hardware_averaging should be set to
            True in class preamble and you should code this implementation)
        kwargs: dict
            others optionals arguments
        """
        ## TODO for your custom plugin: you should choose EITHER the synchrone or the asynchrone version following

        ##synchrone version (blocking function)
        image_array = self.capture_spectra()
        I_ON = image_array[:, ::2]
        I_OFF = image_array[:, 1::2]
        I_ON, I_OFF = I_ON.astype(np.int64), I_OFF.astype(np.int64) 
        TA = -1e3*np.mean(np.log(I_ON/I_OFF), axis = 1)
        I_avg = np.mean(I_ON + I_OFF, axis = 1)/2
        self.dte_signal.emit(DataToExport('lightfield',
                                          data=[DataFromPlugins(name='Spectra',
                                                                data=[TA, I_avg],
                                                                dim='Data1D', labels=['TA', 'I_avg'],
                                                                axes=[self.x_axis])]))
        ##asynchrone version (non-blocking function with callback)
        #self.controller.your_method_to_start_a_grab_snap(self.callback)
        #########################################################
    
    def capture_spectra(self):
        """Single acquisition according the specified experiment settings"""
        return self.controller['lightfield'].capture_spectra()
    
    def callback(self):
        """optional asynchrone method called when the detector has finished its acquisition of data"""
        data_tot = self.controller['lightfield'].your_method_to_get_data_from_buffer()
        self.dte_signal.emit(DataToExport('lightfield',
                                          data=[DataFromPlugins(name='Mock1', data=data_tot,
                                                                dim='Data1D', labels=['dat0', 'data1'])]))

    def stop(self):
        """Stop the current grab hardware wise if necessary"""
        ## TODO for your custom plugin
        self.controller['lightfield'].stop()  # when writing your own plugin replace this line
        self.emit_status(ThreadCommand('Update_Status', ['Lightfield plugin stopped']))
        ##############################
        return ''
    
    def get_controller_class(self):
        return PILF
    
if __name__ == '__main__':
    main(__file__)
