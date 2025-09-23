# MKS-MFC-Multiple-Controller
MKS MFC Multiple Controller - Using Python, provided with a Graphical User Interface (GUI)

<p align="center">
  <img width="400" height="300" alt="image" src="https://github.com/user-attachments/assets/c2b1a884-ac4f-45c7-be1f-0d353b56a6fb" />
</p>

*** The MFC must be manually set up as Modbus protocol, available after going to configuration page of each MFC. ***

pymodbus must be downloaded by executing the command "pip install pymodbus==3.6.9" on your computer.

Ethernet port must be set up to be manual

Open Control Center -> Network and Internet -> Network and Sharing center

Go to the ethernet connection, click on Properties

Under "Internet Protocol Version 4 (TCP/IPv4)", hit Properties.

Click on "Use the following IP address" and type in

IP Address: 192.168.0.10

Subnet mask: 255.255.0.0

Change the parameter NUMBER OF CONTROLLERS to desired number of MFCs to control.

---PERFORM THE STEPS ABOVE OR IT WILL NOT WORK---

Runs on Python version 3.8.

Newer versions of pymodbus doesn't seem to work (3.8.x or newer)

Resource of ModBus is based on this: https://www.mks.com/medias/sys_master/resources/hb3/h6f/9954678341662/C-SeriesMFC-Modbus-Register-Map-Specification/C-SeriesMFC-Modbus-Register-Map-Specification.pdf

Seems to work with G-series as well.

Communicates with MKS MFC Using ModBUS protocol.
Tested on versions MKS MFC firmware version 0.0.7 and 1.1.2
