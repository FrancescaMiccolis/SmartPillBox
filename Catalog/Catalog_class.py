# Script containing the class definition for the patients/devices managing functions of the Catalog


import json
import requests
import random


class Catalog:
    def __init__(self, apikey, url, patients, devices):
        self.apikey = apikey
        self.baseurl = url

        self.patients = patients
        self.devices = devices

    def dump_output(self, filename, output):
        try:
            file = open(filename, "w")
            json.dump(output, file, indent=4)
            file.close()
        except:
            raise KeyError(f"Error updating file {filename}")

    def adjust_hour(self, data):
        temp = data["hour"].split(':')
        first = temp[0]
        second = int(first) + 6
        data["hour"] = [data["hour"], str(second) + ':' + temp[1]]
        return data

    # Therapy management services
    def AddNewPatient(self, toadd):
        pat_id = str(hash(toadd["CF"])) + str(random.randint(10, 99))

        # Create Thingspeak channel
        drug = toadd["drug"]
        thingspeak_data = {"api_key": self.apikey, "name": pat_id,
                           "field1": "WeightControl: "+drug, "field2": "DataAnalyser: "+drug}
        url = self.baseurl + '.json'
        response = requests.post(url, data=thingspeak_data)
        if response.ok:
            r = response.json()
            channelID = str(r["id"])  # Get channel ID from the server's response
            write_apikey = r["api_keys"][0]["api_key"]  # Get write api key for the channel
            read_apikey = r["api_keys"][1]["api_key"]  # Get read api key for the channel
        else:
            print(response.raise_for_status())  # HTTP error
            channelID = None
            write_apikey = None
            read_apikey = None

        # Add new patient to the "patients.json" file
        toadd["hour"] = toadd["hour"].strip('/"')
        if toadd["times"] == 2:
            toadd = self.adjust_hour(toadd)
        newpat = {"ID": pat_id, "Name": toadd["name"], "Surname": toadd["surname"], "CF": toadd["CF"],
                  "Therapy": [{"drug": toadd["drug"], "dose": toadd["dose"], "times": toadd["times"],
                               "hour": toadd["hour"], "tol": toadd["tol"], "start": toadd["start"],
                               "end": toadd["end"], "Thingspeak": {"ch_ID": channelID, "write_apikey": write_apikey,
                                                                   "read_apikey": read_apikey}}],
                  "led_sensors": ""}
        self.patients.append(newpat)
        output = {"patients": self.patients}
        self.dump_output('patients.json', output)

    def DeletePatient(self, del_id):
        for i in range(len(self.patients)):
            if self.patients[i]["ID"] == del_id:
                # Delete all the patient's Thingspeak channels:
                for therapy in self.patients[i]["Therapy"]:
                    todelete = therapy["Thingspeak"]["ch_ID"]
                    url = self.baseurl + '/' + todelete + '.json'
                    requests.delete(url, data={"api_key": self.apikey})
                self.patients.pop(i)  # Delete patient from the "patients.json" file
                break
        output = {"patients": self.patients}
        self.dump_output('patients.json', output)

    def AddTherapy(self, toadd):
        for patient in self.patients:
            if patient["ID"] == toadd["id"]:
                # Create Thingspeak channel for new therapy
                drug = toadd["drug"]
                thingspeak_data = {"api_key": self.apikey, "name": patient["ID"],
                                   "field1": "WeightControl: " + drug, "field2": "DataAnalyser: " + drug}
                url = self.baseurl + '.json'
                response = requests.post(url, data=thingspeak_data)
                if response.ok:
                    r = response.json()
                    channelID = str(r["id"])  # Get channel ID from the server's response
                    write_apikey = r["api_keys"][0]["api_key"]  # Get write api key for the channel
                    read_apikey = r["api_keys"][1]["api_key"]  # Get read api key for the channel
                else:
                    print(response.raise_for_status())  # HTTP error
                    channelID = None
                    write_apikey = None
                    read_apikey = None

                toadd["hour"] = toadd["hour"].strip('/"')
                if toadd["times"] == 2:
                    toadd = self.adjust_hour(toadd)
                newtherapy = {"drug": toadd["drug"], "dose": toadd["dose"], "times": toadd["times"],
                              "hour": toadd["hour"], "tol": toadd["tol"], "start": toadd["start"],
                              "end": toadd["end"], "Thingspeak": {"ch_ID": channelID, "write_apikey": write_apikey,
                                                                  "read_apikey": read_apikey}}
                patient["Therapy"].append(newtherapy)
                break
        output = {"patients": self.patients}
        self.dump_output('patients.json', output)

    def DeleteTherapy(self, todelete):
        for patient in self.patients:
            if patient["ID"] == todelete["id"]:
                for i in range(len(patient["Therapy"])):
                    if patient["Therapy"][i]["drug"] == todelete["therapy"]:
                        # Delete corresponding channel
                        channel = patient["Therapy"][i]["Thingspeak"]["ch_ID"]
                        if channel:
                            url = self.baseurl + '/' + channel + '.json'
                            requests.delete(url, data={"api_key": self.apikey})
                        patient["Therapy"].pop(i)  # Delete therapy entry from list
                        break
                break
        output = {"patients": self.patients}
        self.dump_output('patients.json', output)

    def UpdateTherapy(self, toupdate):
        if toupdate["hour"]:
            toupdate["hour"] = toupdate["hour"].strip('/"')
        keys = list(toupdate.keys())
        for patient in self.patients:
            if patient["ID"] == toupdate["id"]:
                for i in range(len(patient["Therapy"])):
                    if patient["Therapy"][i]["drug"] == toupdate["drug"]:
                        pat_keys = list(patient["Therapy"][i].keys())
                        for key in keys:
                            if toupdate[key] and key in pat_keys:
                                patient["Therapy"][i][key] = toupdate[key]
                        if patient["Therapy"][i]["times"] == 2:
                            patient["Therapy"][i] = self.adjust_hour(patient["Therapy"][i])
                        break
        output = {"patients": self.patients}
        self.dump_output('patients.json', output)

    # Devices management services
    def DeleteDevice(self, patientID):
        if patientID in self.devices:
            self.devices.pop(patientID)
