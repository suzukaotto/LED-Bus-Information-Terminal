import time
import sys
import os
import datetime

import os.path as osp

sys.path.append("/home/suzukaotto/BITP")

try:
    from dotenv import load_dotenv
except:
    sys.exit("dotenv module is not installed")

try:
    from python.API.func import *
except:
    sys.exit("func module not found")

try:
    load_dotenv(osp.join("python", ".env"))
    serviceKey = os.environ["SERVICE_KEY"]
except:
    sys.exit("serviceKey load failed")
    
try:
    with open(osp.join("python", "option.json"), 'r') as f:
        option = json.load(f)
except:
    sys.exit("option.json file load failed")


def get_bus_station_list() -> list:
    option_bus_station_list = option.get('busStationList', None)
    
    # 불러온 option 안에 busStationList이 없을 경우
    if option_bus_station_list == None:
        raise Exception("The busStationList Key cannot be found in the option.json file.")
    
    # option.json 파일 내의 busStationList 순서대로 역 정보 가져와 객체 return
    bus_station_list = []
    for busStation in option_bus_station_list:
        ## busStationList 안에 moblieNo 불러오기
        station_moblieNo = busStation.get('moblieNo', None)
        stationDesc      = busStation.get('stationDesc', "")
        ## busStationList 안에 moblieNo 이 없을 경우
        if station_moblieNo == None:
            raise Exception("The moblieNo Key cannot be found in the busStationList Key in the option.json file.")
        
        ## API Request
        station_data = get_station_info(serviceKey, busStation['moblieNo'])
        ## API Response data 결과 코드 확인
        api_data_error_check_value = api_data_error_check(station_data)
        if api_data_error_check_value == 0:
            ### 값이 문제 없을 경우
            pass
        elif api_data_error_check_value == 4:
            ### 결과가 존재하지 않을 경우
            print(f"There is no bus stop information corresponding to moblieNo. (Registered moblieNo: '{station_moblieNo}')")
            continue
        else:
            ### 기타 문제가 있을 경우
            print(f"An unknown error occurred and the bus stop object could not be created. (Registered moblieNo: '{station_moblieNo}')")
            raise Exception(f"An unknown error occurred and the bus stop object could not be created. (Registered moblieNo: '{station_moblieNo}')")
        
        ## 값 불러오기 및 객체 생성
        station_data = station_data['response']['msgBody']['busStationList']

        ### 역 정보 중복 시 가장 첫 번째 역 선택
        if type(station_data) == list:
            station_data = station_data[0]
        
        stationId =       station_data.get('stationId', None)
        stationNm =       station_data.get('stationName', None)
        mobileNo  =       station_data.get('mobileNo', None)
        gps_y     = float(station_data.get('y', None))
        gps_x     = float(station_data.get('x', None))
        
        bus_station_list.append(BusStation(stationId, stationNm, stationDesc, mobileNo, gps_y, gps_x))
    
    return bus_station_list

def get_station_weather_info(bus_station:BusStation, today_date):
    # 금일 최저, 최고 기온 조회 및 미세먼지 수치 조회
    response_weather_info = get_tomorrow_weater(serviceKey, bus_station.gps_y, bus_station.gps_x, today_date)
    api_data_error_check_value = api_data_error_check(response_weather_info)

    if api_data_error_check_value == 0:
        pass
    else:
        raise Exception(f"[get_station_weather_info] An unknown error occurred. ({api_data_error_check_value})")

    # 필요한 값 쿼리
    weather_items = response_weather_info['response']['body']['items']['item']

    today = today_date
    tomorrow = today + datetime.timedelta(days=1)

    today = f"{today.year}{today.month:02d}{today.day:02d}"
    tomorrow = f"{tomorrow.year}{tomorrow.month:02d}{tomorrow.day:02d}"

    tomorrow_TMN = ""
    tomorrow_TMX = ""
    tomorrow_SKY = ""
    tomorrow_PTY = ""
    
    for item in weather_items:
        try:
            if (item['category'] == "TMN") and (item['fcstDate'] == tomorrow): # 일 최저기온
                tomorrow_TMN = item['fcstValue']
        except:
            tomorrow_TMN = None
        
        try:
            if (item['category'] == "TMX") and (item['fcstDate'] == tomorrow): # 일 최저기온
                tomorrow_TMX = item['fcstValue']
        except:
            tomorrow_TMX = None
        
        try:
            if (item['category'] == "SKY") and (item['fcstDate'] == tomorrow): # 일 최저기온
                tomorrow_SKY = item['fcstValue']
        except:
            tomorrow_SKY = None
        
        try:
            if (item['category'] == "PTY") and (item['fcstDate'] == tomorrow): # 일 최저기온
                tomorrow_PTY = item['fcstValue']
        except:
            tomorrow_PTY = None
        
    return (tomorrow_TMN, tomorrow_TMX, tomorrow_SKY, tomorrow_PTY)
        

def get_arvl_bus_list(bus_station:BusStation):
    # 버스도착정보 조회, 곧 도착 버스 별 정보 조회 및 추가
    
    arvl_bus_list = []
    i = 0
    while True:
        i += 1
        if i == retry_attempt:
            print(get_log_datef(), "station arvl bus API data request failed .")
            raise Exception("The number of retry_attempts has been exceeded.")
        
        print(get_log_datef(), "station arvl bus API Request sent")
        arvl_bus_data = get_station_arvl_bus(serviceKey, bus_station.stationId)
        api_data_error_check_value = api_data_error_check(arvl_bus_data)
        if api_data_error_check_value == 0:
            break
        elif api_data_error_check_value == 4:
            arvl_bus_list.append(None)
            return 4
        else:
            print(get_log_datef(), "An unknown error occurred. Retrying ... (%d/%d)" % (retry_attempt - (i+1), retry_attempt))
            continue
    print(get_log_datef(), "station arvl bus API data received .")
        
    ## 도착 할 버스가 없는 경우 (busArrivalList None 형태일 경우)
    if arvl_bus_data['response']['msgBody']['busArrivalList'] == None:
        arvl_bus_list.append(None)
    
    ## 도착 할 버스가 한 대일 경우
    elif type(arvl_bus_data['response']['msgBody']['busArrivalList']) == dict:
        arvl_bus_data = arvl_bus_data['response']['msgBody']['busArrivalList']
        
        flag          =     arvl_bus_data.get('flag', None)
        locationNo    = int(arvl_bus_data.get('locationNo1', None))
        lowPlate      = int(arvl_bus_data.get('lowPlate1', None))
        plateNo       =     arvl_bus_data.get('plateNo', None)
        predictTime   = int(arvl_bus_data.get('predictTime1', None))
        remainSeatCnt = int(arvl_bus_data.get('remainSeatCnt1', None))
        routeId       =     arvl_bus_data.get('routeId', None)
        staOrder      = int(arvl_bus_data.get('staOrder', None))
        statioinId    =     arvl_bus_data.get('stationId', None)
        
        arvl_bus_list.append(ArvlBus(flag, locationNo, lowPlate, plateNo, predictTime, remainSeatCnt, routeId, staOrder, statioinId))
    
    # 도착할 버스가 여러 대인 경우
    elif type(arvl_bus_data['response']['msgBody']['busArrivalList']) == list:
        arvl_bus_data = arvl_bus_data['response']['msgBody']['busArrivalList']
        for arvl_bus in arvl_bus_data:
            flag          =     arvl_bus.get('flag', None)
            locationNo    = int(arvl_bus.get('locationNo1', None))
            lowPlate      = int(arvl_bus.get('lowPlate1', None))
            plateNo       =     arvl_bus.get('plateNo', None)
            predictTime   = int(arvl_bus.get('predictTime1', None))
            remainSeatCnt = int(arvl_bus.get('remainSeatCnt1', None))
            routeId       =     arvl_bus.get('routeId', None)
            staOrder      = int(arvl_bus.get('staOrder', None))
            statioinId    =     arvl_bus.get('stationId', None)
                        
            arvl_bus_list.append(ArvlBus(flag, locationNo, lowPlate, plateNo, predictTime, remainSeatCnt, routeId, staOrder, statioinId))    
    
    count = 0
    # 곧 도착 버스 별 부가정보 조회 및 추가, 곧 도착 여부 추가
    for arvl_bus in arvl_bus_list:
        count += 1
        ## 부가정보 조회 및 추가
        ### 도착할 버스가 없는 경우 건너뛰기
        if arvl_bus == None:
            break
        
        print(get_log_datef(), ">> Get additional bus information . [{}]({}/{})".format(arvl_bus.routeId, count, len(arvl_bus_list)))
        i = 0
        while True:
            i += 1
            if i == retry_attempt:
                print(get_log_datef(), "station arvl bus API data request failed .")
                raise Exception("The number of retry_attempts has been exceeded.")

            print(get_log_datef(), "route info API Request sent")
            route_data = get_route_info(serviceKey, arvl_bus.routeId)
            api_data_error_check_value = api_data_error_check(route_data)
            if api_data_error_check_value == 0:
                break
            elif api_data_error_check_value == 4:
                break
            else:
                print(get_log_datef(), "An unknown error occurred. Retrying... (%d/%d)" % (retry_attempt - (i+1), retry_attempt))
                continue
        print(get_log_datef(), "route info API API data received")
        
        i = 0
        while True:
            i += 1
            if i == retry_attempt:
                print(get_log_datef(), "station arvl bus API data request failed .")
                raise Exception("The number of retry_attempts has been exceeded.")
            
            print(get_log_datef(), "route order info API Request sent")
            route_order_data = get_route_order_info(serviceKey, arvl_bus.routeId)
            api_data_error_check_value = api_data_error_check(route_order_data)
            if api_data_error_check_value == 0:
                break
            elif api_data_error_check_value == 4:
                break
            else:
                print(get_log_datef(), "An unknown error occurred. Retrying... (%d/%d)" % (retry_attempt - (i+1), retry_attempt))
                continue
        print(get_log_datef(), "route order info API data received")
        
        route_data = route_data['response']['msgBody']['busRouteInfoItem']
        
        routeNm       = route_data.get('routeName', None)
        routeTypeCd   = route_data.get('routeTypeCd', None)
        routeNowStaNm = route_order_data['response']['msgBody']['busRouteStationList'][arvl_bus.staOrder-1-arvl_bus.locationNo]['stationName']
        
        ## 데이터 저장
        arvl_bus.routeNm       = routeNm
        arvl_bus.routeTypeCd   = routeTypeCd
        arvl_bus.routeNowStaNm = routeNowStaNm
        
        
        ## 곧 도착 여부 (3 정거장 이전인 경우)
        if arvl_bus.locationNo < 3:
            arvl_bus.is_arvl = True

    # 남은 도착 시간 순 정렬
    if arvl_bus_list[0] != None:
        arvl_bus_list.sort(key=lambda x: x.predictTime)

    
    
    return arvl_bus_list