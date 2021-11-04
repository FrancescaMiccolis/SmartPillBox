# Weight Control script, responsible for checking Arduino's timestamps and weights, posting the results on thingspeak
# and triggering the missed assumption alarms.
#
# MQTT class: functions to subscribe and publish to topics, to evaluate whether Arduino's data are in the expected range
# or not and to trigger the missed assumption alarms.

import json
import paho.mqtt.client as PahoMQTT
from datetime import datetime
import requests
import threading


class WeightMQTT:

    def __init__(self, clientID, topic, broker, port, url):
        self.port = port
        self.subtopic = topic
        self.broker = broker
        self.clientID = clientID
        self._paho_mqtt = PahoMQTT.Client(clientID)
        self.url = url
        # MQTT callbacks:
        self._paho_mqtt.on_message = self.onMessageReceived
        self._paho_mqtt.on_connect = self.onConnect
        self._isSubscriber = True
        # Subscription topic:
        self.topic_MissedUser = "IoTProject/SmartPill/Alarms/WeightControl/Missed_Assumption"
        self.measurements = {}  # dict with the patientIDs as keys; each key has a dict associated as value that contains the therapy's infos for that patient
        self.arduino_msg = {  # Arduino alarm setting in case of a missed assumption
            "Led": {
                "Status": ["ON", "Fading"]  # led light fading instead of simply flashing
            },
            "Sound": {
                "Status": "ON",
                "Volume": "MAX"
            },
        }

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

    def myPublish(self, patientID, topic, message):
        topic += "/" + patientID
        self._paho_mqtt.publish(topic, message, 2)

    def onConnect(self, paho_mqtt, userdata, flags, rc):
        print(f"\nConnected to {self.broker} with result code: {rc}\n")

    def onMessageReceived(self, paho_mqtt, userdata, msg):
        payload = json.loads(msg.payload)
        if "Alarms/Arduino" in str(msg.topic):
            print("New message from Arduino.")  # Message published by Arduino with weight and timestamp
            topic_list = msg.topic.split("/")
            patientID = topic_list[-1]
            if "Time_1" in payload.keys():  # If the message contains the first weight and timestamp (W1 & T1):
                if int(payload['Time_1']):
                    self.measurements[patientID]["T1"] = int(payload['Time_1'])
                    self.measurements[patientID]["W1"] = int(payload['Weight_1'])
                    self.measurements[patientID]["Timer"].cancel()  # stops the internal timer for the considered patient
            else:  # If the message contains the second weight and timestamp (W2 & T2):
                if int(payload['Time_2']):
                    self.measurements[patientID]["T2"] = int(payload['Time_2'])
                    self.measurements[patientID]["W2"] = int(payload['Weight_2'])
                    # Calling the function to evaluate whether the times and weights are in the correct range or not:
                    self.InputControl(patientID)
        elif "Alarms/Catalog" in str(msg.topic):
            print("New message from Catalog.")  # Message published by the Catalog with the patient's therapy infos
            topic_list = msg.topic.split("/")
            patientID = topic_list[-1]
            if patientID not in self.measurements:
                self.measurements[patientID] = {}
            # Saving therapy's infos in the dict associated to the patientID key:
            self.measurements[patientID]["time_tol"] = int(payload["tol"])*60  # Time window for assumption
            self.measurements[patientID]["dose"] = payload["dose"]  # dose weight
            self.measurements[patientID]["Thingspeak"] = payload["Thingspeak"]  # thingspeak url + apikeys
            self.measurements[patientID]["iteration"] = 0  # keeps track of whether the missed assumption has happened or not
            self.measurements[patientID]["drug"] = payload["drug"]  # name of the drug to take

            # Background timer to trigger the missed assumption alarm if no input is received within the given time window:
            self.measurements[patientID]["Timer"] = threading.Timer(self.measurements[patientID]["time_tol"], self.MissingInput, [patientID])
            self.measurements[patientID]["Timer"].start()

    def MissingInput(self, patientID):
        # Called when the timer stops, triggers the publication of the missed assumption alert message for Arduino and the telegram bot.
        msg = {"drug": self.measurements[patientID]["drug"], "Arduino": self.arduino_msg}
        self.myPublish(patientID, self.topic_MissedUser, json.dumps(msg))
        self.measurements[patientID]["iteration"] = 1

    def InputControl(self, patientID):
        # Function to evaluate if the timestapms and the weights are in the correct ranges or not.
        tol = self.measurements[patientID]["dose"] * 5 / 100  # weight tolerance
        upper = self.measurements[patientID]["dose"] + tol  # upper limit of the dose weight range
        lower = self.measurements[patientID]["dose"] - tol  # lower limit of the dose weight range
        # Weight of drug taken:
        weight_diff = self.measurements[patientID]["W1"] - self.measurements[patientID]["W2"]
        # Time interval passed for the current assumption:
        time_diff = self.measurements[patientID]["T2"] - self.measurements[patientID]["T1"]
        time_range = self.measurements[patientID]["time_tol"]
        # Time check:
        if time_diff <= time_range and self.measurements[patientID]["iteration"] == 0:
            self.measurements[patientID]["time_flag"] = "OK"
        else:
            self.measurements[patientID]["time_flag"] = "Late"  # always late if a missed assumption happened
        # Weight check:
        if upper >= weight_diff >= lower:  # Calculated weight corresponding to correct dose
            self.measurements[patientID]["dose_flag"] = "OK"
        else:
            if weight_diff > upper:  # More drug taken than expected
                self.measurements[patientID]["dose_flag"] = "High"
            elif weight_diff < lower:  # Less drug taken than expected
                self.measurements[patientID]["dose_flag"] = "Low"
        # Message for the telegram bot to notify the completion of the process:
        self.myPublish(patientID, "IoTProject/SmartPill/Alarms/WeightControl/Input_Acquired", json.dumps({"drug": self.measurements[patientID]["drug"]}))
        # Process result:
        result = json.dumps({
            "time_flag": self.measurements[patientID]["time_flag"],
            "dose_flag": self.measurements[patientID]["dose_flag"],
            "timestamp": str(datetime.now())
            })
        print(f"\nOutput:\n\t - time_flag: {self.measurements[patientID]['time_flag']}\n\t - dose_flag: {self.measurements[patientID]['dose_flag']}")
        # POST request to thingspeak:
        data = {"api_key": self.measurements[patientID]["Thingspeak"]["write_apikey"], "field1": result}
        requests.post(self.url, data=data)
        print("Output sent to Thingspeak database.\n")
        # Removing the dict entry related to the patientID:
        del self.measurements[patientID]
