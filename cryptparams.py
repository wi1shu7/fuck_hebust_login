import hashlib
import os
import random
import re
import config
import requests
import base64
from datetime import datetime


# 消除安全证书错误的warning
requests.packages.urllib3.disable_warnings()


class CryptParams(object):

    def __init__(self,
                 username: str,
                 password: str,
                 loginRequest: requests.session(),
                 url: bool = False,
                 ):
        """
        :param username: 用户名
        :param password: 密码
        :param loginRequest: 登录所用request.session()
        :param url: 是否启用备用URL地址（True/False）
        """
        self.__username = username
        self.__password = password
        self.__webRootPath = 'https://202.206.64.231' if url else 'https://jw.hebust.edu.cn'
        self.__loginUrl = self.__webRootPath + "/hbkjjw/cas/login.action"
        self.__GetKingoEncyptUrl = self.__webRootPath + "/hbkjjw/custom/js/GetKingoEncypt.jsp"
        self.__SetKingoEncyptUrl = self.__webRootPath + "/hbkjjw/custom/js/SetKingoEncypt.jsp"
        self.__codeUrl = self.__webRootPath + '/hbkjjw/cas/genValidateCode'
        self.__header = {
            "Referer": self.__webRootPath + '/hbkjjw/cas/login.action'
        }

        # 设置request.session()
        self.__loginRequest = loginRequest
        # self.__loginRequest = requests.session()
        self.__cookie = self.__loginRequest.cookies.get("JSESSIONID")

        # 参数初始化
        self.__token = self.__password
        self.__randnumber = ""
        self.__passwordPolicy = self.__isPasswordPolicy()
        self.__txt_mm_expression = self.__checkParams()
        self.__txt_mm_length = str(len(self.__password))
        self.__txt_mm_userzh = self.__inUserzh()
        self.__hid_flag = "1"

    def cryptParam(self):
        """
        :return: 最终加密并且经过拼接后的密文
        """

        if config.openCodeLogin:
            self.__hid_flag = ""
            self.__randnumber = self.__setCode().strip()
            # 判断验证码是否有误
            checkNum = 0
            while checkNum < 5 and not (lambda code: bool(re.match(r'^\d{4}$', code)))(self.__randnumber):
                checkNum += 1
                self.__randnumber = self.__setCode().strip()

        getDesKey_param = {'random': str(round(random.uniform(0, 1), 17))}
        req_getFakeKey = self.__loginRequest.get(self.__GetKingoEncyptUrl, params=getDesKey_param,
                                                 headers=self.__header, verify=False)
        try:
            desKey = re.search("var _tdeskey = '(.*?)';", req_getFakeKey.text, re.M).group(1)
        except Exception:
            print(f"访问{self.__GetKingoEncyptUrl}有误！请检查")
            raise

        if not desKey:
            getDesKey_param = {'random': str(round(random.uniform(0, 1), 15))}
            req_setFakeKey = self.__loginRequest.get(self.__SetKingoEncyptUrl, params=getDesKey_param,
                                                     headers=self.__header, verify=False)
            try:
                desKey = re.search("var _deskey = '(.*?)';", req_setFakeKey.text, re.M).group(1)
            except Exception:
                print(f"访问{self.__SetKingoEncyptUrl}有误！请检查")
                raise

        print(f'[DEBUG] des key -> {desKey}')

        p_username = "_u" + self.__randnumber
        p_password = "_p" + self.__randnumber

        b64_username = base64.b64encode((self.__username + ";;" + self.__cookie).encode('utf-8')).decode('utf-8')
        md5_password = self.__hex_md5(self.__hex_md5(self.__password) + self.__hex_md5(self.__randnumber.lower()))

        param = p_username + "=" + b64_username + "&" + p_password + "=" + md5_password + "&randnumber=" + \
                 self.__randnumber + "&isPasswordPolicy=" + self.__passwordPolicy + "&txt_mm_expression=" + \
                 self.__txt_mm_expression + "&txt_mm_length=" + self.__txt_mm_length + "&txt_mm_userzh=" + \
                 self.__txt_mm_userzh + "&hid_flag=" + self.__hid_flag + "&hidlag=1"
        crypt_param = self.__getEncParams(param, desKey) + "&deskey=" + desKey + "&ssessionid=" + self.__cookie

        print(f'[DEBUG] final crypt data -> {crypt_param}')

        return crypt_param

    def __setCode(self):

        try:
            from PIL import Image
            import baiduocr
        except Exception:
            print("导入PIL库失败！")
            raise

        setTime = datetime.now().strftime("%y%m%d_%H_%M_%S")

        save_path = "./images/" + self.__username + "/" + setTime + ".png"
        fuck_save_path = "./images/" + self.__username + "/fuck-" + setTime + ".png"
        if not os.path.exists("./images/" + self.__username + "/"):
            os.makedirs("./images/" + self.__username + "/")

        param = {
            'v': str(random.randint(1, 100))
        }
        random_png = self.__loginRequest.get(
            self.__codeUrl,
            headers=self.__header,
            verify=False,
            params=param
        )

        with open(save_path, "wb") as f:
            f.write(random_png.content)

        image = Image.open(save_path)
        image = image.convert('L')  # 将图片转为灰度图片
        threshold = 135  # 设置阈值
        table = []
        for i in range(256):
            if i < threshold:
                table.append(0)
            else:
                table.append(1)
        image = image.point(table, '1')

        #  resize图片大小，入口参数为一个tuple，新的图片的大小
        imageBig = image.resize((330, 154))
        # imageBig.show()
        #  处理图片后存储路径，以及存储格式
        imageBig.save(fuck_save_path, 'PNG')

        code = baiduocr.bdFuckCode(fuck_save_path)

        if code == False:
            print("获取apitoken错误,请检查 API_KEY 以及 SECRET_KEY")
            exit()

        print("[DEBUG] fuckCheckcode -> " + code)

        if not config.saveCodeImg:
            try:
                os.remove(save_path)
                os.remove(fuck_save_path)
            except Exception:
                print("删除验证码失败")
                raise

        return code

    def __isPasswordPolicy(self):
        if self.__password == "" or self.__username == self.__password:
            return "0"
        if len(self.__password) < 6:
            return "0"
        return "1"

    def __checkParams(self):
        result = 0
        for char in self.__password:
            result |= self.__charType(ord(char))
        return str(result)

    def __inUserzh(self):
        return '1' if self.__username.lower().strip() in self.__password.lower().strip() else '0'

    def __getEncParams(self, param, desKey):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        token = self.__hex_md5(self.__hex_md5(param) + self.__hex_md5(timestamp))
        _params = base64.b64encode(self.__pyExecJsCryptParam(param, desKey).encode('utf-8')).decode('utf-8')
        _params_final = "params=" + _params + "&token=" + token + "&timestamp=" + timestamp
        return _params_final

    def __pyExecJsCryptParam(self, param, deskey) -> str:
        import execjs
        with open("./js/desdecrypt.js", 'r', encoding='utf-8') as f:
            ctx = execjs.compile(f.read())
            enc = ctx.call("strEnc", param, deskey, None, None)
            # enc = ctx.call("函数名","参数")
            # 文本名 为你在js设置的函数 参数为你传的参数
        return enc

    @staticmethod
    def __charType(num):
        if 48 <= num <= 57:
            return 8
        if 97 <= num <= 122:
            return 4
        if 65 <= num <= 90:
            return 2
        return 1

    @staticmethod
    def __hex_md5(s):
        return hashlib.md5(s.encode()).hexdigest()