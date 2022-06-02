import googlemaps
import requests
from bs4 import BeautifulSoup
import time
import sys

introduction = '''Best Beaches version 1.0

This program allows a user to input an address and it will return the best beaches in the area to go to based on the wind, temperature, and water temperature at that beach.

In the next version there will be an updated algorithm that uses more data points like UV index and wind direction.
'''

print(introduction)


def getAPIKey():
    return open("apiKey.txt", "r").read()


def getLocation():
    street = input("Enter your street: ")
    town = input("Enter your town: ")
    state = input("Enter your state (if not in US leave blank): ")
    country = input("Enter your country: ")
    radius = input("How far are you looking to go (miles): ")

    location = f"{street}, {town} {state}, {country}"
    return location, country, int(radius)


def milesToMeters(miles):
    try:
        return miles * 1609.344
    except:
        return 0


def parseAddress(address):
    newAddy = ""
    for i in range(len(address)):
        if address[i] == " ":
            newAddy += "+"
        else:
            newAddy += address[i]
    return newAddy


def getLatLng(addressOrZip, apiKey):
    lat, lng = None, None
    baseURL = "https://maps.googleapis.com/maps/api/geocode/json"
    endpoint = f"{baseURL}?address={addressOrZip}&key={apiKey}"
    # see how our endpoint includes our API key? Yes this is yet another reason to restrict the key
    r = requests.get(endpoint)
    if r.status_code not in range(200, 299):
        return None, None
    try:
        results = r.json()['results'][0]
        lat = results['geometry']['location']['lat']
        lng = results['geometry']['location']['lng']
    except:
        pass
    return lat, lng


def getWaterTemp(beach, vicinity, country):
    try:
        beach = beach.lower()
        newBeachName = ""
        for i in range(len(beach)):
            if beach[i] == " ":
                newBeachName += "-"
            else:
                newBeachName += beach[i]
        baseURL = "https://seatemperature.info/"
        configuredURL = baseURL + newBeachName + "-water-temperature.html"
        page = requests.get(configuredURL)
        soup = BeautifulSoup(page.content, "html.parser")
        waterTemps = soup.find_all("td", class_="s38")
        waterTemp = waterTemps[0].text.strip()
        return float(waterTemp[:-2])
    except:
        country = country.lower()
        newCountry = ""
        for i in range(len(country)):
            if country[i] == " ":
                newCountry += "-"
            else:
                newCountry += country[i]
        vicinity = vicinity.split()
        town = vicinity[-1].strip()
        town = town.lower()
        baseURL = "https://seatemperature.info/"
        configuredURL = baseURL + newCountry + "/" + town + "-water-temperature.html"
        page = requests.get(configuredURL)
        soup = BeautifulSoup(page.content, "html.parser")
        waterTemps = soup.find_all("td", class_="s38")
        waterTemp = waterTemps[0].text.strip()
        return float(waterTemp[:-2])


def getWindAndTemp(beach):
    userAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36"
    lang = "en-US,en;q=0.5"

    beach = beach
    newBeachName = ""
    for i in range(len(beach)):
        if beach[i] == " ":
            newBeachName += "+"
        else:
            newBeachName += beach[i]
    baseURL = "https://www.google.com/search?q=weather+"
    configuredURL = baseURL + newBeachName

    session = requests.Session()
    session.headers['User-Agent'] = userAgent
    session.headers['Accept-Language'] = lang
    session.headers['Content-Language'] = lang
    html = session.get(configuredURL)
    # create a new soup
    soup = BeautifulSoup(html.text, "html.parser")
    wind = soup.find("span", attrs={"id": "wob_ws"}).text
    temp = soup.find("span", attrs={"id": "wob_tm"}).text
    return int(wind[:-4]), int(temp)


def calcOverall(wind, temp, waterTemp):
    windScore = 0
    tempScore = 0
    waterTempScore = 0

    # gets wind score
    if wind < 5:
        windScore = 100
    elif wind < 8:
        windScore = 90
    elif wind < 10:
        windScore = 80
    elif wind < 15:
        windScore = 70
    else:
        windScore = 60

    # gets temp score
    if temp >= 80 and temp < 93:
        tempScore = 100
    elif temp >= 93 and temp <= 100:
        tempScore = 85
    elif temp >= 70 and temp < 80:
        tempScore = 90
    elif temp >= 60 and temp < 70:
        tempScore = 75
    else:
        tempScore = 60

    # gets water temp score
    if waterTemp >= 85 and waterTemp <= 90:
        waterTempScore = 100
    elif (waterTemp >= 91 and waterTemp <= 95) or (waterTemp >= 78 and waterTemp <= 84):
        waterTempScore = 90
    elif waterTemp >= 71 and waterTemp <= 77:
        waterTempScore = 80
    elif waterTemp >= 60 and waterTemp <= 70:
        waterTempScore = 70
    else:
        waterTempScore = 60

    overall = (waterTempScore + windScore + tempScore) / 3
    overallRound = round(overall, 3)

    return overallRound


class Beach:
    def __init__(self, name, wind, temp, waterTemp):
        self.name = name
        self.wind = wind
        self.temp = temp
        self.waterTemp = waterTemp


apiKey = getAPIKey()
gmaps = googlemaps.Client(apiKey)

address, country, distance = getLocation()
address = parseAddress(address)
location = getLatLng(address, apiKey)
keyWord = "beach"
distance = milesToMeters(distance)

print("\nResults make take up to 1 minute...\n")

beaches = []

response = gmaps.places_nearby(
    location=location, keyword=keyWord, radius=distance)
beaches.extend(response.get('results'))
nextPage = response.get("next_page_token")

while nextPage:
    time.sleep(2)
    response = gmaps.places_nearby(
        location=location, keyword=keyWord, radius=distance, page_token=nextPage)
    beaches.extend(response.get('results'))
    nextPage = response.get("next_page_token")


bestBeaches = []

for beach in beaches:
    beachName = beach.get("name")
    try:
        thisWind = getWindAndTemp(beachName)[0]
        thisTemp = getWindAndTemp(beachName)[1]
        thisWaterTemp = getWaterTemp(
            beachName, beach.get("vicinity"), country)
        thisBeach = Beach(beachName, thisWind, thisTemp, thisWaterTemp)
        bestBeaches.append(thisBeach)
    except:
        pass

if len(bestBeaches) == 0:
    print("There are no beaches in your area.")
    sys.exit()

beachDict = {}

for beach in bestBeaches:
    beachDict[beach] = calcOverall(beach.wind, beach.temp, beach.waterTemp)

beachList = sorted(beachDict.items(), key=lambda x: x[1], reverse=True)

count = 1
for beach in beachList:
    print(str(count) + ". " + beach[0].name)
    print("Overall: " + str(beach[1]) + " Wind: " + str(beach[0].wind) +
          " Temperature: " + str(beach[0].temp) + " Water Temperature: " + str(beach[0].waterTemp))
    count += 1
