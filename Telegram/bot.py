# Telegram Bot

import telepot
from telepot.loop import MessageLoop
import requests
from datetime import date
from datetime import datetime
from MyMQTT import *

class IoTBot:
    def __init__(self, token, broker, port, topic, url):
        self.tokenBot = token
        self.bot = telepot.Bot(self.tokenBot)
        botbot = self.bot
        self.chatIDs = ""
        self.client = MyMQTT("telegramBot", broker, port, botbot)
        self.client.start()
        self.topic = topic
        self.url = url
        self.client.mySubscribe(topic)
        self.helpmessage = ("Type /list to get all your current therapies.\n"
                                                           "Type /<drug> to get info on your therapy with <drug>. \n "
                            "Type /stats to get your statistics on ongoing therapies. \n")
        try:
            file = open("listids.json", "r")
            self.chatIDs = json.load(file)
            file.close()
        except:
            raise KeyError("Error reading file 'listids.json'")

        MessageLoop(self.bot, {'chat': self.on_chat_message}).run_as_thread()

    def writefile(self, output, filename):
        try:
            file = open(filename, "w")
            json.dump(output, file, indent=4)
            file.close()
        except:
            raise KeyError(f"Error writing file {filename}")

    def on_chat_message(self, msg):
        content_type, chat_type, chat_ID = telepot.glance(msg)
        userin = msg["text"]
        if userin == "/start":   #Sign in for new users
            if str(chat_ID) not in self.chatIDs:
                self.chatIDs[str(chat_ID)] = ""
                self.bot.sendMessage(chat_ID, text="Please insert your CF:\n")
            else:
                self.bot.sendMessage(chat_ID, text="Welcome back, how can I help you?\n\n"
                                                   +self.helpmessage)
        elif "/" not in userin and self.chatIDs[str(chat_ID)] == "":
            if len(userin) != 16:
                self.bot.sendMessage(chat_ID, text="Oops! Invalid CF. Please type your CF again:\n")
            else:
                response = requests.get(self.url, params={"CF": userin})
                if response.ok:
                    r = response.json()
                    if len(r) != 0:
                        self.chatIDs[str(chat_ID)] = str(r["ID"])
                        self.writefile(self.chatIDs, "listids.json")
                        self.bot.sendMessage(chat_ID, text="Registration completed successfully. Welcome on board!\n\n"
                                                           + self.helpmessage)
                    else:
                        self.bot.sendMessage(chat_ID, text="Oops! Invalid CF. Please check that your CF is correct:\n")
                else:
                    print(response.raise_for_status())
        elif userin != "/start" and "help" not in userin and "stats" not in userin: 
            pat_id = self.chatIDs[str(chat_ID)]
            response = requests.get(self.url, params={"id": pat_id})
            if response.ok:
                r = response.json()
                if len(r) != 0:
                    if userin == "/list":
                        tosend = "Current therapies:\n"
                    else:
                        tosend = ""
                    for therapy in r["therapy"]:
                        if therapy["drug"].casefold() in userin.casefold():
                            if therapy['start']:
                                if therapy["end"]:
                                    end = datetime.strptime(therapy["end"], "%d/%m/%Y").date()
                                    if date.today() <= end:
                                        tosend = f'You must assume {therapy["drug"]} {therapy["times"]} time(s) per day,' \
                                            f' at {therapy["hour"]}, until {therapy["end"]}.'
                                else: #chronic therapy case
                                    tosend = f'You must assume {therapy["drug"]} {therapy["times"]} time(s) per day,' \
                                            f' at {therapy["hour"]}.'
                        elif "list" in userin:
                            if therapy['start']:
                                if therapy["end"]:
                                    end = datetime.strptime(therapy["end"], "%d/%m/%Y").date()
                                    if date.today() <= end:
                                        tosend += f'{therapy["drug"]}, {therapy["times"]} time(s) per day, ' \
                                                f'at {therapy["hour"]}, until {therapy["end"]}.\n\n'
                                else:   #chronic therapy case
                                    tosend += f'{therapy["drug"]}, {therapy["times"]} time(s) per day, ' \
                                                f'at {therapy["hour"]}.\n\n'
                    if tosend:
                        self.bot.sendMessage(chat_ID, text=tosend)
                    else:
                        self.bot.sendMessage(chat_ID, text="No corresponding therapy found.")
                else:
                    self.bot.sendMessage(chat_ID, text="No ongoing therapies.")
        elif "stats" in userin:
            pat_id = self.chatIDs[str(chat_ID)]
            adurl = self.url.strip("telegram")
            resp = requests.get(adurl + "adherence", params={"id": pat_id})
            if resp.ok:
                r = resp.json()
                if len(r) != 0:
                    for drug in r:                         
                        ts_url = "https://api.thingspeak.com/channels/"+r[drug][0]+"/fields/2/last.json"
                        response = requests.get(ts_url, params={"api_key": r[drug][1]})
                        if response.ok:
                            data = json.loads(response.json()["field2"])                           
                            if data['OK'] >= 75:
                                first = f"Congrats! You are doing great with your {drug} therapy! \n" \
                                        f"Your current adherence is {data['OK']} %. \n"
                                second = ""
                            else:
                                first = f"Mmmmmh, there is room for improvement with your {drug} therapy! \n" \
                                        f"Your current adherence is {data['OK']} %. \n"
                                if data['timealert'] > data['dosealert']:
                                    second = "You should focus on your intake timing."
                                elif data['timealert'] == data['dosealert']:
                                    second = "You should be more careful with both your intake timing and dose. \n"
                                else:
                                    second = "You should be more careful with your intake dose. \n"
                            streak = round(data["streak"]*r[drug][2]/100)
                            third = f"Your streak is {streak} consecutive correct assumptions, corresponding to {data['streak']} % of your therapy.\n"
                            self.bot.sendMessage(chat_ID, text=first + second + third)
                        else:
                            print(response.raise_for_status())
        elif "help" in userin:
            self.bot.sendMessage(chat_ID, text = self.helpmessage)
        
        else:
            self.bot.sendMessage(chat_ID, text="Command not supported, please try again.")
