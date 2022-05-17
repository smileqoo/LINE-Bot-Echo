import os
from datetime import datetime

from flask import Flask, abort, request

# https://github.com/line/line-bot-sdk-python
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import json,requests,statistics,time

app = Flask(__name__)

tk = os.environ.get("CHANNEL_ACCESS_TOKEN")
secret = os.environ.get("CHANNEL_SECRET")
line_bot_api = LineBotApi(tk)
handler = WebhookHandler(secret)


@app.route("/", methods=["GET", "POST"])
def callback():
    if request.method == "GET":
        return "Hello Heroku"
    if request.method == "POST":
        #建立訊息
        try:
            body = request.get_data(as_text=True)
            json_data = json.loads(body)
            print(json_data)
            signature = request.headers['X-Line-Signature']
            handler = handler.handle(body,signature)
            '''
            #取得位置
            events = json_data['events']
            if events:
                events = events[0]
                msg_type = events['message']['type']
                reply_token = events['replyToken']
                
                if 'text' in msg_type:
                    msg = events['message']['text']
                    if '氣象' in msg or '雷達' in msg:
                        img = f'https://cwbopendata.s3.ap-northeast-1.amazonaws.com/MSC/O-A0058-003.png?{time.time_ns()}'
                        reply_img(tk,reply_token,img)
                    elif '地震' in msg:
                        info_data = earth_quake()
                        reply_earthquake(tk,reply_token,info_data)
                    else :                
                        reply_msg(tk,reply_token,msg)
                        
                elif 'location' in msg_type:
                    address = events['message']['address'].replace('台','臺')
                    #weather_data = current_weather(address)
                    msg = f'{address}\n\n{current_weather(address)}\n\n{aqi(address)}\n\n{forcast(address)}'
                    reply_msg(tk,reply_token,msg) #↑函數直接插入
                '''
        except InvalidSignatureError:
            abort(400)
        return 'ok'
    
#空氣品質
def aqi(address):
    city_list,site_list={},{}
    msg = '找不到空氣品質資訊'

    try:
        url = 'https://data.epa.gov.tw/api/v1/aqx_p_432?limit=1000&api_key=9be7b239-557b-4c10-9775-78cadfc555e9&sort=ImportDate%20desc&format=json'
        a_data = requests.get(url)
        a_data_json = a_data.json()
        for i in a_data_json['records']:
            city = i["County"]
            if city not in city_list:
                city_list[city]=[]
            site = i['SiteName']
            aqi = int(i["AQI"])
            status = i['Status']
            site_list[site] = {'AQI':aqi,'Status':status}
            city_list[city].append(aqi)
                
        for i in city_list:
            if i in address:
                aqi_val = round(statistics.mean(city_list[i]),0)
                aqi_status =''
                if aqi_val <= 50:
                    aqi_status = '良好'
                elif aqi_val >50 and aqi_val<=100:
                    aqi_status = '普通'
                elif aqi_val >100 and aqi_val<=150:
                    aqi_status = '對敏感族群不健康'
                elif aqi_val >150 and aqi_val<=200:
                    aqi_status = '對所有族群不健康'
                elif aqi_val >200 and aqi_val<=300:
                    aqi_status = '非常不健康'
                else:
                    aqi_status = '危害'
                msg = f'空氣品質{aqi_status} (AQI {aqi_val} )'
                break

        for i in site_list:
            if i in address:
                msg = f"空氣品質{site_list[i]['Status']} (AQI {site_list[i]['AQI']} )"
                break
        return msg
        
    except:
        print('錯誤有問題')
        return msg

#天氣預報
def forcast(address):
    area_list={}
    # 將主要縣市個別的 JSON 代碼列出
    json_api = {"宜蘭縣":"F-D0047-001","桃園市":"F-D0047-005","新竹縣":"F-D0047-009","苗栗縣":"F-D0047-013",
            "彰化縣":"F-D0047-017","南投縣":"F-D0047-021","雲林縣":"F-D0047-025","嘉義縣":"F-D0047-029",
            "屏東縣":"F-D0047-033","臺東縣":"F-D0047-037","花蓮縣":"F-D0047-041","澎湖縣":"F-D0047-045",
            "基隆市":"F-D0047-049","新竹市":"F-D0047-053","嘉義市":"F-D0047-057","臺北市":"F-D0047-061",
            "高雄市":"F-D0047-065","新北市":"F-D0047-069","臺中市":"F-D0047-073","臺南市":"F-D0047-077",
            "連江縣":"F-D0047-081","金門縣":"F-D0047-085"}

    msg = '找不到天氣預報資訊'

        

    try:
        code = 'CWB-3636F524-277C-4059-82F3-4B653C11256A'
        url = f'https://opendata.cwb.gov.tw/fileapi/v1/opendataapi/F-C0032-001?Authorization={code}&downloadType=WEB&format=JSON'
        f_data = requests.get(url)
        f_data_json = f_data.json()
        location = f_data_json['cwbopendata']['dataset']['location']  # 取得縣市的預報內容
        for i in location:
            city=i["locationName"]
            wx8=i['weatherElement'][0]['time'][0]['parameter']['parameterName']
            maxt8=i['weatherElement'][1]['time'][0]['parameter']['parameterName']
            mint8=i['weatherElement'][2]['time'][0]['parameter']['parameterName']
            ci8=i['weatherElement'][3]['time'][0]['parameter']['parameterName']
            pop8=i['weatherElement'][4]['time'][0]['parameter']['parameterName']            
            area_list[city] = f'未來8小時 {wx8}，最高溫 {maxt8} 度，最低溫 {mint8} 度，降雨機率 {pop8} %'
        
        #比對位址跟列表資訊
        for i in area_list:
            if i in address:
                msg = area_list[i]
                url = f'https://opendata.cwb.gov.tw/fileapi/v1/opendataapi/{json_api[i]}?Authorization={code}&downloadType=WEB&format=JSON'
                f_data = requests.get(url)
                f_data_json = f_data.json()
                location = f_data_json['cwbopendata']['dataset']['locations']['location']    # 取得預報內容
                break
        for i in location:
            name = i['locationName']
            wd = i['weatherElement'][10]['time'][0]['elementValue']['value']  # 綜合描述
            
            if name in address:
                msg = f'未來8小時天氣{wd}'
                break        
        return msg

    except:
        print('錯誤有問題')
        return msg

#天氣資訊
def current_weather(address):
    city_list,area_list,area_list2={},{},{} #area_list->儲存鄉鎮天氣資訊、city_list->儲存縣市天氣資訊、area_list2->如果找不到鄉鎮，讀取這個列表，平均縣市鄉鎮裡的天氣資訊
    msg = '找不到氣象資訊'

    #抓取天氣資訊
    def get_data(url):
        w_data = requests.get(url)
        w_data_json = w_data.json()
        location = w_data_json['cwbopendata']['location']
        for i in location:
            name = i['locationName'] #觀測站
            city = i['parameter'][0]['parameterValue'] #縣市
            area = i['parameter'][2]['parameterValue'] #鄉鎮
            temp = check_data(i['weatherElement'][3]['elementValue']['value']) #氣溫
            humd = check_data(round(float(i['weatherElement'][4]['elementValue']['value'])*100,1)) #濕度
            r24 = check_data(i['weatherElement'][6]['elementValue']['value']) #累積雨量
            #print(city,area,name,temp,humd,r24)

            if area not in area_list:
                area_list[area]={'temp':temp,'humd':humd,'r24':r24}
            if city not in city_list:
                city_list[city]={'temp':[],'humd':[],'r24':[]}
            city_list[city]['temp'].append(temp)
            city_list[city]['humd'].append(temp)
            city_list[city]['r24'].append(temp)

        
    #檢查資料-如果數值小於0，返回False
    def check_data(e):
        return False if float(e) < 0 else float(e)
    
    #天氣查詢
    def msg_content(loc,msg): 
        a=msg
        for i in loc:
            #print(i)
            if i in address:
                print(i) #測試
                temp = f"氣溫 {loc[i]['temp']} 度，" if loc[i]['temp'] != False else ''
                humd = f"濕度 {loc[i]['humd']}%，" if loc[i]['temp'] != False else ''
                r24 = f"累積雨量 {loc[i]['r24']}mm" if loc[i]['r24'] != False else ''
                description = f'{temp}{humd}{r24}'.strip('，')
                a = f'{description}'
                print(a) #測試
                break
        return a
    
    try:
        code = 'CWB-3636F524-277C-4059-82F3-4B653C11256A'
        get_data(f'https://opendata.cwb.gov.tw/fileapi/v1/opendataapi/O-A0001-001?Authorization={code}&downloadType=WEB&format=JSON')
        get_data(f'https://opendata.cwb.gov.tw/fileapi/v1/opendataapi/O-A0003-001?Authorization={code}&downloadType=WEB&format=JSON')

        for i in city_list:
            if i not in area_list2:#平均天氣溫度、濕度、累積雨量，存在area_list2
                area_list2[i] = {'temp':round(statistics.mean(city_list[i]['temp']),1),
                                 'humd':round(statistics.mean(city_list[i]['humd']),1),
                                 'r24':round(statistics.mean(city_list[i]['r24']),1),}
        msg = msg_content(area_list2,msg)   # 將訊息改為「大縣市」
        msg = msg_content(area_list,msg)    # 將訊息改為「鄉鎮區域」
        return msg  # 回傳 msg
    
          
    except :
        print('網址有問題')
        return msg
    
#地震資訊
def earth_quake():
    info_data = ['找不到地震資訊','https://image.16pic.com/00/53/59/16pic_5359804_s.jpg?imageView2/0/format/png']
    try:
        url = 'https://opendata.cwb.gov.tw/api/v1/rest/datastore/E-A0016-001?Authorization=CWB-3636F524-277C-4059-82F3-4B653C11256A'
        r = requests.get(url)
        r_json = r.json()
        data =r_json['records']['earthquake']
        for i in data:
            loc = i['earthquakeInfo']['epiCenter']['location'] #地點
            val = i['earthquakeInfo']['magnitude']['magnitudeValue'] #芮氏規模
            dep = i['earthquakeInfo']['depth']['value'] #深度
            eq_time = i['earthquakeInfo']['originTime'] #時間
            img = i['reportImageURI']
            msg = f'{loc}，芮氏規模{val}級，深度{dep}公里，發生時間{eq_time}'
            info_data = [msg,img]
            break
        return info_data
    except:
        return info_data


def reply_msg(tk,re_tk,msg):
    headers = {'Authorization':'Bearer '+tk,'Content-Type':'application/json'}
    body = {
            'replyToken':re_tk,
            'messages':[{
                        'type':'text',
                        'text':msg
                }
                        ]
        }
    req = requests.request('POST','https://api.line.me/v2/bot/message/reply',headers=headers,data=json.dumps(body))
    print(req.text)

def reply_img(tk,re_tk,img):
    headers = {'Authorization':'Bearer '+tk,'Content-Type':'application/json'}
    body = {
            'replyToken':re_tk,
            'messages':[{
                        'type':'image',
                        'originalContentUrl':img,
                        'previewImageUrl':img
                }
                        ]
        }
    req = requests.request('POST','https://api.line.me/v2/bot/message/reply',headers=headers,data=json.dumps(body))
    print(req.text)

def reply_earthquake(tk,re_tk,info_data):
    headers = {'Authorization':'Bearer '+tk,'Content-Type':'application/json'}
    body = {
            'replyToken':re_tk,
            'messages':[
                {
                'type':'text',
                'text':info_data[0]
                    },
                {
                'type':'image',
                'originalContentUrl':info_data[1],
                'previewImageUrl':info_data[1]
                }
                        ]
        }
    req = requests.request('POST','https://api.line.me/v2/bot/message/reply',headers=headers,data=json.dumps(body))
    print(req.text)    

    
