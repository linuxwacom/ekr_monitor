#!/usr/bin/env python2

"""
Monitor the system for newly-attached Express Key Remote devices and
their mode change events.

The Express Key Remote (EKR) is an accessory for Wacom tablets that
appears to the system as a "pad-only" tablet that contains a number
of hardware buttons ("ExpressKeys") and a touch-sensitive jog dial
("Touch Ring"). The EKR also includes a special "mode switch" button
which cycles through a bank of LEDs that indicate the remote's current
mode.

The mode switch is used by the Windows and OSX drivers to allow the
definition of multiple Touch Ring behaviors. For instance, the Touch
Ring may send scroll/zoom events in the first mode, commands to change
the brush size in the second, and rotate the canvas in the third. The
Linux drivers, on the other hand, leave the job of acting on mode
switch events to userspace daemons.

This program is one such daemon, periodically polling sysfs for newly-
attached Express Key Remote devices and mode switch events. When such
an event occurs, the `xsetwacom` command is called to configure the
buttons and Touch Ring according to this program's configuration files.

This program does not take any arguments. The following paths are
searched for configuration files:

  * /etc/ekr_monitor.conf
  * ~/.ekr_monitor.conf

If multiple configuration files are present, preferences in the later
files will take precedence.
"""

from __future__ import print_function

__license__ = "GPL3"
__copyright__ = "Copyright 2018 by Jason Gerecke, Wacom."
__author__ = "Jason Gerecke <jason.gerecke@wacom.com>"

import glob
import os
import time
import shlex
import ConfigParser
from subprocess import Popen, PIPE
from sys import stderr

CONFIGFILES = ["/etc/ekr_monitor.conf",
               os.path.expanduser("~/.ekr_monitor.conf")]

REMOTE_SYSFS_GLOB = "/sys/module/*wacom/drivers/*/*/wacom_remote/*/remote_mode"


class Remote(object):
    """
    Representation of an Express Key Remote for tracking and applying
    mode switch operations.

    This class stores information about a Remote's current mode and
    the commands that should be executed when the mode changes. It
    also provides a few helper functions for e.g. locating paths to
    provide to the constructor and reformatting command strings into
    the expected format.
    """

    mode_dev = None
    event_dev = None
    x11_dev = None

    mode = None
    mode_commands = {}

    def __init__(self, mode_dev):
        """
        Create a new object representing an Express Key Remote.
        """
        print("Creating Remote for {0}".format(mode_dev))
        self.mode_dev = mode_dev
        self.event_dev = Remote._find_event_dev(self.mode_dev)
        self.x11_dev = Remote._find_x11_dev(self.event_dev)

    def set_mode_commands(self, mode, commands):
        """
        Define the list of commands that should be run for a given mode.

        After creating a Remote, this method should be called
        to specify the commands that should be run when entering
        a given mode. The available mode numbers are defined by
        the hardware (e.g. 0 through 2 for the Express Key Remote).
        Commands associated with an unknown mode will never be
        executed.

        Commands should be provided as a list of lists. Each
        list item represents a separate command that will be
        executed, and should itself be a list of arguments.
        These arguments will be added to the command `xsetwacom
        set <id>`, so those items should be omitted. The
        `split commands` static method can be used to convert
        a list of commands in string format to a form appropriate
        for this method.

        For example, to set the third button to press CTRL+Z and
        the fourth button to press the 'a' key, the following
        call could be made:

        ~~~
        set_mode_commands(1, [["button", "3", "key", "CTRL", "z"],
                ["button", "4", "key", "a"]])
        ~~~

        The above command will result in the following set of
        program executions when mode 1 is entered (automatically
        replacing the <id> as appropriate):

        ~~~
        xsetwacom set <id> button 3 key CTRL k
        xsetwacom set <id> button 4 MaptToOutput next
        ~~~

        Paramters:
        mode(int): The mode number that the program should run the
            provided commands upon becoming active.

        commands(list): A list of commands to be run when the
            specified mode becomes active. Each command in the
            list must itself be a list of individual arguments.
        """
        cmds = []
        for command in commands:
            cmd = ["xsetwacom", "set", self.x11_dev]
            cmd.extend(command)
            cmds.append(cmd)
        self.mode_commands[mode] = cmds

    def poll(self):
        """
        Check the remote's current mode and execute the associated commands.

        This method should be called periodically to ensure that
        mode toggle events are acted on in a timely manner. The
        current mode will be checked, and if it is different from
        the previous call to `poll`, then the commands associated
        with the new mode will be executed.
        """
        update_required = self._update_mode()
        if update_required is None:
            return False

        if update_required:
            self._run_commands()
        return True

    @staticmethod
    def split_commands(commands):
        """
        Split a newline-seperated string of commands into parameters.

        This method is provided as a convenience to avoid having to
        manually split simple command strings into the argument array
        format that is required by `set_mode_commands`. Each line is
        considered an independet command. The `shlex` module is used
        to ensure quoted arguments are kept together similar to how
        the shell would interpret it.

        Parameters:
        commands (string):
            Newline-separated string of zero or more commands to split.
        """
        commands = [x.strip() for x in commands.splitlines()]
        commands = [x for x in commands if len(x) > 0]
        cmds = []
        for command in commands:
            cmds.append(shlex.split(command))
        return cmds

    @staticmethod
    def search_for_remote_mode_devs():
        """
        Find mode indicator devices present in the system.

        Search the sysfs filesystem for mode indicator devices that
        can be passed into the constructor of this class.
        """
        return glob.glob(REMOTE_SYSFS_GLOB)

    def _update_mode(self):
        try:
            with open(self.mode_dev, 'r') as f:
                current_mode = f.read()
            current_mode = int(current_mode)
        except (IOError, ValueError) as err:
            print(err, file=stderr)
            return None

        changed = current_mode != self.mode
        self.mode = current_mode
        return changed

    def _run_commands(self):
        if self.mode < 0:
            return

        #print("Running commands for mode {0}".format(self.mode))
        if self.mode not in self.mode_commands:
            return

        for command in self.mode_commands[self.mode]:
            #print("\t{0}".format(command))
            Popen(command).wait()

    @staticmethod
    def _find_event_dev(mode_path):
        event_glob = mode_path[:-len("remote_mode")] + "../../input/*/event*"
        event_path = glob.glob(event_glob)[0]
        event_name = os.path.basename(os.path.normpath(event_path))
        return "/dev/input/{0}".format(event_name)

    @staticmethod
    def _find_x11_dev(event_path):
        results = []

        devices = Remote._list_x_devices()
        for devid in devices.keys():
            xid, name = devid
            if "Express Key Remote" not in name:
                continue

            props = devices[devid]
            for key in props.keys():
                if not key.startswith("Device Node"):
                    continue

                node = props[key].replace('"', '')
                if node == event_path:
                    results.append(xid)

        if len(results) > 0:
            return results[0]
        return ""

    @staticmethod
    def _list_x_devices():
        x_devices = {}

        process = Popen(["xinput", "list", "--id-only"], stdout=PIPE)
        stdout = process.communicate()[0]

        for xid in stdout.splitlines():
            if xid.startswith("~"):
                print("Ignoring floating device {0}".format(xid), file=stderr)
                continue

            process = Popen(["xinput", "list-props", xid], stdout=PIPE)
            stdout = process.communicate()[0]
            name = ""
            props = {}

            for line in stdout.splitlines():
                if not line.startswith("\t"):
                    prefixlen = len("Device '")
                    suffixlen = len("':")
                    name = line[prefixlen:-suffixlen]
                else:
                    key, value = line.strip().split("\t")
                    props[key] = value

            x_devices[(xid, name)] = props

        return x_devices


REMOTES = []
CONFIG = None


def _build_commands(option, command_text):
    commands = Remote.split_commands(command_text)

    prefix = option
    suffix = ""
    if "_" in option:
        prefix, suffix = option.split("_", 1)

    prepend_args = []

    if prefix == "button":
        button = int(suffix)
        if button > 3:  # Skip over inaccessible range
            button += 4
        prepend_args = ["button", str(button)]
    elif prefix == "ring":
        if suffix == "cw":
            prepend_args = ["AbsWheelDown"]
        elif suffix == "ccw":
            prepend_args = ["AbsWheelUp"]
        else:
            raise ValueError("Unknown ring suffix {0}".format(suffix))

    commands = [prepend_args + x for x in commands]
    return commands


def _configure(remote):
    for i in range(0, 3):
        section = "mode_{0}".format(i)
        commands = []

        try:
            options = CONFIG.items(section)

            for option, value in options:
                try:
                    cmds = _build_commands(option, value)
                    commands.extend(cmds)
                except ValueError:
                    print("Ignoring option '{0}' in section '{1}'".format(
                          option, section), file=stderr)

            #print(commands)
            remote.set_mode_commands(i, commands)

        except ConfigParser.NoSectionError:
            print("Unable to find section '{0}' in config file".format(
                  section), file=stderr)
            continue


def _mainloop():
    for path in Remote.search_for_remote_mode_devs():
        hits = [x for x in REMOTES if x.mode_dev == path]
        if len(hits) > 0:
            remote = hits[0]
        else:
            remote = Remote(path)
            REMOTES.append(remote)
            _configure(remote)

        if not remote.poll():
            print("Unable to update mode for '{0}'".format(
                  remote.mode_dev), file=stderr)
            REMOTES.remove(remote)


def _main():
    global CONFIG

    CONFIG = ConfigParser.RawConfigParser()
    CONFIG.read(CONFIGFILES)

    try:
        sleep_seconds = CONFIG.getfloat("general", "sleep")
    except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
        sleep_seconds = 0.1

    while True:
        _mainloop()
        time.sleep(sleep_seconds)


if __name__ == "__main__":
    _main()