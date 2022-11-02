import serial
from serial.tools import list_ports
from collections import deque
import json
import threading
from uuid import uuid4

class QueuedJsonSerialDevice:

    """QueuedJsonSerialDevice is a base class for building serial device classes
    which communicate with the underlying serial device using JSON messages and
    which have a reply message queue to capture event messages emitted by the
    serial device.  ArduninoJson (https://arduinojson.org/) can be helpful
    in handling and returning JSON messages from Arduino and compatible boards.

    There are three requirements on the JSON messages used between sub-classes
    and the attached devices.
        1. All messages going to/coming from the device must include a "messageId"
        field.  It may be a blank string, but if the inbound messageId is not
        blank, then the reply from the device to that specific message must include
        the same messageId value to allow the class to match the reply to the
        sent message.  This requirement includes error messages discussed below.

        Note, the execCommand() method will generate and insert a uuid as the
        messageId if one is not provided.

        2. Errors from the device should be reported back to the class in a
        field labeled "Error".

        3. The device must reply with a message back for every message sent to it

    You must sub-class this class to use it.  The sub-class must override two
    methods:  _checkDeviceId() and _checkDeviceInfo().  The first method is intended
    to give sub-classes the ability to filter by USB VID/PID and to provide data
    for later validation during the _checkDeviceInfo() method.  This two step
    approach to filtering and valitdating the device limits communication with
    devices which are not expecting the target messages.  Additionally, the
    subclass may set the serial device connection settings (e.g. baudrate, bytesize)
    in its __init__() method.

    Once the sub-class has been written the QueuedJsonSerialDevice has a straight
    forward pattern of use.
        1. Instantiate an object of type QueuedJsonSerialDevice-sub-class
        2. Call the connect() method to look for, connect to, and validate the
        serial device
        3. Call execCommand() to send a message to the device and get its direct
        reply in a single message
        4. call disconnect() when done to close the serial connection to the device

        Optionally
        * Use readData() to ensure all data has been read from the serial buffer
        (should be called until it returns None) into the data queue
        * Use popData() to pop the front message in the queue
        * Use connected() to test if the serial connection to the device is alive
        and open

    Example Usage
        The MyLedBlinker class below connects to Arduino Unos which support three
        commands sent in a JSON object with messageId and command fields.
            * name - returns the string "LED Blinker" to identify the Arduino is
            the one we are looking for.
            * blinkOn - starts the LED Blinker's LED blinking
            * blinkOff - stops the LED Blinker's LED blinking

        class MyLedBlinker(jsonserial.QueuedJsonSerialDevice):
            def __init__(self):
                super().__init__()
                self.device.baudrate = 115200
                self.device.bytesize = serial.EIGHTBITS
                self.device.parity = serial.PARITY_NONE
                self.device.stopbits = serial.STOPBITS_ONE

            def _checkDeviceId(self, vid, pid):
                if (vid == '2341' and pid == '0001'):
                    return { 'expectedName': 'LED Blinker' }

                return None

            def _checkDeviceInfo(self, devicePortInfo):
                deviceResults = json.loads(self.execCommand({"command":"name"}))

                # check for errors
                if ('Error' in deviceResults):
                    print('Error: %s' % deviceResults['Error'])
                    return False

                # check result, is this Holoseat?
                if (deviceResults['name'] != devicePortInfo['expectedName']):
                    return False

        # use MyLedBlinker
        blinker = MyLedBlinker() # returns true if connected
        blinker.execCommand({"command":"blinkOn"}) # blinking starts
        blinker.execCommand({"command":"blinkOff"}) # blinking stops
        blinker.disconnect() # done with blinker

    """

    def __init__(self):
        """Initialize the serial device object from serial package, an RLock in
        for thread safety around the queue, and a deque for efficient left pops."""
        self.device = serial.Serial()
        self.lock = threading.RLock()
        self.data = deque([])

    def connected(self):
        """Returns True if the device is open and alive (liveness is verified by
        testing for data in the in_waiting property which will throw a
        SerialException if the connection is not alive).  If the connection is
        not alive then it is closed with disconnect to sync the is_open property
        with the liveness."""
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
        """Optional argument: messageId to ensure we return the result matching
        the messageId

        Reads data from serial device into data queue until there is no data waiting
        on the serial connection.  Then returns the message with the first Error
        encountered or that matches the optional messageId when provided."""
        with self.lock:
            result = None
            while (self.connected() and self.device.in_waiting):
                tempResult = self.device.readline().decode("utf-8").strip()
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
        """Pops the the first message in the data queue and returns it or returns
        None if the data queue is empty."""
        with self.lock:
            if (len(self.data)):
                return self.data.popleft()
            return None

    def execCommand(self, cmd):
        """Sends the message cmd to the device, waits for the device to reply, and
        then returns the response from the device.  The cmd should be a Python
        dictionary and it may include the messageId.  If messageId is not included,
        one will be generated by this method."""
        with self.lock:
            messageId = ""
            if ('messageId' in cmd):
                messageId = cmd['messageId']
            else:
                messageId = uuid4().hex
                cmd['messageId'] = messageId

            self.device.write(json.dumps(cmd).encode('utf-8'))

            # wait for the result to come back
            result = None
            while not(result):
                result = self.readData(messageId)

            return result

    def connect(self):
        """Looks for the device (by calling _findDevicePort()) and connects to it
        (calling _checkDeviceInfo() to validate the device is the one we want to
        connect to)."""
        devicePortInfo = self._findDevicePort()
        if not(devicePortInfo):
            return False  # no appropriate devices connected to USB

        self.device.port = devicePortInfo['comPort']
        try:
            self.device.open()
            ready = self._checkDeviceInfo(devicePortInfo)
            if not ready:
                self.disconnect()
            return ready

        except serial.serialutil.SerialException as e:
            return False  # device not accessible

    def disconnect():
        """Closes the serial connection to the device."""
        self.device.close()
        self.device.port = None

    def _findDevicePort(self):
        """Iterates over all available serial devices looking for matching VID/PID
        based on calling _checkDeviceId()"""
        comPorts = list_ports.comports()
        for comPort in comPorts:
            vid = format(comPort.vid, 'X')
            pid = format(comPort.pid, 'X')

            # check for Alpha Controller (aka - Adafruit Feather 324u)
            deviceIdCheck = self._checkDeviceId(vid, pid)
            if deviceIdCheck:
                deviceIdCheck['comPort'] = comPort.device
                return deviceIdCheck

        # we iterated over all available com ports and did not find device
        return None

    def _checkDeviceId(self, vid, pid):
        """Override this method to provide expected version data from device
        based on USB VID/PID pair.  VID and PID are formatted as upper case hex
        values without leading 0x (e.g. 0x1234 is 1234)."""
        return None

    def _checkDeviceInfo(self, devicePortInfo):
        """Override this method to provide to verify expect version info and
        perform other application specific initialization.

        Note:
            Do not disconnect on error in this method, just return False."""
        return False
