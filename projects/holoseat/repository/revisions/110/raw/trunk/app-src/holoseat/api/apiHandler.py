from holoseat.api import status, apiThreadPool, apiConfig, connectedOrConnect
from concurrent.futures import ThreadPoolExecutor
from tornado.concurrent import run_on_executor
from tornado import web, gen, escape
from holoseat.util import holoseatDevice
import json
import serial

class apiHandler(web.RequestHandler):
    _threadPool = apiThreadPool
    SUPPORTED_METHODS = ('GET', 'PUT')

    @run_on_executor(executor="_threadPool")
    def connectedOrConnect(self):
        return connectedOrConnect()

    @run_on_executor(executor="_threadPool")
    def execCommand(self, command):
        return json.loads(holoseatDevice.execCommand(command))

    @web.asynchronous
    @gen.coroutine
    def processCommand(self, command, args=None):
        holoseatConnected = yield self.connectedOrConnect()
        if (holoseatConnected):
            try:
                if (args):
                    command['args'] = args
                results = yield self.execCommand(command)

                # check for errors
                if ('Error' in results):
                    holoseatDevice.disconnect()
                    self.set_status(status.HTTP_500_INTERNAL_SERVER_ERROR)
                    self.write(results)
                    self.finish()
                    return

                self.set_status(status.HTTP_200_OK)
                self.write(results)
                self.finish()
                return
            except serial.serialutil.SerialException as e:
                holoseatDevice.disconnect()
                self.set_status(status.HTTP_503_SERVICE_UNAVAILABLE)
                response = {
                    'ConnectionError': 'Lost connection to Holoseat',
                    'exceptionDetails': e.args[0]
                }
                self.write(response)
                self.finish()
                return

        else:
            response = {
                'ConnectionError': 'Cannot find Holoseat'
            }
            self.set_status(status.HTTP_503_SERVICE_UNAVAILABLE)
            self.write(response)
            self.finish()
            return

    def get(self):
        command = {"uri":self.request.uri.replace("/api",""),"verb":"GET"}
        self.processCommand(command)

    def put(self):
        args = escape.json_decode(self.request.body)
        command = {"uri":self.request.uri.replace("/api",""),"verb":"PUT", "args":args}
        self.processCommand(command)
