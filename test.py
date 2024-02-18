import requests, json, xmltodict, datetime

url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
params = {
    "serviceKey" : "Y+K/PG7BzlPBzLKybehRrc2U90kkXQbkuDj3DrFrnXRgL2UWCO8uIyaHlZPaKPsHPn0nCF2fcRP6eVnAUn4mUA==",
    "numOfRows"  : "1000",
    "pageNo"     : "1",
    "base_date"  : "20240217",
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
xml_weather_data = response.content.decode('utf-8')
json_weather_data = xml_to_json(xml_weather_data, indent=2)

print("-- XML DATA --")
print(xml_weather_data, end="\n\n")

print("-- JSON DATA --")
print(json_weather_data, end="\n\n")

print("-- QUERY DATA --")
json_weather_data = json.loads(json_weather_data)
weather_items = json_weather_data['response']['body']['items']['item']

today = datetime.datetime.now()
tomorrow = today + datetime.timedelta(days=1)

today = f"{today.year}{today.month:02d}{today.day:02d}"
tomorrow = f"{tomorrow.year}{tomorrow.month:02d}{tomorrow.day:02d}"


for item in weather_items:
    if (item['category'] == "TMN") and (item['fcstDate'] == tomorrow): # 일 최저기온
        print(f"일 최저기온: {item['fcstValue']}°C {item['fcstDate']}")
        
    if (item['category'] == "TMX") and (item['fcstDate'] == tomorrow): # 일 최저기온
        print(f"일 최고기온: {item['fcstValue']}°C {item['fcstDate']}")
    