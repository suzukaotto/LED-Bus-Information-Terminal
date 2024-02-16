import requests, json, xmltodict

url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
params = {
    "serviceKey" : "Y+K/PG7BzlPBzLKybehRrc2U90kkXQbkuDj3DrFrnXRgL2UWCO8uIyaHlZPaKPsHPn0nCF2fcRP6eVnAUn4mUA==",
    "numOfRows"  : "100",
    "pageNo"     : "1",
    "base_date"  : "20240214",
    "base_time"  : "0500",
    "nx"         : "37",
    "ny"         : "127"
}

def xml_to_json(xml_data, indent=None):
    try:
        return json.dumps(xmltodict.parse(xml_data), indent=indent)
    except Exception as e:
        print(e)
        return

response = requests.get(url, params=params)
xml_station_data = response.content.decode('utf-8')
json_station_data = xml_to_json(xml_station_data, indent=2)

print("-- XML DATA --")
print(xml_station_data, end="\n\n")

print("-- JSON DATA --")
print(json_station_data, end="\n\n")
