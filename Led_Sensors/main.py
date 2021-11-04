# Arduino adaptor: led and sensors manager


from Arduino import * 
import json
from datetime import datetime
import requests
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
        deviceID_base = "led_sensors"
        deviceID = deviceID_base + str(hash(datetime.now()))
        url = conf["Catalog_url"]+"settings"
        params = {"id": deviceID}
        response = requests.get(url, params=params)

        if response.ok:
            r = response.json()
            broker = r["MQTT"]["broker"]
            port = r["MQTT"]["port"]
            patientID = r["patient_ID"]
            topic = "IoTProject/SmartPill/Alarms/+/"+patientID+"/#"
            topic2 = "IoTProject/SmartPill/Alarms/WeightControl/Missed_Assumption/" + patientID
            # Instantiate MQTT client
            led_sensors = arduinoMQTT(patientID, "Led_Sensors_MQTT", broker, port, topic, topic2)
            led_sensors.start()
            try:
                while True:
                    time.sleep(30)
            except KeyboardInterrupt:
                print('\nArduino stopped.')
                led_sensors.stop()
        else:
            print(response.raise_for_status())
