import requests
from bs4 import BeautifulSoup

import re
import base64
from hebustlogin import HebustLogin
from datetime import datetime

# 消除安全证书错误的warning
requests.packages.urllib3.disable_warnings()


class HebustFunc(HebustLogin):

    def __init__(self, username='', password=''):
        super().__init__(username, password)
        self.__user = super()
        self.__loginRequest: requests.session() = super().login()

    def getAcademicRecord(self,
                          xn: int = 0,
                          xq: int = 1,
                          mode: int = 1,
                          time: int = 1,
                          havefx: bool = True,
                          ) -> dict:
        """
        默认读取入学以来所有成绩
        :param xn: 学年，2022-2023学年就填2022，以此类推
        :param xq: 学期，上学期为1，下学期为2
        :param mode: 原始成绩为1，有效成绩为2
        :param time: 入学以来为1，学年为2，学期为3
        :param havefx: 是否包含辅修
        :return: json格式的数据
        """

        if not (xn == 0 or (1000 <= xn <= 9999)):
            raise ValueError("xn必须为0或四位整数。")

        if not (xq == 1 or xq == 2):
            raise ValueError("xq必须为1或2。")

        if not (mode == 1 or mode == 2):
            raise ValueError("mode必须为1或2。")

        if not (1 <= time <= 3):
            raise ValueError("time必须在1到3之间。")

        url = self.__user.getUrl() + "/hbkjjw/student/xscj.stuckcj_data.jsp"

        headers = {
            "Referer": self.__user.getUrl() + "/hbkjjw/student/xscj.stuckcj_data.jsp?menucode=S40303",
            "Origin": self.__user.getUrl(),
            "Content-Type": "application/x-www-form-urlencoded"
        }

        data = {
            'sjxz': 'sjxz' + str(time),
            'ysyx': 'yxcj' if mode - 1 else 'yscj',
            'zx': '1',
            'fx': '1',
            'btnExport': '%B5%BC%B3%F6',
            'xn': xn,
            'xn1': xn + 1,
            'xq': xq - 1,
            'ysyxS': 'on',
            'sjxzS': 'on',
            'zxC': 'on',
            'fxC': 'on',
            'menucode_current': 'S40303'
        }

        if not havefx:
            del data["fx"]
        if time == 1:
            del data['xn'], data['xq']
            data['xn1'] = datetime.now().strftime("%y")
        elif time == 2:
            del data['xq']

        req = self.__loginRequest.post(url=url, data=data, headers=headers, verify=False)

        recode_dict = {
            'user': None,
            'course': [],
        }

        soup = BeautifulSoup(req.text.lstrip(), 'lxml')
        info_soup = soup.find('div', {"group": 'group'})
        info_list = {infoName: info for infoName, info in [_.split("：") for _ in info_soup.text.strip().split("\n")]}
        recode_dict.update({'user': info_list})

        course_iter = iter(soup.find_all("tr"))
        translation_list = ['serial_number', 'course_module', 'credits', 'total_hours', 'category', 'learning_property',
                            'assessment_method', 'acquisition_method', 'score', 'remark']
        course_dict = {
            'course_time': "",
            'course_info': []
        }
        course_info_dict = {
            'serial_number': '',
            'course_module': '',
            'credits': '',
            'total_hours': '',
            'category': '',
            'learning_property': '',
            'assessment_method': '',
            'acquisition_method': '',
            'score': '',
            'remark': ''
        }
        for course in course_iter:
            course_info = course.text.strip()
            if re.match('学年学期：\d{4}-\d{4}学年第.?学期', course_info):
                if course_dict['course_info']:
                    recode_dict['course'].append(course_dict)

                course_dict = {
                    'course_time': course_info,
                    'course_info': []
                }
                next(course_iter)
            else:
                translation_list_iter = iter(translation_list)
                course_info_dict = {
                    'serial_number': '',
                    'course_module': '',
                    'credits': '',
                    'total_hours': '',
                    'category': '',
                    'learning_property': '',
                    'assessment_method': '',
                    'acquisition_method': '',
                    'score': '',
                    'remark': ''
                }
                for course_info_data in course_info.split("\n"):
                    course_info_dict[next(translation_list_iter)] = course_info_data
                course_dict['course_info'].append(course_info_dict)

        if course_dict['course_info']:
            recode_dict['course'].append(course_dict)

        return recode_dict

    def getTimetable(self, xn=-1, xq=1) -> dict:

        """
        默认读取今年第一学期
        :param xn: 学年，2022-2023学年就填2022，以此类推
        :param xq: 学期，上学期为1，下学期为2
        :return: json格式的数据
        """

        if not ((1000 <= xn <= 9999) or xn == -1):
            raise ValueError("xn必须为四位整数。")

        if not ((xq == 1 or xq == 2) or xq == -1):
            raise ValueError("xq必须为1或2。")

        if xn == -1:
            xn = int(datetime.now().strftime("%y")) - 1

        xn = str(xn)
        xq = str(xq - 1)

        # 获取伪学号
        timetable_url1 = self.__user.getUrl() + "/hbkjjw/frame/home/js/SetMainInfo.jsp"

        xh_req = self.__loginRequest.get(timetable_url1)
        xh_text = xh_req.text.lstrip()
        xh_text_re = re.search(r"G_USER_CODE = '(\d{12})", xh_text, re.M)
        xh_num = xh_text_re.group(1)
        print("fakeStudentNum -> " + xh_num)

        params2_ = "xn=" + xn + "&xq=" + xq + "&xh=" + xh_num
        params2_bs4 = str(base64.b64encode(params2_.encode())).lstrip("b").strip("\'")
        timetable_url2 = self.__user.getUrl() + "/hbkjjw/wsxk/xkjg.ckdgxsxdkchj_data10319.jsp"
        headers = {
            "Referer": self.__user.getUrl() + "/hbkjjw/student/xkjg.wdkb.jsp?menucode=S20301",
        }
        params2 = {"params": params2_bs4}
        timetable_text = self.__loginRequest.get(timetable_url2, headers=headers, params=params2).text

        timetable_soup = BeautifulSoup(timetable_text.lstrip(), 'lxml')

        try:
            timetable_tr = timetable_soup.tbody.find_all("tr")
        except Exception:
            if "没有检索到记录" in timetable_text.lstrip():
                print("课表没有检索到记录！")
                return {'student_number': super().getUsername(), 'messages': None}
            else:
                raise


        timetable_data = {
            'student_number': super().getUsername(),
            'messages': [],
        }

        for j in timetable_tr:
            timetable_td = j.find_all("td")
            course_name = re.search(r'\[.*](.*)', timetable_td[1].string).group(1)
            teacher_name = re.search(r'\[.*](.*)', timetable_td[5].string).group(1)
            course_info = timetable_td[8].string
            # print(course_info)
            pattern1 = r'((?:\d{1,2}\,)+\d{1,2})\S (\S)\[(\d+-\d+)\] (\S+)\(\d*\)'
            pattern2 = r'(\d+-\d+)周 (\S+)\[(\d+-\d+)\] (\S+)\(\d*\)'

            # 第一部分：3,5,7,9,11,13,15周 五[7-8] 信息楼C104(80)
            part1_data = [[week, week_day, course_time, place]
                          for week, week_day, course_time, place
                          in re.findall(pattern1, course_info)]

            # 第二部分：4-15周 一[1-2] 公教楼C405(180)
            part2 = re.findall(pattern2, course_info)
            week_list = [",".join(map(str, range(int(p[0].split('-')[0]), int(p[0].split('-')[1]) + 1))) for p
                         in part2]
            part2_data = [[week, week_day, course_time, place] for
                          (start_end_week, week_day, course_time, place), week in zip(part2, week_list)]

            if part1_data:
                for d in part1_data:
                    timetable_data["messages"].append(
                        {
                            "student_number": super().getUsername(),
                            "course_name": repr(course_name),
                            "teacher_name": repr(teacher_name),
                            "week": repr(d[0]),
                            "week_day": repr(d[1]),
                            "course_time": repr(d[2]),
                            "place": repr(d[3])
                        }
                    )

            if part2_data:
                for d in part2_data:
                    timetable_data["messages"].append(
                        {
                            "student_number": super().getUsername(),
                            "course_name": repr(course_name),
                            "teacher_name": repr(teacher_name),
                            "week": repr(d[0]),
                            "week_day": repr(d[1]),
                            "course_time": repr(d[2]),
                            "place": repr(d[3])
                        }
                    )
        return timetable_data

    # 递归输出信息
    @staticmethod
    def recursivePrintDict(data, indent=''):
        if isinstance(data, dict):
            print('{')
            for key, value in data.items():
                print(f"{indent}    {key}: ", end='')
                HebustFunc.recursivePrintDict(value, indent + '    ')
            print(f"{indent}}}")
        elif isinstance(data, list):
            print('[')
            for idx, item in enumerate(data):
                print(f"{indent}    ", end='')
                HebustFunc.recursivePrintDict(item, indent + '    ')
                if idx < len(data) - 1:
                    print(',')  # 打印逗号用于分隔列表元素
            print(f"{indent}]")
        else:
            print(data)


if __name__ == '__main__':
    l = HebustFunc()
    academicRecord = l.getAcademicRecord()
    timetable = l.getTimetable(2022, 2)
    l.recursivePrintDict(academicRecord)
    l.recursivePrintDict(timetable)
