pymodaq_plugins_princeton_instruments (Princeton Instruments Cameras)
#####################################################################

PyMoDAQ plugin for Princeton Instruments Cameras. Relies on Alexey Shkarin's pylablib hardware control python module.

The picam library produced by Princeton Instruments has to be installed to use this plugin (freely downloadable at https://www.princetoninstruments.com/products/software-family/pi-cam).

If pylablib is not able to find the existing picam installation (.dll file), it is easy to solve. See: https://pylablib.readthedocs.io/en/latest/devices/Picam.html#cameras-picam)

You can help in the development of this plugin by testing it with your hardware and reporting issues and successes in this repository. I will update the list of tested hardware hardware accordingly.

Authors
=======

* Nicolas Tappy

Instruments
===========
Should support all cameras using picam through adaptative parameters parsing.

Tested on Princeton Instrument PYLon BR eXcelon cameras.

Viewer2D
++++++++

* **picam**: Control of cameras using the picam library.
