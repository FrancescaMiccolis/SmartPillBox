# Telegram bot manager


import time
from datetime import datetime
from bot import *


if __name__ == "__main__":
    # Read settings file to get the Catalog address
    flag = ""
    try:
        file = open("settings.json", "r")
        conf = json.load(file)
        file.close()
        flag = "ok"
    except:
        raise KeyError("Error reading file 'settings.json'")

    if flag == "ok":
        deviceID_base = "telegram"
        deviceID = deviceID_base + str(hash(datetime.now()))
        url = conf["Catalog_url"]
        params = {"id": deviceID}
        response = requests.get(url+"settings", params=params)
        
        if response.ok:
            r = response.json()
            broker = r["MQTT"]["broker"]
            port = r["MQTT"]["port"]
            topic = conf["mqttTopic"]
            token = conf["telegramToken"]
        else:
            print(response.raise_for_status())  # HTTP error

        # Set MQTT client
    startbot = IoTBot(token, broker, port, topic, url+"telegram")
    try:
        while True:
            time.sleep(3)
    except KeyboardInterrupt:
        startbot.client.stop()
        print("\nTelegram bot stopped.")

