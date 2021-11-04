# Arduino's LEDs, sound and sensors simulation script.
#
# MQTT class: functions to handle subscriptions, publications, missed assumption alarms and retrieving therapy's infos.
# Normal class: function to simulate weight and time measurements that would otherwise be provided by sensors.

import random
import time
import paho.mqtt.client as PahoMQTT
import json


class arduinoMQTT:

    def __init__(self, patientID, clientID, broker, port, subtopic, subtopic2):
        self.clientID = clientID
        self._paho_mqtt = PahoMQTT.Client(clientID)
        self.port = port
        self.broker = broker
        # Subscription topics:
        self.subtopic = subtopic  # for catalog's messages
        self.subtopic2 = subtopic2  # for weight control's messages
        self._isSubscriber = True
        # Therapy's infos:
        self.time_window = 0  # time interval given to the patient to take the medicament
        self.patientID = patientID  # patient ID
        self.drug = ""  # name of the drug to take
        self.flag_FirstDone = False  # flag to know whether the first sensors' output was generated or not
        # MQTT callbacks:
        self._paho_mqtt.on_connect = self.OnConnect
        self._paho_mqtt.on_message = self.OnMessage
        # Normal class recall:
        self.sensors = Sensors(self.patientID)

    def start(self):
        self._paho_mqtt.connect(self.broker, self.port)
        self._paho_mqtt.loop_start()
        if self._isSubscriber:
            self._paho_mqtt.subscribe(self.subtopic, 2)
            self._paho_mqtt.subscribe(self.subtopic2, 2)

    def stop(self):
        if self._isSubscriber:
            self._paho_mqtt.unsubscribe(self.subtopic)
            self._paho_mqtt.unsubscribe(self.subtopic2)
        self._paho_mqtt.loop_stop()
        self._paho_mqtt.disconnect()

    def OnConnect(self, paho_mqtt, userdata, flags, rc):
        if rc == 0:
            print(f"\nConnection to {self.broker} established.")
        else:
            print(f"\nFailed to connect to {self.broker}.")

    def myPublish(self, topic, message):
        self._isSubscriber = False
        topic += "/" + self.patientID
        self._paho_mqtt.publish(topic, message, 2)

    def OnMessage(self, paho_mqtt, userdata, message):
        msg = json.loads(message.payload)
        if "Catalog" in message.topic:
            if "Deleted" in message.topic:  # If the patient's therapy has been interrupted for any reason
                self.stop()
            else:
                # Saving therapy's infos:
                self.time_window = msg["tol"]
                self.sensors.weight_ref = [100 * msg["dose"], msg["dose"], msg["dose"]/random.randint(2, 4), msg["dose"]*random.randint(10, 25)/10]
                self.drug = msg["drug"]
                print("New message from Catalog.")
                # Initial alarm activation:
                print(
                    """\nAssumption Alarm:\n\t- LED status:\n\t\tON, Blinking, Color: Blue\n\t- Sound Alarm status:\n\t\tON, Intermittent, Volume: MAX\n""")
                print("Waiting for measurements...\n")
                # Assumption type selection by the user:
                choice = input("Do you want to simulate missed assumption? Type y or n\n> ")
                if "n" in choice:  # On time assumption, otherwise waits for messages from the weight control
                    print("\nSimulating medicament acquisition...\n")
                    # Simulation of the first and second weight measurements + related timestamps:
                    for i in range(0, 2):
                        msg, self.flag_FirstDone = self.sensors.simulate(self.time_window, self.flag_FirstDone)
                        # Sending a message to the weight control with the sensors' output:
                        self.myPublish("IoTProject/SmartPill/Alarms/Arduino", json.dumps(msg))
                        print(f"Sent message to Weight Control with Time_"+str(i+1)+" and Weight_"+str(i+1)+".")
                        if i == 0:
                            # Sending a message to the telegram bot to notify that the first weight measurement has been done:
                            self.myPublish("IoTProject/SmartPill/Alarms/WeightControl/Arduino_Inputs", json.dumps({"drug": self.drug}))
                            print("Sent message to Telegram bot to notify first input acquisition.\n")
        elif "WeightControl" in message.topic and "Arduino" in msg:
            # A message is received by the weight control, i.e. we're in the case of a missed assumption:
            print("New message from Weight Control.")
            # Activation of missed assumption alarms:
            print(f"""\nAssumption Alarm:  (Missed Assumption)
        - Led status: \n\t\t{msg["Arduino"]["Led"]["Status"][0]}, Blinking + {msg["Arduino"]["Led"]["Status"][1]}, Color: Red
        - Sound status: \n\t\t{msg["Arduino"]["Sound"]["Status"]}, Intermittent, Volume: {msg["Arduino"]["Sound"]["Volume"]}\n""")
            # Generating the two weight measurements:
            for i in range(0, 2):
                msg, self.flag_FirstDone = self.sensors.simulate(self.time_window, self.flag_FirstDone)
                self.myPublish("IoTProject/SmartPill/Alarms/Arduino", json.dumps(msg))
                print(f"Sent message to Weight Control with Time_" + str(i + 1) + " and Weight_" + str(i + 1) + ".")
                if i == 0:
                    self.myPublish("IoTProject/SmartPill/Alarms/WeightControl/Arduino_Inputs", json.dumps({"drug": self.drug}))
                    print("Sent message to Telegram bot to notify first input acquisition.\n")

class Sensors:
    def __init__(self, patientID):
        self.patientID = patientID
        self.weight_ref = []  # Reference list with: [starting_weight, expected_dose_weight, low_dose_weight, excessive_dose_weight]

    def simulate(self, window_time, flag_FirstDone):
        T = int(window_time*60)-30
        time.sleep(random.randint(5, T))
        # Sleeping for a random amount of time between 5 seconds and the length of the given assumption interval minus 30 seconds
        # to simulate different delays each time.
        if not flag_FirstDone:  # if it's the first measurement
            W = self.weight_ref[0]  # Starting weight
            print("First weight acquired.")
            print("""\nAssumption Alarm:\n\t- LED status:\n\t\tON, Fixed, Color: Blue\n\t- Sound Alarm status:\n\t\tOFF\n""")
            flag_FirstDone = True
        else:  # second measurement
            index = random.randint(0, 3)
            W = self.weight_ref[0] - self.weight_ref[index]  # Second weight
            print("Second weight acquired.")
            print("\nAssumption Alarm:\n\t- LED status:\n\t\tOFF\n\t- Sound Alarm status:\n\t\tOFF\n")
            flag_FirstDone = False

        t = time.time()  # Getting the current time in seconds
        if flag_FirstDone:
          index = 1
        else:
          index = 2
        msg = {"Time_" + str(index): t, "Weight_" + str(index): W}

        return msg, flag_FirstDone
