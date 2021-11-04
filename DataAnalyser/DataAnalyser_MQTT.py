# Script containing the class definition for the MQTT functions of the Data Analyser


import paho.mqtt.client as PahoMQTT
import json
import requests
from DataAnalyser_class import *


class DataAnalyserMQTT:
    def __init__(self, clientID, broker, port, url_read, url_write):
        self.clientID = clientID

        # Parameters to establish MQTT connection
        self.broker = broker
        self.port = port
        self.subtopic = "IoTProject/SmartPill/Alarms/Catalog/+"

        # Parameters to communicate with ThingSpeak through HTTP requests:
        self.url_read = url_read
        self.url_write = url_write

        self._paho_mqtt = PahoMQTT.Client(clientID, False)

        # MQTT callbacks
        self._paho_mqtt.on_connect = self.OnConnect
        self._paho_mqtt.on_message = self.OnMessage

        # Data Analyser class:
        self.analyser = DataAnalyser()

    def start(self):
        self._paho_mqtt.connect(self.broker, self.port)
        self._paho_mqtt.loop_start()
        self._paho_mqtt.subscribe(self.subtopic, 2)

    def stop(self):
        self._paho_mqtt.unsubscribe(self.subtopic)
        self._paho_mqtt.loop_stop()
        self._paho_mqtt.disconnect()

    def OnConnect(self, paho_mqtt, userdata, flags, rc):
        if rc == 0:
            print(f"Connection to {self.broker} established.")
        else:
            print(f"Failed to connect to {self.broker}.")

    def OnMessage(self, paho_mqtt, userdata, msg):
        print( f"Message received from Catalog on topic \n {self.subtopic} \n Body: \n {msg.payload}")
        # Idea: quando il Catalog triggera gli allarmi per il medicinale di uno specifico paziente,
        # il Data Analyser ottiene dal messaggio le informazioni per fare una richiesta GET al canale ThingSpeak
        # collegato a questa terapia -> usiamo questo stesso messaggio di Alarms/Catalog per triggerare anche i calcoli
        # da parte del Data Analyser
        # if "Deleted" not in msg.topic:  # Forse si può omettere
        thingspeak = json.loads(msg.payload)["Thingspeak"]
        url = self.url_read + "/" + thingspeak["ch_ID"] + "/fields/1.json"
        read_apikey = thingspeak["read_apikey"]
        params = {"api_key": read_apikey}
        response = requests.get(url, params=params)
        print ("GET request sent to Thingspeak to obtain stats")
        if response.ok:
            data = response.json()["feeds"]
            output = self.analyser.stats(data)
            thingspeak_data = {"api_key": thingspeak["write_apikey"], "field2": json.dumps(output)}
            requests.post(self.url_write, data=thingspeak_data)
            print("POST request sent to Thingspeak with stats updated")
        else:
            print(response.raise_for_status())
