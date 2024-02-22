import asyncio
import os
import re
import time
import random
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
from pyppeteer.dialog import Dialog
from pyppeteer_stealth import stealth
import pause as pause
import requests as requests
from bs4 import BeautifulSoup
from pyppeteer import launch, chromium_downloader
from pyppeteer.page import Page

from domain.entity import MakeDltReserveResponse, DltReserveInfo, KeyValuePair

chromium_executable = {
 'linux': Path(os.getcwd() + '/chromium_worker/linux/chrome-linux/chrome'),  # use in google cloud function
}


SYSTEM_CLOSE = ['ปิดระบบจองเลข']
SYSTEM_WAIT = ['ขณะนี้ยังไม่ถึงเวลาเปิดระบบจองเลขทะเบียนเปิดระบบจองเลขทะเบียนเวลา 10:00:00 น.', 'ขณะนี้ยังไม่ถึงเวลาเปิดระบบจอง']

# Main page for reserve dlt
url = "https://reserve.dlt.go.th/reserve/v2/?menu=resv_m&state="

# time for retry in main page
numberForLoopTry = 500

# Line Token
cus_token_list = ['UHSxtDOU4FvM53JX6COB1yqoib9WKYHEMzt3sanHrPZ', 'uyPywOo1gC8gLBk7UggZgUcTafY9KOH3kFPxF6uo2KE',
                      '3IyfAaLFfsUlFuLHoIebAhfFM4ppnQxMdnSZkBnjJqP', 'glMoSqIX4Om08qC4PWrU4u4Lj65koYuJHNZ9U0rX5i6',
                      'NnHXRmcxaiavRwrOwglNKfTNX1RkHrMP8Wl24ru2VhD', 'LqWesSmdNsvMiT6D89fRjwajly7Z3u2lTy9TlPauXCt',
                      'NEgypkBtalVFNfgcjz2Cb4tn1yOxmnU1W4jylLgg67Y', 'QxIZnlpDTpcj5Um0tX7Dzwe2xcBCGkPc3QdJMyztiZA',
                      'OmJHizOPAlvG52YIyWCaKPABf78r5F2MjBQfOizSJNI']

def get_executable_chromium_path() -> Optional[Path]:
    exec_path = chromium_executable.get(chromium_downloader.current_platform())
    return exec_path

def check_words_in_text(words, text):
    print('+__LOG : Check wording__+')
    triggered_words = []
    for word in words:
        if word.lower() in text.lower():
            triggered_words.append(word)
    return bool(triggered_words)

async def get_request(dialog_message, wait_sec, page: Page, data: DltReserveInfo, php_session_id: str) -> Optional[str]:
    print(f"[{data.reserve_number}]GET REQUEST START---")
    print(f"[{data.reserve_number}]PHP SESSION ID : {php_session_id}")

    message = ''
    navigationPromise = asyncio.gather(page.waitForNavigation())
    start_index = None
    for i in range(numberForLoopTry):
        try:
            print(f"[{data.reserve_number}]START x{i} TIMES GETING DATA FOR 60 SEC...")
            await navigationPromise
            try:
                # Wait for the elements to appear
                element = await page.waitForSelector('#center', {'visible': True})
                text = await page.evaluate('(element) => element.textContent', element)
                start_index = text.find('*/')
                if start_index is not None:
                    message = " ".join(str(text[start_index + 2:].strip()).split())
                else:
                    message = " ".join(str(text.strip()).split())
                print('+__LOG : GET TEXT %s' % message)
                if message is None:
                    await page.reload()
                    await cooldown(page, 5)
                    element = await page.waitForSelector('#center', {'visible': True})
                    text = await page.evaluate('(element) => element.textContent', element)
                    start_index = text.find('*/')
                    if start_index is not None:
                        message = " ".join(str(text[start_index + 2:].strip()).split())
                    else:
                        message = " ".join(str(text.strip()).split())
                    print('+__LOG : GET TEXT SECOND %s' % message)
                else:
                    return message
                    
            except Exception as e:
                print(traceback.format_exc())
                str_e = str(e)
                print(f"str_e :{str_e}")
                await page.reload()
                continue

        except Exception as e:
            print(traceback.format_exc())
            str_e = str(e)
            print(f"str_e :{str_e}")
            if "Navigation Timeout Exceeded" in str_e:
                await page.reload()
                continue
            if "Execution context was destroyed" in str_e:
                await page.reload()
                continue
            # if another error please break
            message = dialog_message[-1]
            # break
            return ''
    return " ".join(str(message.strip()).split()) 


async def check_system_close(page: Page):
    print("++__LOG CHECK SYSTEM CLOSE__++")
    # xpath = '//*[@id="center"]/div/center'
    # await page.waitForXPath(xpath, timeout=5000)
    # Get all matching elements
    element = await page.waitForSelector('#center', {'visible': True})
    text = await page.evaluate('(element) => element.textContent', element)
    text = text.strip()
    if not text:
        return False, text
    return check_words_in_text(SYSTEM_CLOSE, text), text

async def check_system_wait(page: Page):
    print("++__LOG CHECK SYSTEM WAIT__++")
    # xpath = '//*[@id="center"]/div/center'
    # await page.waitForXPath(xpath, timeout=5000)
    # Get all matching elements
    element = await page.waitForSelector('#center', {'visible': True})
    text = await page.evaluate('(element) => element.textContent', element)
    text = text.strip()
    if not text:
        print('+__LOG : TEXT IS : ', text)
        return True, text
    return check_words_in_text(SYSTEM_WAIT, text), text

def get_value(input_list, name) -> str:
    result = list(filter(lambda p: p.get('name') == name, input_list))
    if not result:
        raise RuntimeError
    return result[0].get('value') or ''


def make_DltReserveInfo(input_list, reserve_number: str, prefix: str,) -> DltReserveInfo:
    return DltReserveInfo(
            action=get_value(input_list=input_list, name='action'),
            mode=get_value(input_list=input_list, name='mode'),
            group=get_value(input_list=input_list, name='group'),
            number_reserve=get_value(input_list=input_list, name='number_reserve'),
            open=get_value(input_list=input_list, name='open'),
            close=get_value(input_list=input_list, name='close'),
            confirm=get_value(input_list=input_list, name='confirm'),
            car_type=get_value(input_list=input_list, name='car_type'),
            FYIZ=get_value(input_list=input_list, name='FYIZ'),
            ip=get_value(input_list=input_list, name='ip'),
            locationz=get_value(input_list=input_list, name='locationz'),
            vzh=str(35),
            recaptcha_response=get_value(input_list=input_list, name='recaptcha_response'),
            prefixZQ=prefix,
            reserve_number=reserve_number
        )


def fill_encrypted_fields(
        info: DltReserveInfo,
        raw_html: str,
        id_number: str,
        name: str,
        last_name: str,
        brand: str,
        phone_number: str,
        car_body_number: str,
) -> DltReserveInfo:
    confirm_line = ""
    for line in raw_html.split("\n"):
        if 'โปรดตรวจสอบข้อมูลของท่านก่อนดำเนินการต่อ' in line:
            confirm_line = line

    if not confirm_line:
        raise RuntimeError('something wrong, cannot find confirm_line')

    encrypted_field_name = ""
    encrypted_field_last_name = ""
    encrypted_id = ""
    encrypted_phone_number = ""
    encrypted_car_brand = ""
    encrypted_car_body_number = ""
    for sub_line in confirm_line.split("\\n"):
        if 'ชื่อ' in sub_line:
            alert_line = sub_line.split("document.getElementById")
            for i, n in enumerate(alert_line):
                details = re.findall(r"'([^']*)'", n)
                if i == 2:
                    encrypted_field_name = details[0]
                elif i == 3:
                    encrypted_field_last_name = details[0]
        elif 'เลขบัตร' in sub_line:
            alert_line = sub_line.split("document.getElementById")
            for i, n in enumerate(alert_line):
                details = re.findall(r"'([^']*)'", n)
                if i == 1:
                    encrypted_id = details[0]
        elif 'โทรศัพท์' in sub_line:
            alert_line = sub_line.split("document.getElementById")
            for i, n in enumerate(alert_line):
                details = re.findall(r"'([^']*)'", n)
                if i == 1:
                    encrypted_phone_number = details[0]
        elif 'รายละเอียดรถ' in sub_line:
            alert_line = sub_line.split("document.getElementById")
            for i, n in enumerate(alert_line):
                details = re.findall(r"'([^']*)'", n)
                if i == 1:
                    encrypted_car_brand = details[0]
                elif i == 2:
                    encrypted_car_body_number = details[0]
    return info.update(
        name=KeyValuePair(key=encrypted_field_name, value=name),
        last_name=KeyValuePair(key=encrypted_field_last_name, value=last_name),
        id_number=KeyValuePair(key=encrypted_id, value=id_number),
        phone_number=KeyValuePair(key=encrypted_phone_number, value=phone_number),
        brand=KeyValuePair(key=encrypted_car_brand, value=brand),
        car_body_number=KeyValuePair(key=encrypted_car_body_number, value=car_body_number)
    )


async def cooldown(page: Page, sec: int):
    current = 1
    while sec >= current:
        print(f"LOG DELAY {sec} SEC CURRENT IS {current}")
        await page.waitFor(1000)
        current = current + 1

async def request_interception(req):
    """ await page.setRequestInterception(True) would block the flow, the interception is enabled individually """
    # enable interception
    req.__setattr__('_allowInterception', True)
    if req.method == "POST" and req.url.startswith('http') and not req.postData.startswith('timepress') and req.resourceType == "document":
        # if req.method == "POST":
        print(f"\nreq.url: {req.url}")
        print(f"req.resourceType: {req.resourceType}")
        print(f"req.method: {req.method}")
        # print(f"req.postData: {req.postData}")
        print(f"req.headers: {req.headers}")
        print(f"req.response: {req.response}")
    return await req.continue_()

async def handle_dialog(dialog_message, page, dialog: Dialog):
    print(f"dialog data[{dialog.type}]: {dialog.message}")  # Print out the message of the pop-up box
    if dialog.type == "confirm":
        await page.waitFor(1000)
        await dialog.accept('OK')  # You can set the default value for the pop-up window
    if dialog.type == "alert":
        dialog_message.append(dialog.message)
        await dialog.accept('OK')
    if "ไม่สามารถจองได้" in dialog.message:
        raise Exception(dialog.message)  # Raise an exception to stop the function
    if "จองเลขทะเบียนไปแล้ว" in dialog.message:
        raise Exception(dialog.message)  # Raise an exception to stop the function
    if "ยังไม่พ้นกำหนด" in dialog.message:
        raise Exception(dialog.message)  # Raise an exception to stop the function
    if "ไม่สามารถดำเนินการ" in dialog.message:
        raise Exception(dialog.message)  # Raise an exception to stop the function

# Continue from main
async def run_browser(
        id_number: str,
        prefix: str,
        name: str,
        last_name: str,
        brand: str,
        phone_number: str,
        personal_type: str,
        car_body_number: str,
        reserve_number: str,
        wait_sec: int,
        carType: str,
        cus_no: int
) -> MakeDltReserveResponse:
    start_time = time.time() # Time for start (Time for server)
    timeout = 2500 
    dialog_message = [None]


    print("chromium_executable: ", chromium_downloader.chromium_executable())
    browser = await launch(headless=True,
                           handleSIGINT=False,
                           handleSIGTERM=False,
                           handleSIGHUP=False,
                           devtools=False,
                           executablePath=get_executable_chromium_path())

    print("LOG CREATE INCOGNITO BROWSERCONTEXT")
    await browser.createIncognitoBrowserContext()
    print("LOG INCOGNITO BROWSERCONTEXT TAB")
    page = await browser.newPage()
    page.setDefaultNavigationTimeout(60 * 1000)
    page.on('request', lambda req: asyncio.ensure_future(request_interception(req)))
    await stealth(page)  # <-- Here
    print("LOG CONFIG USERS AGENT")
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36')
        
    status = "OK"
    rule_form = None
    message = ''
    is_flow_data = True
    i_rule_form = 0
    while is_flow_data:
        i_rule_form += 1
        print(f"GO TO URL :{url}")
        await page.goto(url)
        await cooldown(page, 2)
        print("LOG WAIT UNTIL RUN (10.00 TH LOCAL = 03:00 UTC)")
        now = datetime.utcnow()
        open_time = now.replace(hour=2, minute=30, second=0, microsecond=0) # +7.00 = 9:30 in Thai Time
        close_time = now.replace(hour=9, minute=0, second=0, microsecond=0) # +7.00 = 16:00 in Thai Time
        try:
            page.on('dialog', lambda dialog: asyncio.ensure_future(handle_dialog(dialog_message, page, dialog)))
        except Exception as e:
            is_flow_data = False
            return MakeDltReserveResponse(
                    status="FAILED",
                    message=" ".join(e.split()),
                    executed_time=time.time() - start_time
                )
        
        if not (open_time < datetime.utcnow() < close_time):
            is_close, message= await check_system_close(page=page)
            if is_close:
                is_flow_data = False
                return MakeDltReserveResponse(
                    status="OK",
                    message= " ".join(message.split()) if message else 'Can Not get page for now',
                    executed_time=time.time() - start_time
                )
            print('+__LOG : CHECK SYSTEM INTIME__+')
            is_wait, message = await check_system_wait(page=page)
            if is_wait:
                is_flow_data = True
                continue
            else:
                is_flow_data = False
                return MakeDltReserveResponse(
                    status="OK",
                    message= " ".join(message.split()) if message else 'Can Not get page for now',
                    executed_time=time.time() - start_time
                )
        
        current_url = page.url
        print("++__QRCode page__++")
        print("++__Send QRCode To Line__++")
        if "https://imauth.bora.dopa.go.th/oauth2/?version=2" not in current_url:
            continue

        # send message to line
        # Noti line message API K'KAW
        notice_url = 'https://notify-api.line.me/api/notify'
        token = cus_token_list[cus_no]
        headers = {
            "Authorization": "Bearer " + token,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        requests.post(notice_url, headers=headers, data = {'message': f"\n \n 💢 ⏰  Please access this link : {current_url} in 20 sec \n"})

        # Wait untill singin complete if over 30 sec resent QR code
        auth_count_time = 0
        login_status = True
        while page.url == current_url:
            print(f"+__WAIT AUTH SIGN IN : {auth_count_time + 1}__+")
            await page.waitFor(1000)
            auth_count_time += 1
            if auth_count_time >= 30:
                login_status = False
                break
        if not login_status:
            continue
        
        await cooldown(page, 2)

        #Check Name is visible
        cs_body_xpath = '/html/body/div[2]/div/div[2]/div[1]/div[2]'
        element = await page.waitForXPath('/html/body/div[2]/div/div[2]/div[1]/div[2]', {'visible': True})
        text = await page.evaluate('(element) => element.textContent', element)        
        print("++__GO TO RULE PAGE__++")
        print(f"++__FIND USER ID {id_number} AND {name} {last_name}__++")

        print('++__CHEKC CONTENT RULE PAGE__++')
        print(" ".join(text.strip().split()))
        text = " ".join(text.strip().split())
        print(f'++__THIS IS {personal_type.upper()} TYPE__++')
        if personal_type == 'personal' and (id_number not in text or str(id_number) not in text):
            print('**Have no customer name in page')
            print("++__RETRY LOOP__++")
            continue
        elif personal_type == 'business' and 'หมายเลขบัตร: ชื่อ-นามสกุล: ออกจากระบบ' in text:
            print('**Have no name in page for business type')
            print("++__RETRY LOOP__++")
            continue
        
        start_rule_time = time.time()
        try:
            rule_form = await page.waitForXPath(xpath='//*[@id="f_rule"]')
            if rule_form:
                print("++__Found Rule Page__++")
            else:
                print("++__Not found Rule Page__++")
        except Exception as e:
            print(traceback.format_exc())
            
        # I expect that it will fail from try/execpt and then newPage() will working.
        # But if it's ok and then it will break from while loop 
        if rule_form is None:
            await page.reload({'waitUntil' : 'networkidle2'})
            print(f"LOG PAGE RELOADING x{i_rule_form} TIMES")
            continue

        if i_rule_form == numberForLoopTry - 1:
            await browser.close()
            is_flow_data = False
            return MakeDltReserveResponse(
                status="FAILED",
                message=f"Cannot Load Rule Page x{i_rule_form} Times",
                executed_time=time.time() - start_time
            )
        await rule_form.click()
        # Car Type
        car_type_form = None
        for i_car_type_form in range(numberForLoopTry):
            try:
                if carType == "CAR":
                    car_type_form = await page.waitForXPath(xpath='/html/body/div[2]/div/div[1]/article/section/div/div/center/input[1]',
                                                                    timeout=timeout)
                if carType == "VAN":
                    car_type_form = await page.waitForXPath(xpath='/html/body/div[2]/div/div[1]/article/section/div/div/center/input[2]',
                                                                    timeout=timeout)
                if carType == "TRUCK":
                    car_type_form = await page.waitForXPath(xpath='/html/body/div[2]/div/div[1]/article/section/div/div/center/input[3]',
                                                                    timeout=timeout)
                break
            except Exception as e:
                print(traceback.format_exc())

            if car_type_form is None:
                await page.reload({'waitUntil' : 'networkidle0'})
                print(f"LOG PAGE RELOADING x{i_car_type_form} TIMES")

            if i_car_type_form == numberForLoopTry - 1:
                await browser.close()
                is_flow_data = False
                return MakeDltReserveResponse(
                    status="FAILED",
                    message=f"cannot load car type page x{i_car_type_form} times",
                    executed_time=time.time() - start_time
                )

        random_number = random.randint(200, 300)
        print(f"LOG PLEASE WAIT {random_number} ms")
        await page.waitFor(random_number)
        print("LOG CLICK SELECTE CARTYPE")
        await car_type_form.click()

        # Personnal type
        personnal_type_form = None
        for i_personnal_type_form in range(numberForLoopTry):
            try:
                if personal_type == "personal":
                    personnal_type_form = await page.waitForXPath(xpath='/html/body/div[2]/div/div[1]/article/section/div/div/center/input[1]',
                                                                    timeout=timeout)
                if personal_type == "business":
                    personnal_type_form = await page.waitForXPath(xpath='/html/body/div[2]/div/div[1]/article/section/div/div/center/input[2]',
                                                                    timeout=timeout)
                break
            except Exception as e:
                print(traceback.format_exc())

            if personnal_type_form is None:
                await page.reload({'waitUntil' : 'networkidle0'})
                print(f"LOG PAGE RELOADING x{i_personnal_type_form} TIMES")

            if i_personnal_type_form == numberForLoopTry - 1:
                await browser.close()
                is_flow_data = False
                return MakeDltReserveResponse(
                    status="FAILED",
                    message=f"cannot load car type page x{i_personnal_type_form} times",
                    executed_time=time.time() - start_time
                )
        print(f"LOG PLEASE WAIT {random_number} ms")
        await page.waitFor(random_number)
        print("LOG CLICK SELECTE PERSONAL TYPE")
        await personnal_type_form.click()

        print("LOG TRYING LOAD CONTENT PAGE")
        content = None
        submit_form = None
        for i_content in range(numberForLoopTry):
            # input frame
            try:
                # input_frame = list(filter(lambda p: p.name == 'iframe_a', page.frames))[0]
                await page.waitForXPath(xpath='//*[@id="number"]', options={"timeout": timeout})
                await page.waitForFunction('document.getElementById("recaptchaResponse").value != ""')
                submit_form = await page.waitForXPath(xpath='//*[@id="s_resz"]', options={"timeout": timeout})
                content = await page.content()
                break
            except Exception as e:
                print(traceback.format_exc())
                await page.reload()
                print(f"CONTENT PAGE RELOADING x{i_content} TIMES")

        if content is None:
            await page.reload({'waitUntil' : 'networkidle0'})
            print(f"LOG PAGE RELOADING x{i_content} TIMES")

        if i_content == numberForLoopTry - 1:
            await browser.close()
            is_flow_data = False
            return MakeDltReserveResponse(
                status="FAILED",
                message=f"cannot load input form page x{i_content} times",
                executed_time=time.time() - start_time
            )
        start_content_time = time.time()
        print("LOG TRYING LOAD CONTENT PAGE WAS DONE")
        html = BeautifulSoup(content, 'html.parser')
        hidden_inputs = html.find_all("input", type="hidden")
        info = make_DltReserveInfo(input_list=hidden_inputs, reserve_number=reserve_number, prefix=prefix)
        # print("info : %s" % info,
        #       "raw_html : %s" % content,
        #       "name : %s" % name,
        #       "last_name : %s" % last_name,
        #       "id_number : %s" % id_number,
        #       "phone_number : %s" % phone_number,
        #       "car_body_number : %s" % car_body_number,
        #       "brand : %s" % brand)
        updated = fill_encrypted_fields(info=info, raw_html=content,
                                        name=name,
                                        last_name=last_name,
                                        id_number=id_number,
                                        phone_number=phone_number,
                                        car_body_number=car_body_number,
                                        brand=brand)
        cookies = await page._client.send('Network.getAllCookies')
        php_session_id = list(filter(lambda p: p['name'] == 'PHPSESSID', cookies['cookies']))[0]['value']

        try:
            print(f"LOG TYPING USER ID:prefixZQ w/ {updated.prefixZQ} WAS SUCCESSFUL !!!")
            if personal_type == 'business':
                await page.select('#prefixZQ', 'บริษัท')
        except Exception as e:
            print(e)

        try:
            input_userId = await page.waitForXPath(xpath=f"//*[@id='{updated.id.key}']", options={"timeout": timeout})
            await input_userId.type(updated.id.value.lower(),delay=0)
            print(f"LOG TYPING USER ID:{updated.id.key} w/ {updated.id.value} WAS SUCCESSFUL !!!")
        except Exception as e:
            print(e)

        try:
            input_name = await page.waitForXPath(xpath=f"//*[@id='{updated.name.key}']", options={"timeout": timeout})
            await input_name.type(updated.name.value.lower(),delay=0)
            print(f"LOG TYPING NAME ID:{updated.name.key} w/ {updated.name.value} WAS SUCCESSFUL !!!")
        except Exception as e:
            print(e)

        try:
            input_lastname = await page.waitForXPath(xpath=f"//*[@id='{updated.lastname.key}']", options={"timeout": timeout})
            await input_lastname.type(updated.lastname.value.lower(),delay=0)
            print(f"LOG TYPING LASTNAME ID:{updated.lastname.key} w/ {updated.lastname.value} WAS SUCCESSFUL !!!")
        except Exception as e:
            print(e)

        try:
            input_carId = await page.waitForXPath(xpath=f"//*[@id='{updated.phone_number.key}']", options={"timeout": timeout})
            await input_carId.type(updated.phone_number.value.lower(),delay=0)
            print(f"LOG TYPING TELEPHONE ID:{updated.phone_number.key} w/ {updated.phone_number.value} WAS SUCCESSFUL !!!")
        except Exception as e:
            print(e)

        try:
            input_carId = await page.waitForXPath(xpath=f"//*[@id='{updated.brand.key}']", options={"timeout": timeout})
            await input_carId.type(updated.brand.value.lower(),delay=0)
            print(f"LOG TYPING BRAND ID:{updated.brand.key} w/ {updated.brand.value} WAS SUCCESSFUL !!!")
        except Exception as e:
            print(e)

        try:
            input_number = await page.waitForXPath(xpath=f"//*[@id='number']", options={"timeout": timeout})
            await input_number.type(str(updated.reserve_number),delay=0)
            print(f"LOG TYPING NUMBER ID:number w/ {updated.reserve_number} WAS SUCCESSFUL !!!")
        except Exception as e:
            print(e)

        try:
            input_carId = await page.waitForXPath(xpath=f"//*[@id='{updated.car_body_number.key}']", options={"timeout": timeout})
            await input_carId.type(updated.car_body_number.value.lower(),delay=0)
            print(f"LOG TYPING CAR BODY NUMBER ID:{updated.car_body_number.key} w/ {updated.car_body_number.value} WAS SUCCESSFUL !!!")
        except Exception as e:
            print(e)        

        print(f"[{updated.reserve_number}]PLEASE WAIT FOR {20} SEC")
        await page.waitFor(20 * 1000)
        print(f"[{updated.reserve_number}]CLICK SUBMIT FORM")
        await submit_form.click()
        print(f"[{updated.reserve_number}]CLICK SUBMIT FORM DONE")
        print("---RULE PAGE TIME TO BEFOR REQUEST API %s SECONDS ---" % (time.time() - start_rule_time))
        print("---CONTENT PAGE TIME TO BEFOR REQUEST API %s SECONDS ---" % (time.time() - start_content_time))
        message = await get_request(dialog_message, wait_sec, page, data=updated, php_session_id=php_session_id)
        if message == None or message == " ":
            print("+__LOG : RETRY AGAIN__+")
            continue
        if 'เลขที่ประจำตัวของท่านยังไม่พ้นกำหนด' in message:
            message = 'ขออภัย ท่านไม่สามารถทำรายการจองได้ เนื่องจากเลขที่ประจำตัวของท่านยังไม่พ้นกำหนด 3 เดือน'

        #TODO : Add next car plate number next priority
        
        print("---RULE PAGE TIME TO AFTER REQUEST API %s SECONDS ---" % (time.time() - start_rule_time))
        print("---CONTENT PAGE TIME TO AFFTER REQUEST API %s SECONDS ---" % (time.time() - start_content_time))
        await browser.close()
        return MakeDltReserveResponse(
            status=status,
            message= " ".join(message.split()),
            executed_time=time.time() - start_time
        )
    return MakeDltReserveResponse(
        status=status,
        message= " ".join(message.split()),
        executed_time=time.time() - start_time
    )
