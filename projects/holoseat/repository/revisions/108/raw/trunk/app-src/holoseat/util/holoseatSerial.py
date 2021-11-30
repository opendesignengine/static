import serial
from serial.tools import list_ports
from collections import deque
import json
import threading
from uuid import uuid4

# set up the serial port for Holoseat comms
holoseat = serial.Serial()
holoseat.baudrate = 115200
holoseat.bytesize = serial.EIGHTBITS
holoseat.parity = serial.PARITY_NONE
holoseat.stopbits = serial.STOPBITS_ONE
holoseat.timeout = 5 # 5 second timeout for comms with Holoseat

# data queue objects
lock = threading.RLock()
data = deque([])

def sendCommand(cmd):
    return holoseat.write(cmd.encode('utf-8'))

def readResultLine():
    return holoseat.readline().decode("utf-8").strip()

def connected():
    # check to see if we think the com port is connected
    if holoseat.is_open:
        try:
            # then check to see if we can actually talk to holoseat
            temp = holoseat.in_waiting
        except serial.serialutil.SerialException as e:
            # if not, then close the connection
            disconnect()

    # either way, is_open is now the true state of the connection
    return holoseat.is_open

def readData(messageId=None):
    with lock:
        result = None
        while (connected() and holoseat.in_waiting):
            tempResult = readResultLine()
            if (tempResult):
                tempResultJson = json.loads(tempResult)
                if ('Error' in tempResultJson):
                    result = tempResult
                if (messageId and ('messageId' in tempResultJson)
                    and (tempResultJson['messageId'] == messageId)):
                    result = tempResult
                data.append(tempResult)

        # return None if we did not read a result matching the messageId
        return result

def popData():
    with lock:
        if (len(data)):
            return data.popleft()
        return None

def execCommand(cmd):
    with lock:
        messageId = ""
        if ('messageId' in cmd):
            messageId = cmd['messageId']
        else:
            messageId = uuid4().hex
            cmd['messageId'] = messageId

        sendCommand(json.dumps(cmd))

        # wait for the result to come back
        result = None
        while not(result):
            result = readData(messageId)

        return result

def findHoloseatPort():
    comPorts = list_ports.comports()
    for comPort in comPorts:
        vid = format(comPort.vid, 'X')
        pid = format(comPort.pid, 'X')

        # check for Alpha Controller (aka - Adafruit Feather 324u)
        if (vid == '239A' and pid == '800C'):
            return { 'comPort': comPort.device,
                     'expectedHwVer' : ['v0.4'],
                     'expectedDevice': 'Holoseat Alpha' }

        # check for v1.0+ (aka Holoseat vid/pid)
        if (vid == '1209' and pid == 'B058'):
            return { 'comPort': comPort.device,
                     'expectedHwVer' : ['v1.0'],
                     'expectedDevice' : 'Holoseat' }

    # we iterated over all available com ports and did not find Holoseat
    return None

def connect(expectedHspVer=None):
    holoseatPort = findHoloseatPort()
    if not(holoseatPort):
        return False  # no Holoseat Controllers connected to USB

    holoseat.port = holoseatPort['comPort']
    try:
        holoseat.open()

        # get device name
        deviceResults = json.loads(execCommand({"uri":"/main/devicename","verb":"GET"}))

        # check for errors
        if ('Error' in deviceResults):
            disconnect()
            print('Error: %s' % deviceResults['Error'])
            return False

        # check result, is this Holoseat?
        if (deviceResults['deviceName'] != holoseatPort['expectedDevice']):
            disconnect()
            return False

        # retrieve version info
        versionResults = json.loads(execCommand({"uri":"/main/version","verb":"GET"}))

        # check for errors
        if ('Error' in versionResults):
            disconnect()
            print('Error: %s' % versionResults['Error'])
            return False

        # is this the expected HW version?
        if not(versionResults['hwVer'] in holoseatPort['expectedHwVer']):
            disconnect()
            return False

        # TODO - is this a compatible FW version?

        # is this the compatible HSP version (must match exactly)?
        if expectedHspVer and (versionResults['hspVer'] != expectedHspVer):
            disconnect()
            return False

        # tell holoseat to echo out all status events to sync up any connected clients
        eventsResults = json.loads(execCommand({"uri":"/lowlevel/events","verb":"GET"}))
        if ('Error' in eventsResults):
            disconnect()
            print('Error: %s' % eventsResults['Error'])
            return False

        # passed all tests, we can talk to this Holoseat
        return True
    except serial.serialutil.SerialException as e:
        return False  # Holoseat not accessible


def disconnect():
    holoseat.close()
    holoseat.port = None
