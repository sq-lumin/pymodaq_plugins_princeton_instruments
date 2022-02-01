import numpy as np
from easydict import EasyDict as edict
from pymodaq.daq_utils.daq_utils import ThreadCommand, getLineInfo, DataFromPlugins, Axis
from pymodaq.daq_viewer.utility_classes import DAQ_Viewer_base, comon_parameters, main
from pyqtgraph.parametertree import Parameter

from ...hardware.picam_utils import define_pymodaq_pyqt_parameter

import pylablib.devices.PrincetonInstruments as PI


class DAQ_2DViewer_PYLon(DAQ_Viewer_base):
    """
    """
    _dvcs = PI.list_cameras()
    serialnumbers = [dvc.serial_number for dvc in _dvcs]

    params = comon_parameters + [
        {'title': 'Controller ID:', 'name': 'controller_id', 'type': 'str', 'value': '', 'readonly': True},
        {'title': 'Serial number:', 'name': 'serial_number', 'type': 'list', 'limits': serialnumbers}
    ]

    def __init__(self, parent=None, params_state=None):
        super().__init__(parent, params_state)

        self.x_axis = None
        self.y_axis = None

    def _update_all_settings(self):
        for grandparam in ['settable_camera_parameters', 'read_only_camera_parameters']:
            for param in self.settings.child(grandparam).children():
                #update limits in the parameter
                self.controller.get_attribute(param.title()).update_limits()
                #retrieve a value change in other parameters
                newval = self.controller.get_attribute_value(param.title())
                if newval != param.value():
                    self.settings.child(grandparam, param.name()).setValue(newval)
                    self.emit_status(ThreadCommand('Update_Status', [f'updated {param.title()}: {param.value()}']))

    def commit_settings(self, param):
        """
        """
        #Only if the parameter that was changed is settable and also
        if self.controller.get_attribute(param.title()).writable:
            if self.controller.get_attribute_value(param.title()) != param.value():
                #Update the controller
                self.controller.set_attribute_value(param.title(),param.value(),truncate=True,error_on_missing=True)
                #Log that a parameter change was called
                self.emit_status(ThreadCommand('Update_Status', [f'Changed {param.title()}: {param.value()}']))
                self._update_all_settings()

#         ## TODO for your custom plugin
#         if param.name() == "a_parameter_you've_added_in_self.params":
#             self.controller.your_method_to_apply_this_param_change()
# #        elif ...

    ##

    def ini_detector(self, controller=None):
        """Detector communication initialization

        Parameters
        ----------
        controller: (object) custom object of a PyMoDAQ plugin (Slave case). None if only one detector by controller (Master case)

        Returns
        -------
        self.status (edict): with initialization status: three fields:
            * info (str)
            * controller (object) initialized controller
            *initialized: (bool): False if initialization failed otherwise True
        """

        try:
            self.status.update(edict(initialized=False, info="", x_axis=None, y_axis=None, controller=None))
            if self.settings.child(('controller_status')).value() == "Slave":
                if controller is None:
                    raise Exception('no controller has been defined externally while this detector is a slave one')
                else:
                    self.controller = controller
            else:

                camera = PI.PicamCamera(self.settings.child('serial_number').value())
                self.settings.child('controller_id').setValue(camera.get_device_info().model)

                self.controller = camera  # any object that will control the stages

                atd = camera.get_all_attributes(copy=True)
                camera_params = []
                for k, v in atd.items():
                    tmp = define_pymodaq_pyqt_parameter(v)
                    if tmp != None:
                        camera_params.append(tmp)
                #####################################

                read_and_set_parameters = [par for par in camera_params if not par['readonly']]
                read_only_parameters = [par for par in camera_params if par['readonly']]

                self.settings.addChild({'title':  'Settable Camera Parameters',
                                        'name': 'settable_camera_parameters',
                                        'type': 'group',
                                        'children': read_and_set_parameters,
                                        })

                self.settings.addChild({'title' : 'Read Only Camera Parameters',
                                        'name': 'read_only_camera_parameters',
                                        'type': 'group',
                                        'children': read_only_parameters,
                                        })

            # ## TODO for your custom plugin
            # # get the x_axis (you may want to to this also in the commit settings if x_axis may have changed
            # data_x_axis = self.controller.your_method_to_get_the_x_axis()  # if possible
            # self.x_axis = Axis(data=data_x_axis, label='', units='')
            # self.emit_x_axis()
            #
            # # get the y_axis (you may want to to this also in the commit settings if y_axis may have changed
            # data_y_axis = self.controller.your_method_to_get_the_y_axis()  # if possible
            # self.y_axis = Axis(data=data_y_axis, label='', units='')
            # self.emit_y_axis()

            # ## TODO for your custom plugin
            # # initialize viewers pannel with the future type of data
            # self.data_grabed_signal_temp.emit([DataFromPlugins(name='Mock1', data=["2D numpy array"],
            #                                       dim='Data2D', labels=['dat0'],
            #                                       x_axis=self.x_axis,
            #                                       y_axis=self.y_axis), ])

            ##############################

            self.status.info = "Initialising camcam"
            self.status.initialized = True
            self.status.controller = self.controller
            return self.status

        except Exception as e:
            self.emit_status(ThreadCommand('Update_Status', [getLineInfo() + str(e), 'log']))
            self.status.info = getLineInfo() + str(e)
            self.status.initialized = False
            return self.status

    def close(self):
        """
        Terminate the communication protocol
        """
        self.controller.close()
        ##

    def grab_data(self, Naverage=1, **kwargs):
        """

        Parameters
        ----------
        Naverage: (int) Number of hardware averaging
        kwargs: (dict) of others optionals arguments
        """
        pass
        # ## TODO for your custom plugin
        #
        # ##synchrone version (blocking function)
        # data_tot = self.controller.your_method_to_start_a_grab_snap()
        # self.data_grabed_signal.emit([DataFromPlugins(name='Mock1', data=data_tot,
        #                                               dim='Data2D', labels=['dat0'])])
        # #########################################################
        #
        # ##asynchrone version (non-blocking function with callback)
        # self.controller.your_method_to_start_a_grab_snap(self.callback)
        #########################################################

    def callback(self):
        """optional asynchrone method called when the detector has finished its acquisition of data"""
        pass
        # data_tot = self.controller.your_method_to_get_data_from_buffer()
        # self.data_grabed_signal.emit([DataFromPlugins(name='Mock1', data=data_tot,
        #                                               dim='Data2D', labels=['dat0'])])

    def stop(self):
        pass
        # ## TODO for your custom plugin
        # self.controller.your_method_to_stop_acquisition()
        # self.emit_status(ThreadCommand('Update_Status', ['Some info you want to log']))
        ##############################

        return ''


if __name__ == '__main__':
    main(__file__)