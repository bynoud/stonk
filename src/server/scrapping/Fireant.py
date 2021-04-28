
from seleniumwire import webdriver
import re, json, time


def scroll(driver, cnt=5, cnt2=1, pauseTime=0.5, pauseTime2=2):
    last_height = driver.execute_script("return document.body.scrollHeight")
    cnt1 = cnt
    while cnt1 > 0 and cnt2 > 0:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(pauseTime)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height: 
            break
        last_height = new_height
        cnt1 -= 1
        if cnt1 == 0:
            cnt1 = cnt
            cnt2 -= 1
            if cnt2 > 0:
                time.sleep(pauseTime2)

def connect(scroll=3):
    driver = webdriver.Firefox(executable_path=r'geckodriver-v0.29.1-win64/geckodriver.exe')
    driver.get('https://fireant.vn/home')
    scroll(driver, cnt2=scroll)
    return driver

def getPosts(driver):
    res = {'posts':[], 'userPosts':[]}
    postRe = re.compile(r'^https://restv2.fireant.vn/posts\?(.*)$')

    for request in driver.requests:
        m = postRe.match(request.url)
        if m:
            params = {v.split('=')[0]:v.split('=')[1] for v in m.group(1).split('&')}
            if 'type' not in params:
                continue
            body = json.loads(request.response.body.decode('utf-8'))
            if not isinstance(body, list):
                continue
            if params['type'] == '0':
                res['userPosts'].append(body)
            elif params['type'] == '1':
                res['posts'].append(body)
    return res