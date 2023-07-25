from hebustfunc import HebustFunc
import os

if __name__ == '__main__':
    print("当前运行目录：", os.getcwd())
    l = HebustFunc("", "")
    academicRecord = l.getAcademicRecord()
    timetable = l.getTimetable(2022, 2)
    l.recursivePrintDict(academicRecord)
    l.recursivePrintDict(timetable)
