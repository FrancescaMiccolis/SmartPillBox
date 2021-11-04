import paho.mqtt.client as PahoMQTT
import json
class MyMQTT:
    def __init__(self, clientID, broker, port, bot):

        self.broker = broker
        self.port = port
        self.clientID = clientID
        self.bot = bot
        self._topic = ""
        self._isSubscriber = True
        # create an instance of paho.mqtt.client
        self._paho_mqtt = PahoMQTT.Client(clientID, True)
        # register the callback
        self._paho_mqtt.on_connect = self.myOnConnect
        self._paho_mqtt.on_message = self.myOnMessageReceived
 
     def mySubscribe (self, topic):
        # subscribe for a topic
        self._paho_mqtt.subscribe(topic, 2) 
        self._isSubscriber = True
        self._topic = topic
        print ("subscribed to %s" % (topic))
 
    def start(self):
        #manage connection to broker
        self._paho_mqtt.connect(self.broker , self.port)
        self._paho_mqtt.loop_start()
    def unsubscribe(self):

        if (self._isSubscriber):
            # remember to unsuscribe if it is working also as subscriber 
            self._paho_mqtt.unsubscribe(self._topic)
            
    def stop (self):

        if (self._isSubscriber):
            # remember to unsuscribe if it is working also as subscriber 
            self._paho_mqtt.unsubscribe(self._topic)
 
        self._paho_mqtt.loop_stop()
        self._paho_mqtt.disconnect()
        
    def writefile(self, output, filename):
        try:
            file = open(filename, "w")
            json.dump(output, file, indent=4)
            file.close()
        except:
            raise KeyError(f"Error writing file {filename}")

    def myOnConnect (self, paho_mqtt, userdata, flags, rc):

        print("Connected to %s with result code: %d" % (self.broker, rc))

    def myOnMessageReceived (self, paho_mqtt,userdata, msg):
        # A new message is received 
        filename = "listids.json"  #File where the chatID is associated at the userID
        file = open(filename)
        myids = json.load(file)
        file.close()
        self.payload = json.loads(msg.payload)
        mytopic = msg.topic
        if "Deleted" in mytopic:
            #delete from listids all chatIDs associated with that userID
            id_da_eliminare = self.payload["todelete"]
            myids.pop(id_da_eliminare)
            self.writefile(myids, "listids.json")
        else:
            mytopic = mytopic.split("/")
            mid = mytopic[-1]
            for key in myids:  
                if myids[key] == mid:
                    chat_ID = key
                    if len(mytopic) != 0:
                        info = json.loads(msg.payload)
                        if "Catalog" in mytopic and "Stats" not in mytopic:   #The message is an Alarm of a patient
                            drug = info["drug"]
                            toll = info["tol"]
                            dose = info["dose"]
                            self.bot.sendMessage(chat_ID,
                                                 text=f'ALERT!!! Remember to take {dose} mg of {drug} within {toll} minutes.')
                        elif "Stats" in mytopic:  #A therapy is terminated. Final stats are shared with the patient
                            info = json.loads(info)
                            drug = info["drug"]
                            ok = info["OK"]
                            duration = info["duration"]
                            streak_abs = info["streak"]*duration/100  # Streak as absolute value (# consecutive OK assumptions)
                            self.bot.sendMessage(chat_ID, text=f"Congratulations, you have finished your therapy with {drug}. \n Your adherence score is {ok} %. \n Your best streak is {round(streak_abs)} consecutive correct assumptions, corresponding to {info['streak']} % of your therapy. \n")

                        elif "WeightControl" in mytopic:   #Measurement message received
                            drug = info["drug"]
                            if "Arduino_Inputs" in mytopic:  #First input
                                self.bot.sendMessage(chat_ID,
                                                     text=f"Remember to weight PillBox again after taking {drug}, thank you!")
                            elif "Input_Acquired" in mytopic:  #Second input
                                self.bot.sendMessage(chat_ID,
                                                     text=f"Input acquired correctly. Stay safe!")
                            elif "Missed_Assumption" in mytopic:  #Missed input
                                self.bot.sendMessage(chat_ID, f"WARNING!!! It seems you forgot to take {drug}! \n")
                else:
                    print(f"User {mid} still hasn't accessed the SmartPillBox bot.")
