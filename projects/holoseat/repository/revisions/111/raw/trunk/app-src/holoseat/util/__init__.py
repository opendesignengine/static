import socket
from contextlib import closing

from holoseat.util import holoseatSerial, jsonserial

holoseatDevice = holoseatSerial.holoseatSerialDevice()

# from https://stackoverflow.com/a/45690594
def findFreePort():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('localhost', 0))
        return s.getsockname()[1]

def getHost():
    # per https://stackoverflow.com/a/19638229
    return socket.gethostbyname(socket.gethostname())
