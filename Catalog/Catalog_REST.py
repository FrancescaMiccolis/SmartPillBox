# Script containing the class definition for the REST functions of the Catalog


import cherrypy
import json
from datetime import date
from datetime import datetime


class CatalogREST:
    exposed = True

    def __init__(self, clientID, patients, settings, devices):
        self.ID = clientID
        self.output = {}
        self.patients = patients["patients"]
        self.settings = settings
        self.devices = devices

    def dump_output(self, filename, output):
        try:
            file = open(filename, "w")
            json.dump(output, file, indent=4)
            file.close()
        except:
            raise KeyError(f"Error updating file {filename}")

    def GET(self, *uri, **params):
        if len(uri) > 0:
            if uri[0] == "patients" or uri[0] == "therapy" or uri[0] == "telegram":
                if uri[0] == "patients":  # GET request from Dashboard to obtain patients' names
                    names = [patient["Name"] + ' ' + patient["Surname"] for patient in self.patients]
                    id_pat = [patient["ID"] for patient in self.patients]
                    temp = {names[i]: id_pat[i] for i in range(len(names))}
                    self.output = {"names": names, "id": temp}
                elif uri[0] == "therapy" or uri[0] == "telegram":
                    if params != {}:
                        if "id" in params:
                            id_pat = params["id"]
                            for patient in self.patients:
                                if patient["ID"] == id_pat:
                                    therapy = patient["Therapy"]
                                    if uri[0] == "therapy":  # Dashboard
                                        self.output = {"therapy": [therapy[i]["drug"] for i in range(len(therapy))]}
                                    else:  # Telegram bot manager
                                        self.output = {"therapy": therapy}
                        elif "CF" in params:  # Telegram bot - new patient registration
                            cf = params["CF"]
                            for patient in self.patients:
                                if patient["CF"] == cf:
                                    self.output = {"ID": patient["ID"]}
                    else:
                        raise cherrypy.HTTPError(400, "No patient ID/CF submitted. Please check parameters.")

            elif uri[0] == "adherence":
                if params != {} and params["id"]:
                    id_pat = params["id"]
                    if "drug" in params:  # Dashboard
                        drug = params["drug"]
                        for patient in self.patients:
                            if patient["ID"] == id_pat:
                                therapies = patient["Therapy"]
                                for therapy in therapies:
                                    if therapy["drug"] == drug and therapy["start"]:
                                        self.output = therapy["Thingspeak"]
                    else:  # Telegram asking for a patient's stats
                        for patient in self.patients:
                            if patient["ID"] == id_pat:
                                self.output = {}
                                for therapy in patient["Therapy"]:
                                    if therapy["start"]:
                                        today = date.today()
                                        if therapy["end"]:
                                            end = datetime.strptime(therapy["end"], "%d/%m/%Y").date()
                                            if today <= end:
                                                pass
                                            else:
                                                break
                                        start = datetime.strptime(therapy["start"], "%d/%m/%Y").date()
                                        duration = (today - start).days * therapy["times"]
                                        self.output[therapy["drug"]] = [therapy["Thingspeak"]["ch_ID"],
                                                                        therapy["Thingspeak"]["read_apikey"],
                                                                        duration]

                else:
                    raise cherrypy.HTTPError(400, "Please check parameters. Patient ID and drug name must be submitted "
                                                  "to get therapy adherence info.")

            elif uri[0] == "settings":  # Devices/Microservices registration to the Catalog
                if params != {} and params["id"]:
                    deviceID = params["id"]
                    if "led_sensors" in deviceID:
                        for patient in self.patients:
                            if not patient["led_sensors"]:
                                patient["led_sensors"] = deviceID
                                self.output = {"MQTT": self.settings["MQTT"], "patient_ID": patient["ID"]}
                                if patient["ID"] not in self.devices:
                                    self.devices[patient["ID"]] = {}
                                self.devices[patient["ID"]]["led_sensors"] = deviceID
                                break
                    elif "weight_control" in deviceID:
                        self.output = {"MQTT": self.settings["MQTT"], "ThingSpeak": self.settings["ThingSpeak"]}
                        self.devices["weight_control"] = deviceID
                    elif "data_analyser" in deviceID:
                        self.output = {"MQTT": self.settings["MQTT"], "ThingSpeak": self.settings["ThingSpeak"]}
                        self.devices["data_analyser"] = deviceID
                    elif "telegram" in deviceID:
                        self.output = {"MQTT": self.settings["MQTT"]}
                        self.devices["telegram"] = deviceID
                    patients_updated = {"patients": self.patients}
                    self.dump_output('patients.json', patients_updated)
                    self.dump_output('devices.json', self.devices)
                else:
                    raise cherrypy.HTTPError(400, "No device ID submitted. Please check parameters.")
            else:
                raise cherrypy.HTTPError(400, "uri must be 'patients', 'therapy', or 'settings'")
        else:
            raise cherrypy.HTTPError(400, "uri must be present")

        response = json.dumps(self.output)
        self.output = {}
        return response
