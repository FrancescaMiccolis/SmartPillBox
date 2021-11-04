# Data Analyser


from datetime import datetime
from DataAnalyser_MQTT import *
import time


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
        # Communication with Catalog:
        deviceID_base = "data_analyser"
        deviceID = deviceID_base + str(hash(datetime.now()))
        url = conf["Catalog_url"]+"settings"
        params = {"id": deviceID}
        response = requests.get(url, params=params)

        if response.ok:
            r = response.json()
            broker = r["MQTT"]["broker"]
            port = r["MQTT"]["port"]

            url_read = r["ThingSpeak"]["read"]
            url_write = r["ThingSpeak"]["write"]

            mqttclient = DataAnalyserMQTT("DataAnalyser_MQTT", broker, port, url_read, url_write)
            mqttclient.start()
            try:
                while True:
                    time.sleep(10)
            except KeyboardInterrupt:
                mqttclient.stop()
                print("\nData Analyser stopped.")
        else:
            print(response.raise_for_status())  # HTTP error
