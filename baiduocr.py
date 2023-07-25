# 百度ocr用,文档
import base64
import json
from urllib.request import urlopen
from urllib.request import Request as r2
from urllib.error import URLError
from urllib.parse import urlencode
import config

def bdRequest(url, data):
    req = r2(url, data.encode('utf-8'))
    has_error = False
    try:
        f = urlopen(req)
        result_str = f.read()
        result_str = result_str.decode()
        return result_str
    except URLError as err:
        print(err)
        raise


def bdFuckCode(fuck_save_path):
    # 防止https证书校验不正确
    import ssl
    ssl._create_default_https_context = ssl._create_unverified_context
    """
    api文档:https://cloud.baidu.com/doc/OCR/s/1k3h7y3db
    替换您的 API_KEY 以及 SECRET_KEY
    教程:https://cloud.baidu.com/doc/OCR/s/dk3iqnq51
    """

    API_KEY = config.API_KEY
    SECRET_KEY = config.SECRET_KEY

    """替换需要用的url"""
    OCR_URL = config.OCR_URLOCR_URL

    """  TOKEN start """
    # 获取access token
    TOKEN_URL = 'https://aip.baidubce.com/oauth/2.0/token'
    params = {'grant_type': 'client_credentials',
              'client_id': API_KEY,
              'client_secret': SECRET_KEY}
    post_data = urlencode(params)
    post_data = post_data.encode('utf-8')
    req = r2(TOKEN_URL, post_data)
    try:
        f = urlopen(req, timeout=5)
        result_str = f.read()
    except URLError as err:
        print(err)
    result_str = result_str.decode()
    result = json.loads(result_str)
    if ('access_token' in result.keys() and 'scope' in result.keys()):
        if not 'brain_all_scope' in result['scope'].split(' '):
            print('please ensure has check the  ability')
            return False
        print("[DEBUG] APItoken -> OK")
    else:
        print('[DEBUG] please overwrite the correct API_KEY and SECRET_KEY')
        return False
    # 读取图片
    image_url = OCR_URL + "?access_token=" + result['access_token']
    with open(fuck_save_path, 'rb') as f:
        file_content = f.read()
    # 发送图片识别请求
    result = bdRequest(image_url, urlencode({'image': base64.b64encode(file_content)}))

    result_json = json.loads(result)
    text = ""
    for words_result in result_json["words_result"]:
        text = text + words_result["words"]
    # 打印文字
    # print(text)
    return text