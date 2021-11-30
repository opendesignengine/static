"""REST Serial - client class to map REST style API to serial protocols.

TODO
    Add info on mapping, examples, and requirements on the serial protocols.
"""

import serial
from serial.tools import list_ports
from collections import deque
import json
import threading
from uuid import uuid4

class RestSerialDevice:
    def __init__(self):
        self.device = serial.Serial()
        self.lock = threading.RLock()
        self.data = deque([])

    def sendCommand(self, cmd):
        return self.device.write(cmd.encode('utf-8'))

    def readResultLine(self):
        return self.device.readline().decode("utf-8").strip()

    def connected(self):
        # check to see if we think the com port is connected
        if self.device.is_open:
            try:
                # then check to see if we can actually talk to device
                temp = self.device.in_waiting
            except serial.serialutil.SerialException as e:
                # if not, then close the device
                disconnect()

        # either way, is_open is now the true state of the device
        return self.device.is_open

    def readData(self, messageId=None):
        with self.lock:
            result = None
            while (self.connected() and self.device.in_waiting):
                tempResult = self.readResultLine()
                if (tempResult):
                    tempResultJson = json.loads(tempResult)
                    if ('Error' in tempResultJson):
                        result = tempResult
                    if (messageId and ('messageId' in tempResultJson)
                        and (tempResultJson['messageId'] == messageId)):
                        result = tempResult
                    self.data.append(tempResult)

            # return None if we did not read a result matching the messageId
            return result

    def popData(self):
        with self.lock:
            if (len(self.data)):
                return self.data.popleft()
            return None

    def execCommand(self, cmd):
        with self.lock:
            messageId = ""
            if ('messageId' in cmd):
                messageId = cmd['messageId']
            else:
                messageId = uuid4().hex
                cmd['messageId'] = messageId

            self.sendCommand(json.dumps(cmd))

            # wait for the result to come back
            result = None
            while not(result):
                result = self.readData(messageId)

            return result

    def findDevicePort(self):
        comPorts = list_ports.comports()
        for comPort in comPorts:
            vid = format(comPort.vid, 'X')
            pid = format(comPort.pid, 'X')

            # check for Alpha Controller (aka - Adafruit Feather 324u)
            deviceIdCheck = self.checkDeviceId(vid, pid)
            if deviceIdCheck:
                deviceIdCheck['comPort'] = comPort.device
                return deviceIdCheck

        # we iterated over all available com ports and did not find device
        return None

    def checkDeviceId(self, vid, pid):
        """Override this method to provide expected version data from device
        based on USB VID/PID pair.  VID and PID are formatted as upper case hex
        values without leading 0x (e.g. 0x1234 is 1234)."""
        return None

    def connect(self):
        devicePortInfo = self.findDevicePort()
        if not(devicePortInfo):
            return False  # no appropriate devices connected to USB

        self.device.port = devicePortInfo['comPort']
        try:
            self.device.open()
            ready = self.checkDeviceInfo(devicePortInfo)
            if not ready:
                self.disconnect()
            return ready

        except serial.serialutil.SerialException as e:
            return False  # device not accessible

    def checkDeviceInfo(self, devicePortInfo):
        """Override this method to provide to verify expect version info and
        perform other application specific initialization.

        Note:
            Do not disconnect on error in this method."""
        return False

    def disconnect():
        self.device.close()
        self.device.port = None
