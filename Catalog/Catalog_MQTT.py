# Script containing the class definition for the MQTT functions of the Catalog
# The Catalog subscribes to the "Dashboard/#" topic to receive updates on patients/therapies from the physician


import paho.mqtt.client as PahoMQTT
from Catalog_class import *


class CatalogMQTT:
    def __init__(self, clientID, broker, port, apikey, url, patients, devices):
        self.clientID = clientID

        # Parameters to establish MQTT connection
        self.broker = broker
        self.port = port
        self.subtopic = "Dashboard/#"
        self.pubtopic = "IoTProject/SmartPill/Alarms/Catalog/"
        self._isSubscriber = True

        # Parameters to communicate with ThingSpeak through HTTP requests:
        self.apikey = apikey
        self.baseurl = url

        # Other Catalog classes instantiation:
        self.catalog = Catalog(self.apikey, self.baseurl, patients, devices)

        self._paho_mqtt = PahoMQTT.Client(clientID, False)

        # MQTT callbacks
        self._paho_mqtt.on_connect = self.OnConnect
        self._paho_mqtt.on_message = self.OnMessage

    def start(self):
        self._paho_mqtt.connect(self.broker, self.port)
        self._paho_mqtt.loop_start()
        if self._isSubscriber:
            self._paho_mqtt.subscribe(self.subtopic, 2)

    def stop(self):
        if self._isSubscriber:
            self._paho_mqtt.unsubscribe(self.subtopic)
        self._paho_mqtt.loop_stop()
        self._paho_mqtt.disconnect()

    def OnConnect(self, paho_mqtt, userdata, flags, rc):
        if rc == 0:
            print(f"Connection to {self.broker} established.")
        else:
            print(f"Failed to connect to {self.broker}.")

    def Publish(self, add, message):
        self._isSubscriber = False
        topic = self.pubtopic + add
        self._paho_mqtt.publish(topic, json.dumps(message), 2)

    def OnMessage(self, paho_mqtt, userdata, msg):
        print("Message from Dashboard received.")
        if msg.topic == "Dashboard/NewPatient":
            toadd = json.loads(msg.payload)
            self.catalog.AddNewPatient(toadd)

        elif msg.topic == "Dashboard/DeletePatient":
            del_id = json.loads(msg.payload)["id"]
            self.catalog.DeletePatient(del_id)
            self.catalog.DeleteDevice(del_id)
            self.Publish(del_id+"/Deleted", json.dumps({"todelete": del_id}))

        elif msg.topic == "Dashboard/ManageTherapy/addnew":
            toadd = json.loads(msg.payload)
            self.catalog.AddTherapy(toadd)

        elif msg.topic == "Dashboard/ManageTherapy/delete":
            todelete = json.loads(msg.payload)
            self.catalog.DeleteTherapy(todelete)

        elif msg.topic == "Dashboard/ManageTherapy/update":
            toupdate = json.loads(msg.payload)
            self.catalog.UpdateTherapy(toupdate)
