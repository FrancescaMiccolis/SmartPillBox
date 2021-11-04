# Catalog


import time
from Catalog_REST import *
from Catalog_MQTT import *


def readfile(filename):
    try:
        file = open(filename, "r")
        content = json.load(file)
        file.close()
        flag = "ok"
    except:
        raise KeyError(f"Error reading file {filename}")
    return content, flag


if __name__ == "__main__":
    # Read info file containing configuration settings, patients information, and devices info list
    info, flag_set = readfile("settings.json")
    pat, flag_pat = readfile("patients.json")
    dev, flag_dev = readfile("devices.json")

    if flag_set == "ok" and flag_pat == "ok" and flag_dev == "ok":
        # Start HTTP server
        rest = CatalogREST("Catalog_REST", pat, info, dev)
        conf = {
            '/': {
                'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
                'tools.sessions.on': True
            }
        }
        cherrypy.config.update(info["REST"])
        cherrypy.tree.mount(rest, '/', conf)
        cherrypy.engine.start()

        # Set MQTT client
        broker = info["MQTT"]["broker"]
        port = info["MQTT"]["port"]
        patients = pat["patients"]
        mqtt = CatalogMQTT("Catalog_MQTT", broker, port,
                           info["ThingSpeak"]["apikey"], info["ThingSpeak"]["read"], patients, dev)
        mqtt.start()

        # Patients therapy check
        try:
            while True:
                time.sleep(40)  # Checks the time every 40 seconds
                today = date.today()
                now = time.strftime('%H:%M')
                in_time = ""
                if patients:
                    for patient in patients:
                        therapies = patient["Therapy"]
                        for drug in therapies:
                            if drug["start"]:
                                start = datetime.strptime(drug["start"], "%d/%m/%Y").date()
                                if drug["end"]:
                                    end = datetime.strptime(drug["end"], "%d/%m/%Y").date()
                                    if today <= end:
                                        in_time = "yes"
                                    else:
                                        read_apikey = drug["Thingspeak"]["read_apikey"]
                                        ch_ID = drug["Thingspeak"]["ch_ID"]
                                        url = info["ThingSpeak"]["read"] + "/" + ch_ID + "/fields/2/last.json"
                                        response = requests.get(url, params={"api_key": read_apikey})
                                        if response.ok:
                                            # Publish message to Telegram bot
                                            r = json.loads(response.json()["field2"])
                                            r["drug"] = drug["drug"]
                                            r["duration"] = (end-start).days * drug["times"]
                                            mqtt.Publish("Stats/" + patient["ID"], json.dumps(r))
                                            # print(r)
                                        else:
                                            print(response.raise_for_status())
                                        # Set therapy to inactive by setting the start (and end) date to none
                                        drug["start"] = None
                                        drug["end"] = None
                                        mqtt.catalog.dump_output("patients.json", patients)
                                else:
                                    in_time = "yes"
                                if today >= start and in_time == "yes":
                                    if now in drug["hour"]:
                                        message = {"drug": drug["drug"], "dose": drug["dose"], "tol": drug["tol"],
                                                   "Thingspeak": drug["Thingspeak"]}
                                        # Trigger visual/sound cues and Telegram message
                                        mqtt.Publish(patient["ID"], message)
                                        # print(message)
                                        raise StopIteration
        except StopIteration:
            pass
        except KeyboardInterrupt:
            print("\nCatalog stopped.")
            cherrypy.engine.stop()
            mqtt.stop()
