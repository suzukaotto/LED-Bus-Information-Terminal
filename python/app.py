#!/usr/bin/env python
import time
import sys
import math
import random
import os
import threading
import tqdm
from datetime import datetime


try:
    from rgbmatrix import RGBMatrix, RGBMatrixOptions
except:
    sys.exit('RGBMatrix library is not installed.\n')

try:
    from PIL import Image, ImageDraw, ImageFont
except:
    sys.exit('PIL library is not installed.\n')
    
try:
    sys.path.append("/home/suzukaotto/BITP")
    
    import python.API.app as API
    
except Exception as e:
    print(e)
    sys.exit('API module is not installed.\n')


font_path5             = '/home/suzukaotto/BITP/fonts/SCDream3.otf'
font_path12            = '/home/suzukaotto/BITP/fonts/SCDream5.otf'
font_path14            = '/home/suzukaotto/BITP/fonts/SCDream5.otf'
font_path16            = '/home/suzukaotto/BITP/fonts/SCDream5.otf'
bus_icon_path          = "python/icon/BUS.png"
bus_lowPlate_icon_path = "python/icon/BUS_lowPlate.png"

class matrixManager:
    def __init__(self):
        # Configuration for the matrix
        # https://github.com/hzeller/rpi-rgb-led-matrix/blob/master/include/led-matrix.h#L57
        options = RGBMatrixOptions()
        options.hardware_mapping = 'adafruit-hat'  # If you have an Adafruit HAT: 'adafruit-hat'
        options.rows = 32
        options.cols = 64
        options.chain_length = 7
        options.pixel_mapper_config = "V-mapper;Rotate:270"
        options.pwm_lsb_nanoseconds = 50
        options.gpio_slowdown = 4
        options.pwm_bits = 5
        options.pwm_dither_bits = 0
        options.show_refresh_rate = False
        self.matrix = RGBMatrix(options = options)
        
        self.size = (self.matrix.width, self.matrix.height)
        
        self.font5  = ImageFont.truetype(font_path5,   5)
        self.font12 = ImageFont.truetype(font_path12, 12)
        self.font14 = ImageFont.truetype(font_path14, 14)
        self.font16 = ImageFont.truetype(font_path16, 16)
        
        # 현재버스위치 표시 관련
        self.x_loca_bus_now_sta = [132, 132, 132, 39]
        self.bus_now_sta_text_delay = [30, 30, 30, 30]
    
    def system_test(self, num_shapes=10):
        print(f"----- System Testing -----")
        
        canvas = Image.new('RGB', self.size, "black")
        draw = ImageDraw.Draw(canvas)
        
        draw.rectangle(((0, 0), (self.size[0], self.size[1])), "white")
        self.refresh(canvas)
        # time.sleep(1000)
        
        test_color = ["red", "lime", "blue", "white"]
        
        for color in test_color:
            draw.rectangle(((0, 0), (self.size[0], self.size[1])), color)
            self.refresh(canvas)
            time.sleep(1)
        
        draw.rectangle(((0, 0), (self.size[0], self.size[1])), "black")
        self.refresh(canvas)
        
        print(f"--------------------------")
        
        return 0
    
    def text_page(self, set_text=""):
        canvas = Image.new('RGB', self.size, "black")
        draw = ImageDraw.Draw(canvas)
        ## 안티에일리어싱 해제
        draw.fontmode="1"
        
        if type(set_text) == str:
            draw.text((1, 1), set_text, "white", self.font12)
            
        elif type(set_text) == list:
            x_loca_row = [0, 13, 26, 39, 51]
            
            i = 0
            for text in set_text:
                if i > 4:
                    break
                
                draw.text((1, x_loca_row[i]), text, "white", self.font12)
                i += 1
            
        self.refresh(canvas)
    
    def get_text_width(self, text, font) -> int:
        dummy_img = Image.new('RGB', (1, 1))
        draw = ImageDraw.Draw(dummy_img)
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]  # Right - Left
        return text_width
    
    def bus_arvl_page(self, bus_station:dict):
        # 도착할 버스 리스트
        bus_arvl_lists = []
        # 곧 도착 버스 텍스트
        bus_arvl_soon_text = ""
        
        for arvl_bus_list in bus_station.arvl_bus_list:
            # print(arvl_bus_list.routeNm, arvl_bus_list.routeNowStaNm)
            if arvl_bus_list.is_arvl:
                bus_arvl_soon_text += f"{arvl_bus_list.routeNm}"
                if arvl_bus_list.remainSeatCnt != -1:
                    bus_arvl_soon_text += f"({arvl_bus_list.remainSeatCnt})"
                bus_arvl_soon_text += ","
            else:
                bus_arvl_lists.append(arvl_bus_list)
        
        # 고정 변수
        y_loca_col = [0, 13, 26, 39, 52]
        x_loca_row = [0, 10, 63, 93, 130]
        x_loca_row_bus_arvl = [0, 40, 40]
        
        bus_now_sta_text_delay = 30
        bus_now_sta_text_move_count = 0
        bus_now_sta_text_move_bool  = False
        
        chunk_size = 3
        arvl_bus_list_chunks = [bus_arvl_lists[i:i+chunk_size] for i in range(0, len(bus_arvl_lists), chunk_size)]
        #   나눈 데이타            전체 데이타
        for arvl_bus_list_chunk in arvl_bus_list_chunks:
            bus_arvl_lists = []
            for arvl_bus_list in arvl_bus_list_chunk:
                bus_arvl_lists.append(arvl_bus_list)
            
            # 픽셀 이동 
            canvas = Image.new('RGB', self.size, "black")
            draw = ImageDraw.Draw(canvas)
            ## 안티에일리어싱 해제
            draw.fontmode="1"
            
            
            x_loca_bus_now_sta = [x_loca_row[4], x_loca_row[4], x_loca_row[4]]
            
            bus_icon = Image.open(bus_icon_path)
            bus_lp_icon = Image.open(bus_lowPlate_icon_path)
                        
            # 고정 문구 출력
            ### 최상단 버스 "정류소명(모바일번호)"" 출력
            stationTitle_text  = "%s (%s)" % (bus_station.stationNm, bus_station.mobileNo)
            draw.text(((self.size[0]-self.get_text_width(stationTitle_text, self.font12))//2 , y_loca_col[0]), stationTitle_text, 'white', self.font12);
            
            # 한 프레임 출력
            for i in range(0, 120+1):
                for l in range(0, len(bus_arvl_lists)):
                    # 버스 한 대 데이타
                    arvl_bus_list = bus_arvl_lists[l]
                    
                    # 문구 크기 계산
                    bus_now_sta_text      = arvl_bus_list.routeNowStaNm
                    bus_now_sta_text_size = self.get_text_width(bus_now_sta_text, self.font12)
                    
                    # 버스 현재 정류소 문구 크기가 화면을 넘을 경우
                    if not (self.size[0] - x_loca_row[4]) >= bus_now_sta_text_size:
                        bus_now_sta_text = (bus_now_sta_text + " ") * math.ceil(200/bus_now_sta_text_size)
                        if i > 30:
                            x_loca_bus_now_sta[l] -= 1
                    
                    ## 버스 현재 정류소 출력
                    draw.rectangle(((0, y_loca_col[l+1]), (self.size[0], y_loca_col[l+2]-1)), "black")
                    draw.text((x_loca_bus_now_sta[l], y_loca_col[l+1]), bus_now_sta_text, 'white', self.font12);
                    draw.rectangle(((0, y_loca_col[l+1]), (x_loca_row[4]-1, y_loca_col[l+2]-1)), "black")
                    
                    ## 혼잡도 출력
                    if (arvl_bus_list.remainSeatCnt != -1) and (type(arvl_bus_list.remainSeatCnt) == int):
                        draw.text((x_loca_row[2], y_loca_col[l+1]), f"({arvl_bus_list.remainSeatCnt})", 'red', self.font12);
                    elif arvl_bus_list.remainSeatCnt == "여유":
                        draw.text((x_loca_row[2], y_loca_col[l+1]), f"({arvl_bus_list.remainSeatCnt})", 'magenta', self.font12);
                    elif arvl_bus_list.remainSeatCnt == "보통":
                        draw.text((x_loca_row[2], y_loca_col[l+1]), f"({arvl_bus_list.remainSeatCnt})", 'blue', self.font12);
                    elif arvl_bus_list.remainSeatCnt == "혼잡":
                        draw.text((x_loca_row[2], y_loca_col[l+1]), f"({arvl_bus_list.remainSeatCnt})", 'red', self.font12);
                    
                    
                    ## 버스 도착 예정 시간 출력
                    if not arvl_bus_list.predictTime == "NOARVL":
                        draw.text((x_loca_row[3], y_loca_col[l+1]) ,  f"{arvl_bus_list.predictTime}분", 'aqua', self.font12);
                    
                    if not arvl_bus_list.routeNm == "NOARVL":
                        # 노선 번호 출력
                        draw.text((x_loca_row[1], y_loca_col[l+1]), arvl_bus_list.routeNm, 'white', self.font12);
                    
                    # 버스 아이콘 출력
                    bus_icon_color = {
                        "11" : "red",         # 직행좌석형시내버스 (5001, 5005)
                        "13" : "lime",        # 일반형시내버스 (66-4, 10)
                        "14" : "red",         # 광역급행형시내버스
                        "30" : "yellow",      # 마을버스 (5)
                        "43" : "darkviolet",  # 시외버스(8342, 8343)
                        "51" : "sienna"       # 리무진공항버스(8165)
                    }
                    ## 저상 여부 아이콘 변경
                    if arvl_bus_list.lowPlate == 1:
                        draw.bitmap((x_loca_row[0], y_loca_col[l+1]), bus_lp_icon, bus_icon_color.get(arvl_bus_list.routeTypeCd, "white"));
                    elif arvl_bus_list.lowPlate == 0:
                        draw.bitmap((x_loca_row[0], y_loca_col[l+1]), bus_icon, bus_icon_color.get(arvl_bus_list.routeTypeCd, "white"));
                    # print(arvl_bus_list.routeNm, arvl_bus_list.routeTypeCd)
                
                bus_arvl_soon_text_size = self.get_text_width(bus_arvl_soon_text[:-1], self.font12)
                if not (self.size[0] - (x_loca_row_bus_arvl[1]-1)) - bus_arvl_soon_text_size >= 0:
                    if bus_now_sta_text_delay > 0:
                        bus_now_sta_text_delay -= 1
                    else:
                        if (self.get_text_width(bus_arvl_soon_text[:-1], self.font12) - (self.size[0] - (x_loca_row_bus_arvl[1]-1))) == bus_now_sta_text_move_count:
                            if bus_now_sta_text_move_bool == False:
                                bus_now_sta_text_delay = 30
                                bus_now_sta_text_move_bool = True
                            else:
                                bus_now_sta_text_move_bool = False
                                bus_now_sta_text_delay = 30
                                x_loca_row_bus_arvl[2] = 40
                                bus_now_sta_text_move_count = 0
                        else:
                            x_loca_row_bus_arvl[2] -= 1
                            bus_now_sta_text_move_count += 1
                        
                
                # 곧 도착 버스 문구 출력
                draw.rectangle(((x_loca_row_bus_arvl[1], y_loca_col[4]), (self.size[0], self.size[1])), "black")
                draw.text((x_loca_row_bus_arvl[2], y_loca_col[4]), bus_arvl_soon_text[:-1], 'white', self.font12)
                
                # 곧 도착 버스 출력
                draw.rectangle(((x_loca_row_bus_arvl[0], y_loca_col[4]), (x_loca_row_bus_arvl[1]-1, self.size[1])), "black")
                draw.text((x_loca_row_bus_arvl[0], y_loca_col[4]), "곧도착:", 'white', self.font12)
                
                self.refresh(canvas)
                time.sleep(0.025)
                
    
    def etc_page(self, bus_station:dict):
        canvas = Image.new('RGB', self.size, "black")
        draw = ImageDraw.Draw(canvas)
        ## 안티에일리어싱 해제
        draw.fontmode="1"
        
        y_loca_col = [1, 16, 32, 48]
        x_loca_row = [1, 74, 83]
        
        ultrafine_dust_text = "보통"
        fine_dust_text      = "좋음"
        tomo_temp_text      = "%d°C~%d°C" % (-3, 9)
        
        now = datetime.now()
        weekday_korean = ["월", "화", "수", "목", "금", "토", "일"]
        weekday_index = now.weekday()
        weekday_korean_str = weekday_korean[weekday_index]
        
        date_text = now.strftime("%m/%d({}) %H시%M분".format(weekday_korean_str))
        
        # Calculate date_text width using textbbox
        date_text_bbox = draw.textbbox((0, 0), date_text, font=self.font14)
        date_text_width = date_text_bbox[2] - date_text_bbox[0]
        date_text_x = (self.size[0] - date_text_width) // 2
        
        draw.text((date_text_x, y_loca_col[0]), date_text,      "white", self.font14)
        draw.text((x_loca_row[0], y_loca_col[1]), "초미세먼지", "white", self.font14)
        draw.text((x_loca_row[0], y_loca_col[2]), "미세먼지",   "white", self.font14)
        draw.text((x_loca_row[0], y_loca_col[3]), "내일의날씨", "white", self.font14)
        
        draw.text((x_loca_row[1], y_loca_col[1]), ":", "white", self.font14)
        draw.text((x_loca_row[1], y_loca_col[2]), ":", "white", self.font14)
        draw.text((x_loca_row[1], y_loca_col[3]), ":", "white", self.font14)
        
        draw.text((x_loca_row[2], y_loca_col[1]), ultrafine_dust_text, "yellow", self.font14)
        draw.text((x_loca_row[2], y_loca_col[2]), fine_dust_text,      "lime", self.font14)
        draw.text((x_loca_row[2], y_loca_col[3]), tomo_temp_text,      "white", self.font14)
        
        self.refresh(canvas)    
    
    def refresh(self, image: Image.Image):
        self.matrix.SetImage(image.convert('RGB'))
    
    def program_kill(self, reason:str=""):
        for i in range(3, 0, -1):
            self.text_page([f"프로그램 종료 됨 .. ({i})", reason])
            time.sleep(1)
        print(API.get_log_datef()+" Program Ended")
        self.text_page()
        exit(0)
        

def update_bus_station_list():
    print(f"----- Getting bus station list -----")
    
    print(API.get_log_datef(), "Bus station list API Request sent")
    bus_station_list = API.get_bus_station_list()
    
    print(API.get_log_datef(), "Got bus station list")
    
    print(f"------------------------------------")
    
    return bus_station_list

def update_station_arvl_bus_list(self):
    print(f"----- Getting arvl bus list -----")
    i = 0
    for bus_station in self.bus_station_list:
        print(API.get_log_datef(), f"Getting arvl bus list ... ({i+1}/{len(self.bus_station_list)}) : {bus_station.stationNm}({bus_station.mobileNo})")
        ## 인터넷 연결 확인
        if not API.check_internet_connection():
            continue
        
        arvl_bus_list_data = API.get_arvl_bus_list(self.bus_station_list[i])
        if arvl_bus_list_data == 4:
            arvl_bus_list_data = []
            arvl_bus_list_data.append(API.noArvlBus())
        
        bus_station.arvl_bus_list = arvl_bus_list_data
        
        print(API.get_log_datef(), f"Got arvl bus list .       ({i+1}/{len(self.bus_station_list)}) : {bus_station.stationNm}({bus_station.mobileNo})")
        i+=1
        
    print(f"-------------------------------------")

def thread_update_arvl_bus_list(manager):
    while True:
        try:
            while True:
                for i in tqdm.trange(30, desc="Refresh arvl bus list ..."):
                    time.sleep(1)
                update_station_arvl_bus_list(manager)
        except KeyboardInterrupt:
            print("Thread Killed: KeyboardInterrupt")
        except Exception as e:
            print(API.get_log_datef(), f"!! An unknown error occurred in thread_update_arvl_bus_list!")
            print(API.get_log_datef(), f"!! Error: {e}")
            print(API.get_log_datef(), f"!! Restart thread_update_arvl_bus_list .")

first_execution = True
def scheduled_task(scheduled_hour:int=20):
    global first_execution
    
    current_hour = time.localtime().tm_hour
    
    while current_hour != scheduled_hour and not first_execution:
        time.sleep(300)
        current_time = time.localtime()
        current_hour = current_time.tm_hour
    
    first_execution = False
    print("작업이 잘 실행되었습니다.")
    
    threading.Timer(24 * 60 * 60, scheduled_task, args=[scheduled_hour]).start()


if __name__ == '__main__':
    manager = matrixManager()
    threads = []
    
    thread_update_bus_arvl_info = threading.Thread(target=thread_update_arvl_bus_list, args=(manager,))
    thread_update_bus_arvl_info.daemon = True
    
    scheduled_task_thread = threading.Thread(target=scheduled_task)
    scheduled_task_thread.daemon = True
    
    
    threads.append(thread_update_bus_arvl_info)
    
    print(end="\n\n")
    
    # manager.system_test()
    
    print("---------Program Start---------")
    
    manager.text_page(["초기화 중... (1/4)", "하드웨어 시간 갱신 중 ..."])
    os.system("sudo hwclock -w")
    
    
    manager.text_page(["초기화 중... (2/4)", "scheduled task 생성 중 ..."])
    scheduled_task_thread.start()
    
    for i in range(0, API.retry_attempt+1):
        try:
            manager.text_page(["초기화 중... (3/4)", "버스정류소 정보 불러오는 중 ..."])
            bus_station_list = update_bus_station_list()
            manager.bus_station_list = bus_station_list
            break
        except KeyboardInterrupt:
            manager.program_kill("KeyboardInterrupt")
        except:
            if i == API.retry_attempt:
                for l in range(300, 0, -1):
                    manager.text_page(["초기화 중... (3/4)", "버스정류소 정보 불러오는 중 ...", "정보를 불러오는 도중 에러가 발생했습니다.", "재시도에 실패했습니다.", f"자동 종료까지 .. ({l})"])
                    time.sleep(1)
                manager.program_kill()
                
            else:
                print("An unknown error occurred and we will retry. (%d/%d)" % (API.retry_attempt - (i+1), API.retry_attempt))
                manager.text_page(["초기화 중... (3/4)", "버스정류소 정보 불러오는 중 ...", "정보를 불러오는 도중 에러가 발생했습니다.", "재시도 중... (%d/%d)" % (API.retry_attempt - (i+1), API.retry_attempt)])
                time.sleep(0.5)
                continue
    
    
    for i in range(0, API.retry_attempt+1):
        try:
            manager.text_page(["초기화 중... (4/4)", "곧 도착 버스 정보 불러오는 중 ..."])
            update_station_arvl_bus_list(manager)
            break
        except KeyboardInterrupt:
            manager.program_kill("KeyboardInterrupt")
        except:
            print("An unknown error occurred and we will retry. (%d/%d)" % (API.retry_attempt - (i+1), API.retry_attempt))
            manager.text_page(["초기화 중... (4/4)", "곧 도착 버스 정보 불러오는 중 ...", "정보를 불러오는 도중 에러가 발생했습니다.", "재시도 중... (%d/%d)" % (API.retry_attempt - (i+1), API.retry_attempt)])
            time.sleep(0.5)
            continue
    
    print("-------------------------------")
    
    thread_update_bus_arvl_info.start()
    
    while 1:
        if manager.bus_station_list == []:
            try:
                for i in range(300, 0, -6):
                    manager.text_page(["불러와진 정류소가 없습니다.", f"자동 종료까지 ... ({i})"])
                    time.sleep(1)
                    manager.text_page(["불러와진 정류소가 없습니다.", f"자동 종료까지 ... ({i-1})"])
                    time.sleep(1)
                    manager.text_page(["불러와진 정류소가 없습니다.", f"자동 종료까지 ... ({i-2})"])
                    time.sleep(1)
                    manager.text_page(["options.json 파일을 확인해주세요.", f"자동 종료까지 ... ({i-3})"])
                    time.sleep(1)
                    manager.text_page(["options.json 파일을 확인해주세요.", f"자동 종료까지 ... ({i-4})"])
                    time.sleep(1)
                    manager.text_page(["options.json 파일을 확인해주세요.", f"자동 종료까지 ... ({i-5})"])
                    time.sleep(1)
            except KeyboardInterrupt:
                manager.program_kill("KeyboardInterrupt")
            
            manager.program_kill("불러와진 정류소가 없습니다.")
            
        
        for bus_station in manager.bus_station_list:
            while True:
                try:
                    for i in range(0, 3+1):
                        manager.bus_arvl_page(bus_station)
                except KeyboardInterrupt:
                    manager.program_kill("KeyboardInterrupt")
                except:
                    continue            
                break
            
            for i in range(0, 50):
                while True:
                    try:
                        manager.etc_page(bus_station)
                    except KeyboardInterrupt:
                        manager.program_kill("KeyboardInterrupt")
                    except:
                        continue            
                    break
                time.sleep(0.1)
    
    manager.program_kill()