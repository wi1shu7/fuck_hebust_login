

username = ''
password = ''

# 密码加密,如果开启，密码请填入加密后的密文
encrypt = False

# AES -> 密文:base64 mode:CBC padding:PKCS7 128位 encoding:utf-8
# 32位key 16位iv
# https://www.toolhelper.cn/SymmetricEncryption/AES
passwordCryptKey = '' # key
passwordCryptIv = '' # iv

# 是否使用验证码登录， 不开启无需配置百度OCR
openCodeLogin = False

# 是否在本地保留验证码
saveCodeImg = True

# 是否输出cookie
printCookie = False

# 百度云OCR
#     api文档:https://cloud.baidu.com/doc/OCR/s/1k3h7y3db
#     替换您的 API_KEY 以及 SECRET_KEY
#     教程:https://cloud.baidu.com/doc/OCR/s/dk3iqnq51
API_KEY = ''
SECRET_KEY = ''
OCR_URLOCR_URL = "https://aip.baidubce.com/rest/2.0/ocr/v1/accurate_basic"



