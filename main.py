import asyncio
import json
from typing import Optional
import nest_asyncio

import requests as requests
from flask import Request, jsonify, make_response, Response, Flask



from domain.runner import run_browser

# Line notify token
cus_token_list = ['UHSxtDOU4FvM53JX6COB1yqoib9WKYHEMzt3sanHrPZ', 'uyPywOo1gC8gLBk7UggZgUcTafY9KOH3kFPxF6uo2KE',
                      '3IyfAaLFfsUlFuLHoIebAhfFM4ppnQxMdnSZkBnjJqP', 'glMoSqIX4Om08qC4PWrU4u4Lj65koYuJHNZ9U0rX5i6',
                      'NnHXRmcxaiavRwrOwglNKfTNX1RkHrMP8Wl24ru2VhD', 'LqWesSmdNsvMiT6D89fRjwajly7Z3u2lTy9TlPauXCt',
                      'NEgypkBtalVFNfgcjz2Cb4tn1yOxmnU1W4jylLgg67Y', 'QxIZnlpDTpcj5Um0tX7Dzwe2xcBCGkPc3QdJMyztiZA',
                      'OmJHizOPAlvG52YIyWCaKPABf78r5F2MjBQfOizSJNI']
# TODO: Change this to multiple Customer not only one
def get_data_from_api(cus_no = None):
    cus_no = 'all' if cus_no is None else cus_no
    res = None
    url = 'https://agent.onetabien.com/api.php/v1/customer/all'
    response = requests.get(url=url)
    # print(" LOG CUSTOMER INFO \n {url} \n WITH STATUS : %d" % response.status_code)
    if response.status_code == 200:
        res = response.json()
    if res is not None:
        print("LOG CUSTOMER NOW COUNT : %s" % len(res))
        if cus_no != 'all':
            return res[cus_no]
        else:
            return res
    elif res is None:
        print("LOG CUSTOMER NOW COUNT : 0")
        return res

#GCF for create a data
@functions_framework.http
def run_script_101(request: Request):
    data = get_data_from_api(0)
    return run_script_general(request, data, 0)


@functions_framework.http
def run_script_102(request: Request):
    data = get_data_from_api(1)
    return run_script_general(request, data, 1)


@functions_framework.http
def run_script_103(request: Request):
    data = get_data_from_api(2)
    return run_script_general(request, data, 2)


@functions_framework.http
def run_script_104(request: Request):
    data = get_data_from_api(3)
    return run_script_general(request, data, 3)


@functions_framework.http
def run_script_105(request: Request):
    data = get_data_from_api(4)
    return run_script_general(request, data, 4)


@functions_framework.http
def run_script_106(request: Request):
    data = get_data_from_api(5)
    return run_script_general(request, data, 5)


@functions_framework.http
def run_script_107(request: Request):
    data = get_data_from_api(6)
    return run_script_general(request, data, 6)


@functions_framework.http
def run_script_108(request: Request):
    data = get_data_from_api(7)
    return run_script_general(request, data, 7)


@functions_framework.http
def run_script_109(request: Request):
    data = get_data_from_api(8)
    return run_script_general(request, data, 8)

def get_message_from_bot( 
        id_number,
        prefix,
        name,
        last_name,
        brand,
        phone_number,
        personal_type,
        car_body_number,
        reserve_number,
        wait_sec,
        carType,
        cus_no):    

    result = asyncio.run(run_browser(
        id_number=id_number,
        prefix=prefix,
        name=name,
        last_name=last_name,
        brand=brand,
        phone_number=phone_number,
        personal_type=personal_type,
        car_body_number=car_body_number,
        reserve_number=reserve_number,
        wait_sec=wait_sec,
        carType=carType,
        cus_no=cus_no
    ))

    try:
        strMsg = result.message.split("alert")[1].split("window.location=")[0].replace(" \\r\\n","").replace("\\\"", "")[1:-3]
    except:
        strMsg = result.message

    # send log to agent web site on log     
    url = f'https://agent.onetabien.com/api.php/v1/customer/callback?msg={strMsg}'
    payload={}
    headers = {'Cookie': 'my_lang=th'}
    requests.request("GET", url, headers=headers, data=payload)
    

    # Noti line message API K'KAW
    notice_url = 'https://notify-api.line.me/api/notify'
    token = 'iwo6hYnY8XGF3833fMzoRdsNvGz5KCJQi9ldyX1cj5G'
    headers = {
    "Authorization": "Bearer " + token,
    "Content-Type": "application/x-www-form-urlencoded"
    }
    requests.post(notice_url, headers=headers, data = {'message': f"\n \n 💢 คุณ {name} {last_name} \n 💢 เลขบัตร {id_number} \n \n 📩 รายละเอีดผลการจอง \n{strMsg} \n \n ⏰ เวลา {result.executed_time} วิ"})
    
    # Noti line message API K'jade
    notice_url = 'https://notify-api.line.me/api/notify'
    token = 'HUKQNdKFkG8PywH8bRHwGVbLdruNEBnyqNctuqtOKEd'
    headers = {
    "Authorization": "Bearer " + token,
    "Content-Type": "application/x-www-form-urlencoded"
    }

    requests.post(notice_url, headers=headers, data = {'message': f"\n \n 💢 คุณ {name} {last_name} \n 💢 เลขบัตร {id_number} \n \n 📩 รายละเอีดผลการจอง \n{strMsg} \n \n ⏰ เวลา {result.executed_time} วิ"})
    return strMsg, result
    

def run_script_general(request: Request, cus_data :dict, cus_no: int):
    if cus_data is None:
        return make_response(jsonify({
            'message': 'DATA_NOT_SUPPORTED'
        }))
    id_number = cus_data['idCard']
    prefix = cus_data['title']
    name = cus_data['name']
    last_name = cus_data['lastName']
    brand = cus_data['carBrand']
    phone_number = cus_data['telNo']
    personal_type = cus_data['personalType']
    car_body_number = cus_data['carBody']
    reserve_numbers = cus_data['wantedNo']
    wait_sec = cus_data['ms'] / 1000
    carType = cus_data['carType']

    count_reserve_order = 0
    reserve_number_list = (str(reserve_numbers).strip()).split(',')
    print(reserve_number_list)
    strMsg = ''
    result = None

    if not reserve_number_list or len(reserve_number_list) < 1:
        strMsg = f"User ID : {id_number} Have no reserve numbers"
        url = f'https://agent.onetabien.com/api.php/v1/customer/callback?msg={strMsg}'
        payload={}
        headers = {'Cookie': 'my_lang=th'}
        requests.request("GET", url, headers=headers, data=payload)
        return
    
    while count_reserve_order < len(reserve_number_list):
        strMsg, result = get_message_from_bot( id_number=id_number,
            prefix=prefix,
            name=name,
            last_name=last_name,
            brand=brand,
            phone_number=phone_number,
            personal_type=personal_type,
            car_body_number=car_body_number,
            reserve_number=reserve_number_list[count_reserve_order],
            wait_sec=wait_sec,
            carType=carType,
            cus_no=cus_no)
        
        

        if 'เนื่องจากมีผู้จองเลขดังกล่าวแล้ว' in strMsg:
            count_reserve_order += 1
            continue

    return jsonify({
        'status': result.status,
        'executed_time': result.executed_time,
        'message': result.message
    })

def send_line_notify(token, message):
    notice_url = 'https://notify-api.line.me/api/notify'
    headers = {
    "Authorization": "Bearer " + token,
    "Content-Type": "application/x-www-form-urlencoded"
    }
    requests.post(notice_url, headers=headers, data = {'message': f"{message}"})


# app = Flask("Ahhhh Shzzzzzz")

# @app.route('/')
# def index():
#     return jsonify({'message': 'Hello, World!'})

# if __name__ == '__main__':
#     # Create an application context
#     nest_asyncio.apply()
#     with app.app_context():
#         data = get_data_from_api(0)
#         asyncio.get_event_loop().run_until_complete(run_script_general(Request, data, 0))
#         app.run(debug=True)

# if __name__ == '__main__':
#     data = get_data_from_api(0)
#     run_script_general(Request, data, 0)
#     cus_data = get_data_from_api()
#     cus_count = len(cus_data) # Customer count number
#     if cus_count > len(cus_token_list):
#         print("Line Notify Token is not enough for all customer,This might be not complete for all customer")

#     if cus_count >= 1:
#         for x in range(1, cus_count + 1):
#             message = f"{x} : {cus_data[x - 1]['name']} : {cus_data[x - 1]['lastName']} : {cus_data[x - 1]['idCard']} \n send link"
#             run_script_general(Request, cus_data[x - 1], x-1)
#             # send_line_notify(cus_token_list[x-1], message)
#     else:
#         print('Have no customer for now.')
