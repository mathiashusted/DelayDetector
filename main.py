import http.client
import json
import time
import os
import datetime
from math import floor

date = datetime.datetime.now()

def wait(actual, now):
    if (actual.replace(tzinfo=None) - now).total_seconds() <= 60:
        return "Now"
    else:
        return str(floor((actual.replace(tzinfo=None)-now).total_seconds()/60)) + "\""

# Open config file

try:
    with open("config.json", "r") as file:
        config = json.load(file)
except FileNotFoundError:
    print("Error opening config file!")

headers = {
    'accept': "application/json"
    }

dateFormat = "%Y-%m-%dT%H:%M:%S%z"

def extract_plannedWhen(data):
    return data.get("plannedWhen")



while True:
    date = datetime.datetime.now()
    conn = http.client.HTTPSConnection("v6.bvg.transport.rest", timeout=5)
    try:
        conn.request("GET", "/stops/" + config["stationId"] + "/departures?duration=" + str(config["duration"]) + "&linesOfStops=false&remarks=true&language=en", headers=headers)
        res = conn.getresponse()
        data = res.read()
        parsed = json.loads(data)
        parsed["departures"] = sorted(parsed["departures"], key=extract_plannedWhen)
    except:
        print("Error retrieving data, trying again...")
        continue

    hasActual = False

    

    if config["outputToTerminal"]:
        os.system('clear')
        print("\33[42mStation: " + config["stationName"] + "\33[0m | Timetable updated: " + date.strftime("%d.%m.%Y %H:%M:%S") + "\n")

        count = 0

        print(f"\033[95m{'Line':<10} {'Destination':<45} {'Departure':<10} {'Wait':<10} {'Delay':<10}\033[0m")
        for elem in parsed["departures"]:
            count += 1
            if count < config["maxTrains"]:
                planned = datetime.datetime.strptime(elem["plannedWhen"], dateFormat)
                if elem["when"] != None:
                    actual = datetime.datetime.strptime(elem["when"], dateFormat)
                    delay = int((actual - planned).total_seconds() / 60)
                    hasActual = True
                if (config["lines"] != []) and  not (elem["line"]["name"] in config["lines"]):
                    continue
                if "remarks" in elem and len(elem["remarks"]) > 1 and "code" in elem["remarks"][1] and elem["remarks"][1]["code"] == "text.realtime.journey.cancelled":
                    print (f"\033[1m{elem['line']['name']:<10}\033[0m {elem['direction']:<45} {planned.strftime('%H:%M'):<10} \033[41mCANCELLED\033[0m")
                    continue

                print(f"\033[1m{elem['line']['name']:<10}\033[0m {elem['direction']:<45} ", end='')

                if hasActual:
                    clock = actual.strftime("%H:%M")   
                    print(f"{clock:<10} ", end='')   
                    if (delay == 0):
                        print(f"{wait(actual,date):<10} ", end='')
                        print("\033[92m(=)\033[0m")
                    elif (delay > 0):
                        print(f"\033[31m{wait(actual,date):<10} \033[0m", end='')
                        print("\033[41m(+" + str(delay) + ")\033[0m")
                    elif (delay < 0):
                        print(f"{wait(actual,date):<10} ", end='')
                        print("\033[43m(" + str(delay) + ")\033[0m")
                else:
                    clock = planned.strftime("%H:%M")
                    print(f"{clock:<10} ", end='')
                    print(f"{wait(planned,date):<10} N/A")
            else:
                break

    time.sleep(config["refreshInterval"])
