pymodaq_plugins_princeton_instruments (Princeton Instruments Cameras)
###################################################################

PyMoDAQ plugin for Princeton Instruments Cameras. Relies on Alexey Shkarin's pylablib hardware control libraries.

Note that the picam library produced by Princeton Instruments has to be installed (freely downloadable at https://www.princetoninstruments.com/products/software-family/pi-cam ).
pylablib should also be able to find it (for instructions, see: https://pylablib.readthedocs.io/en/latest/devices/Picam.html#cameras-picam )

Authors
=======

* Nicolas Tappy

Instruments
===========
Tested on PYLon BR eXcelon cameras

Viewer2D
++++++++

* **PYLon**: Control of a PYLon camera using the picam library.
