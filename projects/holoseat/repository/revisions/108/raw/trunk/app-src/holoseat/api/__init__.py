# Tornado imports
from tornado import web, escape, ioloop, httpclient, gen

# other imports
import threading
from concurrent.futures import ThreadPoolExecutor
from holoseat.util import holoseatSerial

apiConfig = { 'apiVersion' : 'v0.4.0',
              'uiPort' : 8000,
              'apiPort' : 8080,
              'debug' : False }

apiThreadPool = ThreadPoolExecutor()

def connectedOrConnect():
    return holoseatSerial.connected() or holoseatSerial.connect(apiConfig['apiVersion'])

# package imports now that the package variables are declared
from holoseat.api.apiHandler import apiHandler
from holoseat.api import mainHandlers, debugHandlers, socketHandler

def apiThreadFunc(debug=False, port=8080):
    application = web.Application([
        (r"/api/main/devicename", mainHandlers.DevicenameHandler),
        (r"/api/main/version", mainHandlers.VersionHandler),
        (r"/api/main/apiVersion", mainHandlers.ApiVersionHandler),
        (r"/api/debug", debugHandlers.DebugHandler),
        (r"/api/debug/serial", debugHandlers.DebugSerialHandler),
        (r'/ws', socketHandler.SocketHandler)
    ], debug=debug, autoreload=False)
    print("Listening at port {0}".format(port))
    application.listen(port)
    socketMessages = ioloop.PeriodicCallback(socketHandler.SendMessages, 10)
    socketMessages.start()
    ioloop.IOLoop.instance().start()

def start(debug=False, apiPort=8080, uiPort=8000):
    apiConfig['apiPort'] = apiPort
    apiConfig['uiPort'] = uiPort
    apiConfig['debug'] = debug

    apiThread = threading.Thread(target=apiThreadFunc, args=(debug,apiPort,), name='API-Thread')
    apiThread.setDaemon(True)
    apiThread.start()
