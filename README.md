# ExpressKey Remote Monitor

The ExpressKey Remote Monitor allows Linux users to make use of the 
"mode toggle button" on their [Wacom ExpressKey Remote](https://101.wacom.com/UserHelp/en/TOC/EKR-100.html) 
(EKR). It runs in the background, automatically applying a new "xsetwacom"
configuration whenever the button is pressed. This program is useful for 
Linux users who don't otherwise have a way to configure the ExpressKey 
Remote's multiple modes through their preferred control panel.


## Quick Start

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


## Installation

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


## Configuration

The program looks for configuration files at `/etc/ekr_monitor.conf` and 
`~/.ekr_monitor.conf`. If both files are present their settings will be 
merged, giving priority to the latter.

The configuration file primarily consists of three sections (one for each 
of the available modes) with settings for each of the 18 buttons and two 
Touch Ring directions. It looks like this:

~~~ini
[mode_0]
ring_ccw = key CTRL -
ring_cw = key CTRL SHIFT +
button_1 = key a
button_2 = key b
...

[mode_1]
...

[mode_2]
...
~~~

The settings associated with each value (e.g. `key CTRL -`) are "action 
mappings" passed to the "xsetwacom" command. See `man xsetwacom(1)` for 
specific information, but "key", "button", "modetoggle", and "pan" may 
all be possible allowed actions. Be sure to include the "SHIFT" key in 
the action mapping if necessary. For example, "+" on most keyboards requires 
use of the shift key, so `key CTRL +` would not work as expected -- you 
would need to use `key CTRL SHIFT +` instead.

A "sleep" configuration option under the "general" section is also available.
This option defines the polling interval (in seconds) that is used when reading 
the current EKR mode state. A larger value will require fewer resources but 
will result in a larger delay between switching the mode and the program 
applying the actions. The default value should not have a noticible impact on 
performance and have a very minimal delay.


## Todo

 * Support reading the LED sysfs nodes that are provided in later kernel
   versions. These nodes are already world-readable, and so don't rely 
   on the `ekr_fixperm` program.

  * Support reading mode switches for other Wacom models (e.g. Intuos Pro, 
    Cintiq 24HD, etc.)
