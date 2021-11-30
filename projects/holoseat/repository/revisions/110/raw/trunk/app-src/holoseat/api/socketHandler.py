from tornado import websocket
from holoseat.util import getHost
from holoseat.api import apiConfig, connectedOrConnect
from holoseat.util import holoseatDevice
from tornado import web, gen

socketClients = []

class SocketHandler(websocket.WebSocketHandler):
    def check_origin(self, origin):
        uiLocalhost = "http://%s:%s" % ("localhost", apiConfig['uiPort'])
        uiIpAddress = "http://%s:%s" % (getHost(), apiConfig['uiPort'])
        return (origin == uiLocalhost) or (origin == uiIpAddress)

    def open(self):
        if self not in socketClients:
            socketClients.append(self)

    def on_close(self):
        if self in socketClients:
            socketClients.remove(self)

def SendMessages():
    # make sure we have all the data in the serial buffer
    connectedOrConnect()
    data = holoseatDevice.readData()
    while (data):
        data = holoseatDevice.readData()

    # for each line of data, send a message to each socket client
    message = holoseatDevice.popData()
    while (message):
        for client in socketClients:
            client.write_message(message)
        message = holoseatDevice.popData()
