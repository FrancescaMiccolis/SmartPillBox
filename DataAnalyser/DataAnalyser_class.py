# Script containing the class definition for the statistical analysis functions of the Data Analyser


import json


class DataAnalyser:
    def __init__(self):
        self.OK = 0  # dose=ok & time=ok
        self.timealert = 0  # dose=ok & time!=ok
        self.dosealert = 0  # dose!=ok & time=ok
        self.KO = 0  # dose!=ok & time!=ok
        self.streak = []  # max number of consecutive assumptions where dose=ok & time=ok

    def stats(self, data):
        N = 0
        for entry in data:
            if entry["field1"]:
                N += 1
                flags = json.loads(entry["field1"])
                if flags["time_flag"] == "OK" and flags["dose_flag"] == "OK":
                    self.OK += 1
                    if not self.streak:
                        self.streak.append(1)
                    else:
                        self.streak[-1] += 1
                elif flags["time_flag"] != "OK" and flags["dose_flag"] == "OK":
                    self.timealert += 1
                    self.streak.append(0)
                elif flags["time_flag"] == "OK" and flags["dose_flag"] != "OK":
                    self.dosealert += 1
                    self.streak.append(0)
                elif flags["time_flag"] != "OK" and flags["dose_flag"] != "OK":
                    self.KO += 1
                    self.streak.append(0)

        output = {"OK": int(100*self.OK/N), "timealert": int(100*self.timealert/N), "dosealert": int(100*self.dosealert/N),
                  "KO": int(100*self.KO/N), "streak": int(100*max(self.streak)/N)}
        return output
