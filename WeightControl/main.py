# Weight Control


import time
from WeightControl import *


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
        deviceID_base = "weight_control"
        deviceID = deviceID_base + str(hash(datetime.now()))
        url = conf["Catalog_url"]+"settings"
        params = {"id": deviceID}
        response = requests.get(url, params=params)

        if response.ok:
            r = response.json()
            broker = r["MQTT"]["broker"]
            port = r["MQTT"]["port"]
            url_thingspeak = r["ThingSpeak"]["write"]
            topic = "IoTProject/SmartPill/Alarms/+/+"
            weightcontrol = WeightMQTT('WeightControl', topic, broker, port, url_thingspeak)
            weightcontrol.start()
            try:
                while True:
                    time.sleep(1)
            except:
                weightcontrol.stop()
        else:
            print(response.raise_for_status())  # HTTP error
