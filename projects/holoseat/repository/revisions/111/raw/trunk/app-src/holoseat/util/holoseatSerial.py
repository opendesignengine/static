from holoseat.util import jsonserial
import serial
import json

class holoseatSerialDevice(jsonserial.QueuedJsonSerialDevice):
    def __init__(self):
        super().__init__()
        self.device.baudrate = 115200
        self.device.bytesize = serial.EIGHTBITS
        self.device.parity = serial.PARITY_NONE
        self.device.stopbits = serial.STOPBITS_ONE
        self.device.timeout = 5 # 5 second timeout for comms with Holoseat

    def _checkDeviceId(self, vid, pid):
        # check for Alpha Controller (aka - Adafruit Feather 324u)
        if (vid == '239A' and pid == '800C'):
            return { 'expectedHwVer' : ['v0.4'],
                     'expectedDevice': 'Holoseat Alpha' }

        # check for v1.0+ (aka Holoseat vid/pid)
        if (vid == '1209' and pid == 'B058'):
            return { 'expectedHwVer' : ['v1.0'],
                     'expectedDevice' : 'Holoseat' }

        # no valid device, return None
        return None

    def _checkDeviceInfo(self, devicePortInfo):
        # get device name
        deviceResults = json.loads(self.execCommand({"uri":"/main/devicename","verb":"GET"}))

        # check for errors
        if ('Error' in deviceResults):
            print('Error: %s' % deviceResults['Error'])
            return False

        # check result, is this Holoseat?
        if (deviceResults['deviceName'] != devicePortInfo['expectedDevice']):
            return False

        # retrieve version info
        versionResults = json.loads(self.execCommand({"uri":"/main/version","verb":"GET"}))

        # check for errors
        if ('Error' in versionResults):
            print('Error: %s' % versionResults['Error'])
            return False

        # is this the expected HW version?
        if not(versionResults['hwVer'] in devicePortInfo['expectedHwVer']):
            return False

        # TODO - is this a compatible FW version?

        # TODO - is this the compatible HSP version?

        # tell holoseat to echo out all status events to sync up any connected clients
        eventsResults = json.loads(self.execCommand({"uri":"/lowlevel/events","verb":"GET"}))
        if ('Error' in eventsResults):
            print('Error: %s' % eventsResults['Error'])
            return False

        # passed all tests, we can talk to this Holoseat
        return True
