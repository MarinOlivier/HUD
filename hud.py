#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2014-18 Richard Hull and contributors
# See LICENSE.rst for details.
# PYTHON_ARGCOMPLETE_OK

from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from PIL import ImageFont

import threading
import time
import bluetooth
import json

serial = i2c(port=1, address=0x3C)
font = ImageFont.truetype("./fonts/coolvetica_comp.ttf", 40)
device = ssd1306(serial, rotate=2)
threads = []
uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"
exit = 0


# Bluetooth communication thread
class ComThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)

    def __del__(self):
        print("Exiting comThread")

    def run(self):
        print("Starting comThread")
        self.wait4connect()
        self.print()


    def wait4connect(self):
        self.server_sock.bind(("", bluetooth.PORT_ANY))
        self.server_sock.listen(1)
        port = self.server_sock.getsockname()[1]

        bluetooth.advertise_service(self.server_sock, "GPSNausoreServer", service_id=uuid,
                                    service_classes=[uuid, bluetooth.SERIAL_PORT_CLASS],
                                    profiles=[bluetooth.SERIAL_PORT_PROFILE])

        # TODO: Other client still connect after that...
        print("Waiting for connection on RFCOMM channel", port)
        self.client_sock, self.client_info = self.server_sock.accept()
        print("Accepted connection from", self.client_info)

    def print(self):
        try:
            while True:
                data = self.client_sock.recv(4096)
                if data.decode() == "CMD_DISCONNECT":
                    self.disconnect()
                else:
                    instruction = Instruction(data)
                    DisplayThread.write(self, instruction.distanceRemaining)
        except OSError:
            pass

    def disconnect(self):
        global exit
        print("Disconnected.")
        self.client_sock.close()
        self.server_sock.close()
        exit = 1
        print("All done.")

class Instruction():
    def __init__(self, instruction):
        self.d = json.loads(instruction.decode())
        print(self.d)
        self.distanceRemaining = str(self.d["distance"])
        self.instructionString = self.d["instruction"]
        self.type = self.d["type"]
        self.modifier = self.d["modifier"]
        self.exit = self.d["exit"]

    def __del__(self):
        print("Destroy Instruction")


class DisplayThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def __del__(self):
        print("Exiting displayThread")


    def run(self):
        print("Starting displayThread")
        self.write("Hello")

    def decode(self, instruction):
        pass

    def write(self, instruction):
        # Box and text rendered in portrait mode
        with canvas(device) as draw:
            text = instruction

            w, h = draw.textsize(text, font=font)
            left = (device.width - w) / 2
            top = (device.height - h) / 2
            draw.text((left, top), text, fill="white", font=font)


if __name__ == '__main__':
    try:
        # Create new threads
        comThread = ComThread()
        dispThread = DisplayThread()

        # Start new Threads
        comThread.start()
        dispThread.start()

        # Add threads to thread list
        threads.append(comThread)
        threads.append(dispThread)

        while not exit:
            pass

        # Wait for all threads to complete
        for t in threads:
            t.join()
        print("Exiting Main Thread")
    except Exception as e:
        print(e)
        print("Error: unable to start thread")
