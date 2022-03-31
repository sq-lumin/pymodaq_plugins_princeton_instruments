import numpy as np
from easydict import EasyDict as edict
from pymodaq.daq_utils.daq_utils import ThreadCommand, getLineInfo, DataFromPlugins, Axis
from pymodaq.daq_viewer.utility_classes import DAQ_Viewer_base, comon_parameters, main
# from pyqtgraph.parametertree import Parameter
from qtpy import QtWidgets

from ...hardware.picam_utils import define_pymodaq_pyqt_parameter, sort_by_priority_list

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

    hardware_averaging = False

    def __init__(self, parent=None, params_state=None):
        super().__init__(parent, params_state)

        self.x_axis = None
        self.y_axis = None

        self.data_shape = 'Data2D'

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

    def _update_rois(self,):
        """ """
        new_x = self.settings.child('settable_camera_parameters', 'rois', 'x').value()
        new_width = self.settings.child('settable_camera_parameters', 'rois', 'width').value()
        new_xbinning = self.settings.child('settable_camera_parameters', 'rois', 'x_binning').value()

        new_y = self.settings.child('settable_camera_parameters', 'rois', 'y').value()
        new_height = self.settings.child('settable_camera_parameters', 'rois', 'height').value()
        new_ybinning = self.settings.child('settable_camera_parameters', 'rois', 'y_binning').value()

        new_roi = (new_x, new_width, new_xbinning, new_y, new_height, new_ybinning)
        if new_roi != tuple(self.controller.get_attribute_value('ROIs')[0]):
            # self.controller.set_attribute_value("ROIs",[new_roi])
            self.controller.set_roi(new_x,new_x+new_width,new_y,new_y+new_height,hbin=new_xbinning,vbin=new_ybinning)
            self.emit_status(ThreadCommand('Update_Status', [f'Changed ROI: {new_roi}']))
            self._update_all_settings()
            self.controller.clear_acquisition()
            self.controller._commit_parameters() #Needed so that the new ROIs are checked by the camera
            self.controller.setup_acquisition()


    def commit_settings(self, param):
        """ """
        # We have to treat rois specially
        if param.parent().name() == "rois":
            self._update_rois()
        # Otherwise the other parameters can be dealt with at once
        elif self.controller.get_attribute(param.title()).writable:
            if self.controller.get_attribute_value(param.title()) != param.value():
                #Update the controller
                self.controller.set_attribute_value(param.title(),param.value(),truncate=True,error_on_missing=True)
                #Log that a parameter change was called
                self.emit_status(ThreadCommand('Update_Status', [f'Changed {param.title()}: {param.value()}']))
                self._update_all_settings()


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

                priority = ['Exposure Time',
                            'ADC Speed',
                            'ADC Analog Gain',
                            'ADC Quality',
                            'ROIs',
                            'Sensor Temperature Set Point',
                            ]

                read_and_set_parameters = sort_by_priority_list(read_and_set_parameters,priority)

                priority = ['Sensor Temperature',
                            'Readout Time Calculation',
                            'Frame Rate Calculation',
                            'Pixel Width',
                            'Pixel Height',
                            ]

                read_only_parameters = sort_by_priorityó_list(read_only_parameters,priority)

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

            self._prepare_view()

            self.status.info = "Initialised camera"
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
        #Terminate the communication
        self.controller.close()
        self.controller = None #Garbage collect the controller
        #Clear all the parameters
        self.settings.child('settable_camera_parameters').clearChildren()
        self.settings.child('settable_camera_parameters').remove()
        self.settings.child('read_only_camera_parameters').clearChildren()
        self.settings.child('read_only_camera_parameters').remove()
        #Reset the status of the Viewer Plugin
        self.status.initialized = False
        self.status.controller = None
        self.status.info = ""


    def _toggle_non_online_parameters(self,enabled):
        for param in self.settings.child('settable_camera_parameters').children():
            if not self.controller.get_attribute(param.title()).can_set_online:
                param.setOpts(enabled=enabled)
        #The ROIs parameters still need special treatment which is not ideal but well...
        for param in self.settings.child('settable_camera_parameters',"rois").children():
            param.setOpts(enabled=enabled)


    def _prepare_view(self):
        wx = self.settings.child('settable_camera_parameters', 'rois', 'width').value()
        wy = self.settings.child('settable_camera_parameters', 'rois', 'height').value()
        bx = self.settings.child('settable_camera_parameters', 'rois', 'x_binning').value()
        by = self.settings.child('settable_camera_parameters', 'rois', 'y_binning').value()

        sizex = wx//bx
        sizey = wy//by

        mock_data = np.zeros((sizey,sizex))

        if sizey != 1 and sizex != 1:
            data_shape = 'Data2D'
        else:
            data_shape = 'Data1D'

        if data_shape != self.data_shape:
            self.data_shape = data_shape
            # init the viewers
            self.data_grabed_signal_temp.emit([DataFromPlugins(name='Picam',
                                                               data=[np.squeeze(mock_data)],
                                                               dim=self.data_shape)])

    def grab_data(self, Naverage=1, **kwargs):
        """
        Parameters
        ----------
        Naverage: (int) Number of averaging
        kwargs: (dict) of others optionals arguments
        """
        # Warning, acquisition_in_progress returns 1,0 and not a real bool
        if not self.controller.acquisition_in_progress():
            # 0. Disable all non online-settable parameters
            self._toggle_non_online_parameters(enabled=False)
            # 1. Start acquisition
            self.controller.stop_acquisition()
            self.controller.clear_acquisition()
            self.controller.start_acquisition()

            self._prepare_view()


        self.controller.wait_for_frame()  # wait for the next available frame
        frame = self.controller.read_oldest_image()

        self.data_grabed_signal.emit([DataFromPlugins(name='Picam',
                                                      data=[np.squeeze(frame)],
                                                      dim=self.data_shape)])
        QtWidgets.QApplication.processEvents()

        # self.data_grabed_signal.emit([DataFromPlugins(name='Picam', data=[np.squeeze(frame)],
        #                                               dim=self.data_shape, labels=['img'])])
        # self.data_grabed_signal.emit([DataFromPlugins(name='Picam', data=[frame], labels=['img'])])

        # if frame.shape[0]>2:
        #     self.data_grabed_signal.emit([DataFromPlugins(name='Picam', data=[frame],
        #                                               dim='Data2D', labels=['img'])])
        # elif frame.shape[0]==2:
        #     self.data_grabed_signal.emit([DataFromPlugins(name='Picam',
        #                                                   data=[frame[0],frame[1]],
        #                                                   dim='Data1D',
        #                                                   labels=['up half','down half']
        #
        #                                                   )])
        # elif frame.shape[0]==1:
        #     self.data_grabed_signal.emit([DataFromPlugins(name='Picam',
        #                                                   data=[frame],
        #                                                   dim='Data1D',
        #                                                   labels=['spectrum']
        #                                                   )])


    def callback(self):
        """optional asynchrone method called when the detector has finished its acquisition of data"""
        raise NotImplementedError


    def stop(self):
        # pass
        # ## TODO for your custom plugin
        # self.controller.your_method_to_stop_acquisition()
        # self.emit_status(ThreadCommand('Update_Status', ['Some info you want to log']))
        #############################
        self.controller.stop_acquisition()
        self.controller.clear_acquisition()
        self._toggle_non_online_parameters(enabled=True)
        return ''


if __name__ == '__main__':
    main(__file__)