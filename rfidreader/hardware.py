"""
This module provides an interface to the SL030 RFID module.

Adapted from https://github.com/molnarg/SL030.py/blob/master/SL030.py.
"""

# The MIT License
#
# Copyright (C) 2013 Gabor Molnar <gabor@molnar.es>
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# 'Software'), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import fcntl
import io
import os.path
import select
import time

# I2C_SLAVE constant from i2c-tools-3.1.0/include/linux/i2c-dev.h
I2C_SLAVE = 0x0703

class RFIDReader(object):
    """
    Interface to the SL030 RFID module.
    """

    # Sleep and wake command codes.
    COMMAND_SLEEP = 0x01

    # Success response code.
    STATUS_SUCCESS = 0x00

    def __init__(self, bus, address, detect=None, wake=None):
        """
        Initialise a new RFID reader.

        :param bus: I2C bus of the reader.
        :param address: I2C address of the reader.
        :param detect: whether to detect the reader through GPIO.
        :param wake: whether to wake the reader on connect.
        """
        # Open the I2C device file.
        self.bus = io.FileIO("/dev/i2c-{}".format(bus), "r+")
        # Specify the address of the slave.
        error = fcntl.ioctl(self.bus, I2C_SLAVE, address)
        if error is not None:
            raise RuntimeError("Couldn't set the slave address:", error)
        # Enable GPIO detection if specified.
        self.pin_detect = None
        if detect is not None:
            try:
                export = open("/sys/class/gpio/export", "w")
                export.write(str(detect))
                export.close()
            except:
                print("Couldn't export detection pin")
            gpio_root = "/sys/class/gpio/gpio{}".format(detect)
            open(os.path.join(gpio_root, "direction"), "w").write("in")
            open(os.path.join(gpio_root, "edge"), "w").write("falling")
            self.pin_detect = open(os.path.join(gpio_root, "value"), "r")
        # Enable GPIO wake-up if specified.
        self.pin_wake = None
        if wake is not None:
            try:
                export = open("/sys/class/gpio/export", "w")
                export.write(str(wake))
                export.close()
            except:
                print("Couldn't export wake pin")
            gpio_root = "/sys/class/gpio/gpio{}".format(wake)
            open(os.path.join(gpio_root, "direction"), "w").write("out")
            self.pin_wake = open(os.path.join(gpio_root, "value"), "w")
            self.pin_wake.write("1")

    def read(self):
        """
        Return a response from the RFID reader.
        """
        # Read the response and length prefix
        response = self.bus.read(256)
        length = ord(response[0])
        # Clean the response by ignoring the MSB
        clean = ''.join(map(chr, map(lambda c: c & 127, map(ord, response))))
        # Extract and return the fields from the response
        command = ord(clean[1])
        status = ord(clean[2])
        data = clean[3:length+1]
        return command, status, data

    def write(self, command, data=''):
        """
        Send a command to the RFID reader.

        :param command: command code.
        :param data: command payload.
        """
        length = 1 + len(data)
        if length > 255:
            raise ValueError("Data must be shorter than 254 bytes")
        if not (0 <= command <= 255):
            raise ValueError("Invalid command")
        self.bus.write(chr(length) + chr(command) + data)

    def transaction(self, command, data=''):
        """
        Send a command and read a response from the RFID reader.

        :param command: command code.
        :param data: command payload.
        """
        self.write(command, data)
        time.sleep(0.1)
        response_command, status, data = self.read()
        if response_command != command:
            raise RuntimeError("Response to invalid command in transaction")
        return status, data

    def sleep(self):
        """
        Send the reader to sleep.
        """
        self.write(RFIDReader.COMMAND_SLEEP)

    def wake(self):
        """
        Wake the reader.
        """
        self.pin_wake.write('1')
        time.sleep(0.1)
        self.pin_wake.write('0')

    def select(self):
        """
        Select information from a presented card.
        """
        status, data = self.transaction(RFIDReader.COMMAND_SELECT)
        if status != RFIDReader.STATUS_SUCCESS:
            return None
        length = len(data)
        return ord(data[length-1]), data[:length-1]

    def poll(self):
        """
        Poll for a change in selection status.
        """
        self.pin_detect.read()
        poll = select.epoll()
        poll.register(self.pin_detect, select.EPOLLPRI)
        poll.poll()
        return self.select()
