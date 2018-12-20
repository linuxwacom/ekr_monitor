# Express Key Remote Monitor

This repository houses a Python script that can be run in the background 
to monitor for Express Key Remote (EKR) mode switch events. When a mode 
switch event occurs, the script will run `xsetwacom` to re-configure the 
EKR based on the settings stored in the monitor's conf file.

It also includes a small C program to fix permissions on the "remote_mode"
sysfs nodes as new EKRs are connected to the system or paired to the dongle.
This program (unfortunately) must run as root in order to add global read
permission to the nodes.

## TODO

 * Support reading the LED sysfs nodes that are provided in later kernel
   versions. These nodes are already world-readable, and so don't rely 
   on the `ekr_fixperm` program.
