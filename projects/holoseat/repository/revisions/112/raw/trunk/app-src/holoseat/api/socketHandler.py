from tornado import websocket, web, gen
from concurrent.futures import ThreadPoolExecutor
from tornado.concurrent import run_on_executor
from holoseat.util import getHost, holoseatDevice
from holoseat.api import apiConfig, connectedOrConnect, apiThreadPool
import json
import serial

socketClients = []

class SocketHandler(websocket.WebSocketHandler):
    _threadPool = apiThreadPool

    @run_on_executor(executor="_threadPool")
    def connectedOrConnect(self):
        return connectedOrConnect()

    @run_on_executor(executor="_threadPool")
    def execCommand(self, command):
        return json.loads(holoseatDevice.execCommand(command))

    @web.asynchronous
    @gen.coroutine
    def getEvents(self):
        holoseatConnected = yield self.connectedOrConnect()
        if (holoseatConnected):
            try:
                command = {"uri":"/lowlevel/events","verb":"GET"}
                results = yield self.execCommand(command)
            except serial.serialutil.SerialException as e:
                pass

    def check_origin(self, origin):
        uiLocalhost = "http://%s:%s" % ("localhost", apiConfig['uiPort'])
        uiIpAddress = "http://%s:%s" % (getHost(), apiConfig['uiPort'])
        return (origin == uiLocalhost) or (origin == uiIpAddress)

    def open(self):
        if self not in socketClients:
            socketClients.append(self)

    def on_message(self, message):
        print("Received message: %s" % message)
        if message == 'getEvents':
            self.getEvents()

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
