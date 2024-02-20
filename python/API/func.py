import requests
import os
import sys
import datetime

try:
    import json
except:
    sys.exit("json module is not installed")

try:
    import xmltodict
except:
    sys.exit("xmltodict module is not installed")

# try:
#     from gtts import gTTS
# except:
#     sys.exit("gTTS module is not installed")

# try:
#     import playsound
# except:
#     sys.exit("playsound module is not installed")

# API 요청 중 에러 시 재시도 기회 횟수
retry_attempt = 30

class BusStation:
    def __init__(self, stationId, stationNm, stationDesc, mobileNo, y, x):
        self.stationId     = stationId      # 정류소 아이디
        self.stationNm     = stationNm      # 정류소명
        self.stationDesc   = stationDesc    # 정류소 부가 정보
        self.mobileNo      = mobileNo       # 정류소 모바일 번호 (5자리 숫자)
        self.gps_y         = y              # 정류소 위도
        self.gps_x         = x              # 정류소 경도
        self.arvl_bus_list = []             # 정류소 곧 도착 버스 리스트
        self.tomorrow_TMN  = None           # 정류소 금일 최저 기온
        self.tomorrow_TMX  = None           # 정류소 금일 최고 기온
        self.tomorrow_SKY  = None           # 하늘상태 [맑음(1), 구름많음(3), 흐림(4)]
        self.tomorrow_PTY  = None           # 강수형태 [없음(0), 비(1), 비/눈(2), 눈(3), 소나기(4)]
        
class ArvlBus:
    def __init__(self, flag, locationNo, lowPlate, plateNo, predictTime, remainSeatCnt, routeId, staOrder, stationId):
        self.flag          = flag           # 상태구분 (RUN: 운행 중, PASS: 운행 중, STOP: 운행종료, WAIT: 회차지 대기)
        self.locationNo    = locationNo     # 몇 정거장 전인지
        self.lowPlate      = lowPlate       # 저상 여부
        self.plateNo       = plateNo        # 차량번호
        self.predictTime   = predictTime    # 버스도착예정시간 (몇 분 후 도착 예정)
        self.remainSeatCnt = remainSeatCnt  # 빈자리 수 (-1: 정보 없음, 1-: 빈자리 수)
        self.routeId       = routeId        # 노선 아이디
        self.staOrder      = staOrder       # 정류소 순번
        self.stationId     = stationId      # 정류소 아이디
        self.is_arvl       = False          # 곧 도착 여부
        self.routeNm       = None           # 노선유형명
        self.routeTypeCd   = None           # 노선유형
        self.routeNowStaNm = None           # 노선 현재 정류소명

# 도착할 버스 없을 때
class noArvlBus:
    def __init__(self):
        self.flag          = "NOARVL"
        self.locationNo    = "NOARVL"
        self.lowPlate      = "NOARVL"
        self.plateNo       = "NOARVL"
        self.predictTime   = "NOARVL"
        self.remainSeatCnt = "NOARVL"
        self.routeId       = "NOARVL"
        self.staOrder      = "NOARVL"
        self.stationId     = "NOARVL"
        self.is_arvl       = False
        self.routeNm       = "NOARVL"
        self.routeTypeCd   = "99"
        self.routeNowStaNm = "도착할 버스가 없습니다."

def speak_text(text, lang='ko'):
    # filename='Program\\App\src\\temp_voice.mp3'
    
    # tts = gTTS(text=text, lang=lang)
    # tts.save(filename)
    # playsound.playsound(filename)
    # os.remove(filename)
    
    print("SPEAKTEXT |", text)

    pass

def get_route_order_info(serviceKey, routeId):
    url = 'http://apis.data.go.kr/6410000/busrouteservice/getBusRouteStationList'
    params = {
        'serviceKey' : serviceKey,
        'routeId'  : routeId
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    response = xml_to_dict(response.content)

    return response
    

def get_route_info(serviceKey, routeId):
    url = 'http://apis.data.go.kr/6410000/busrouteservice/getBusRouteInfoItem'
    params = {
        'serviceKey' : serviceKey,
        'routeId'  : routeId
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    response = xml_to_dict(response.content)

    return response

def get_station_arvl_bus(serviceKey, stationId):
    url = 'http://apis.data.go.kr/6410000/busarrivalservice/getBusArrivalList'
    params = {
        'serviceKey' : serviceKey,
        'stationId'  : stationId
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    response = xml_to_dict(response.content)

    return response

def get_station_info(serviceKey, keyword):
    url = 'http://apis.data.go.kr/6410000/busstationservice/getBusStationList'
    params = {
        'serviceKey' : serviceKey,
        'keyword'    : keyword
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    response = xml_to_dict(response.content)

    return response

def get_tomorrow_weater(serviceKey:str, today_date:str):
    url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
    params = {
        "serviceKey" : serviceKey,
        "numOfRows"  : "1000",
        "pageNo"     : "1",
        "base_date"  : today_date,
        "base_time"  : "0500",
        "nx"         : "37",
        "ny"         : "127"
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    response = xml_to_dict(response.content, indent=2)
    
    return response

def get_now_f_dust_info(serviceKey):
    url = "http://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getCtprvnRltmMesureDnsty"
    params = {
        "serviceKey" : serviceKey,
        "returnType" : "xml",
        "numOfRows"  : 100,
        "pageNo"     : 1,
        "sidoName"   : "경기",
        "ver"        : "1.0",
    }
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    response = xml_to_dict(response.content, indent=2)
    
    return response

def api_data_error_check(response_data, print_normal_result:bool = False) -> int:
    errData = response_data.get('OpenAPI_ServiceResponse', None)
    
    if errData == None:
        # 일반 response 시
        errData = response_data['response']['msgHeader']
        resultCode = int(errData['resultCode'])
        resultMsg  = get_api_result_code_message(resultCode)
        
        if print_normal_result:
            print(get_log_datef(), f"[api_data_error_check]", f"{resultCode} {resultMsg}")
            
        if resultCode == 0:
            # 정상 작동
            return resultCode
        
        elif resultCode == 4:
            # 결과가 존재하지 않을 경우만
            print(get_log_datef(), f"[api_data_error_check]", f"{resultCode} {resultMsg}")
            return resultCode
        
        else:
            # 이 외의 모든 에러
            print(get_log_datef(), f"[api_data_error_check]", f"{resultCode} {resultMsg}")
            return resultCode

    else:
        # OpenAPI_ServiceResponse 시
        errData = errData['cmmMsgHeader']
        
        errMsg           = errData['errMsg']
        returnAuthMsg    = errData['returnAuthMsg']
        returnReasonCode = int(errData['returnReasonCode'])
        
        print(get_log_datef(), f"[api_data_error_check]", f"{errMsg} {returnReasonCode} {returnAuthMsg}")
        return returnReasonCode

def get_api_result_code_message(resultCode:int) -> str:
    resultMessages = {
        0:  "정상적으로 처리되었습니다.",
        1:  "시스템 에러가 발생하였습니다.",
        2:  "필수 요청 Parameter 가 존재하지 않습니다.",
        3:  "필수 요청 Parameter 가 잘못되었습니다.",
        4:  "결과가 존재하지 않습니다.",
        5:  "필수 요청 Parameter(인증키) 가 존재하지 않습니다.",
        6:  "등록되지 않은 키입니다.",
        7:  "사용할 수 없는(등록은 되었으나, 일시적으로 사용 중지된) 키입니다.",
        8:  "요청 제한을 초과하였습니다.",
        20: "잘못된 위치로 요청하였습니다. 위경도 좌표값이 정확한지 확인하십시오.",
        21: "노선번호는 1자리 이상 입력하세요.",
        22: "정류소명/번호는 1자리 이상 입력하세요.",
        23: "버스 도착 정보가 존재하지 않습니다.",
        31: "존재하지 않는 출발 정류소 아이디(ID)/번호입니다.",
        32: "존재하지 않는 도착 정류소 아이디(ID)/번호입니다.",
        99: "API 서비스 준비중입니다."
    }
    
    return resultMessages.get(resultCode, "알 수 없는 코드입니다.")

def get_open_api_result_code_message(resultCode:int) -> str:
    resultMessages = {
        0:  "정상",
        1:  "어플리케이션 에러",
        2:  "데이터베이스 에러",
        3:  "데이터없음 에러",
        4:  "HTTP 에러",
        5:  "서비스 연결실패 에러",
        10: "잘못된 요청 파라메터 에러",
        11: "필수요청 파라메터가 없음",
        12: "해당 오픈API서비스가 없거나 폐기됨",
        20: "서비스 접근거부",
        21: "일시적으로 사용할 수 없는 서비스 키",
        22: "서비스 요청제한횟수 초과에러",
        30: "등록되지 않은 서비스키",
        31: "기한만료된 서비스키",
        32: "등록되지 않은 IP",
        33: "서명되지 않은 호출",
        99: "기타에러"
    }
    
    return resultMessages.get(resultCode, "알 수 없는 코드입니다.")

def check_internet_connection():
    try:
        response = requests.get("http://www.google.com", timeout=5)
        if response.status_code == 200:
            return True
    except requests.ConnectionError:
        print(get_log_datef(), "[Check_Internet_Connection]", "Connection Error")
        return False
    except:
        print(get_log_datef(), "[Check_Internet_Connection]", "Connection Error")
        return False

def xml_to_dict(xml_data, indent=4) -> json:
    try:
        json_data = json.dumps(xmltodict.parse(xml_data), indent=indent)
        return json.loads(json_data)
    except Exception as e:
        print(e)
        return None

def get_log_datef() -> str:
    current_time = datetime.datetime.now()
    date_format = current_time.strftime("[%H:%M:%S.%f]")
    
    return date_format

def cls():
    os.system('cls')
