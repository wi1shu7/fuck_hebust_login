import base64
import json

import requests

import config
import cryptparams

# 消除安全证书错误的warning
requests.packages.urllib3.disable_warnings()


class HebustLogin(object):

    def __init__(self, username="", password=""):
        """
        :param username: 学号，不填写则默认读取config.py里面的username
        :param password: 密码，不填写则默认读取config.py里面的password，如开启加密请传入加密后的密码
        """
        if username == "" or password == "":
            username = config.username
            password = config.password

        if config.passwordCryptKey:
            password = self.aes_decrypt(config.passwordCryptKey, config.passwordCryptIv, password)

        self.__webRootPath = ['https://jw.hebust.edu.cn', 'https://202.206.64.231']
        self.__indexUrl = '/hbkjjw/cas/login.action'
        self.__loginUrl = '/hbkjjw/cas/logon.action'
        self.__homeUrl = ""
        self.__urlNum = 0
        self.__username = username
        self.__password = password
        self.__loginRequest = requests.session()
        self.__cookie = None

        self.__cryptParams = None
        self.__cryptText = ""

        self.__header = {
            "User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
        }
        self.__loginHeader = {
            "Referer": self.getUrl() + '/hbkjjw/cas/login.action',
            'Origin': self.getUrl(),
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        self.__loginRequest.headers.update(self.__header)

    def __del__(self):
        self.__loginRequest.close()

    def login(self):
        """
        :return: 登陆成功的request.session()对象
        """

        print(f'[DEBUG] login username -> {self.__username}')

        # 判断url存活情况，并选用url
        try:
            req = self.__loginRequest.get(self.getUrl() + self.__indexUrl, verify=False)
            print(f'[DEBUG] url -> {self.getUrl()}, status_code -> {str(req.status_code)}')
        except Exception as e:
            print(f'[DEBUG] ERROR url -> {self.getUrl()}, error_type -> {type(e)}')
            self.__loginRequest.cookies.clear()
            self.__urlNum = 1
            req = self.__loginRequest.get(self.getUrl() + self.__indexUrl, verify=False)
            print(f'[DEBUG] url -> {self.getUrl()}, status_code -> {str(req.status_code)}')

        self.__cookie = self.__loginRequest.cookies.get("JSESSIONID")

        self.__cryptParams = cryptparams.CryptParams(self.__username,
                                                     self.__password,
                                                     self.__loginRequest,
                                                     url=True if self.__urlNum else False,
                                                     )

        self.__cryptText = self.__cryptParams.cryptParam()
        req_login = self.__loginRequest.post(self.getUrl() + self.__loginUrl,
                                             headers=self.__loginHeader,
                                             data=self.__cryptText,
                                             verify=False)
        try:
            req_loginDict: dict = json.loads(req_login.text)
            if req_loginDict.get('status', '402') == '200':
                self.__homeUrl = self.getUrl() + req_loginDict.get('result')
                print(f"登录成功 staus -> {req_loginDict.get('status')}, home_url -> {self.__homeUrl}" +\
                      (f", cookie -> JSESSIONID: {self.__cookie}" if config.printCookie else ""))
                return self.__loginRequest
            else:
                print(f"登录失败 status -> {req_loginDict.get('status')}, message -> {req_loginDict.get('message')}")
                self.__loginRequest.close()
                self.__loginRequest = requests.session()
                return None
        except Exception:
            print("登录出现错误！")
            raise

    def getCookie(self):
        return {"JSESSIONID": self.__cookie}

    def getHomeUrl(self):
        return self.__homeUrl

    def getUrl(self):
        return self.__webRootPath[self.__urlNum]

    def getUsername(self):
        return self.__username

    @staticmethod
    def aes_decrypt(key, iv, encrypted_data):
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import unpad
        # 将密钥和IV转换为字节类型
        key = key.encode('utf-8')
        iv = iv.encode('utf-8')
        # 将base64编码后的密文转换为字节类型
        encrypted_data = base64.b64decode(encrypted_data)
        # 创建AES解密器
        cipher = AES.new(key, AES.MODE_CBC, iv)
        # 解密数据并去除填充
        decrypted_data = unpad(cipher.decrypt(encrypted_data), AES.block_size)
        # 将解密后的数据转换为字符串并返回
        return decrypted_data.decode('utf-8')
