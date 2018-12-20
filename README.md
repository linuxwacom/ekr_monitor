# Express Key Remote Monitor

This repository houses a Python script that can be run in the background 
to monitor for Express Key Remote (EKR) mode switch events. When a mode 
switch event occurs, the script will run `xsetwacom` to re-configure the 
EKR based on the settings stored in the monitor's conf file.


## QUICK START

The following set of commands will get the program up and running with minimal 
fuss, suitable for evaluation or development. See the "Installation" section 
below for the correct way to deploy this program onto end-user systems.

    $ cp ekr_monitor.conf ~/.ekr_monitor.conf
    $ sudo chmod +x ekr_monitor.py
    $ sudo ekr_monitor.py

The unmodified configuration file is set up for use with Krita. Feel free to 
change the configuration to meet your needs. Information on the configuration 
file format can be found in the "Configuration" section below. Note that you 
will need to restart the `ekr_monitor.py` script after making any changes.


## INSTALLATION

1. Compile and install the permission-fixing daemon

       $ gcc ekr_fixperm.c -o ekr_fixperm
       $ chmod +x ekr_fixperm
       $ sudo cp ekr_fixperm /usr/bin

2. Install the EKR monitor script

       $ sudo cp ekr_monitor.py /usr/bin

3. Add a default system-wide configuration

       $ sudo cp ekr_monitor.conf /etc

4. Setup the programs to run automatically.

   * The `ekr_fixperm` daemon should be run on startup as root. This 
     can be done via an `/etc/init.d` script or a systemd system unit.

   * The `ekr_monitor.py` script should be run as the local user when 
     they start an Xorg session. This can be done by adding a call inside 
     `~/.xinitrc`, adding a call inside the global `/etc/X11/xinit/xinitrc`
     (so the script runs for all users automatically), or through a 
     desktop-specific mechanism.


## CONFIGURATION

The program looks for configuration files at `/etc/ekr_monitor.conf` and 
`~/.ekr_monitor.conf`. If both files are present their settings will be 
merged, giving priority to the latter.


## TODO

 * Support reading the LED sysfs nodes that are provided in later kernel
   versions. These nodes are already world-readable, and so don't rely 
   on the `ekr_fixperm` program.

  * Support reading mode switches for other Wacom models (e.g. Intuos Pro, 
    Cintiq 24HD, etc.)
