import colorama
import re
import time
import traceback


def do_interactive_enroll():
    """
    interactive enroll. user will enter the course_ids manually
    :return:
    """
    print('课程类型(0-5): ' + ' '.join(['必修', '选修', '本学期计划', '跨年级', '跨专业', '公共课']))

    while True:
        try:
            in_text = input('输入课程ID和课程类型编号, 以空格分隔. 输入 "exit" 结束.\nID:')
            if in_text == 'exit':
                break
            elif in_text == '':
                continue
            elif not re.match('.* \d$', in_text):
                print(colorama.Fore.LIGHTRED_EX + '格式错误!')
                continue
            course_id, __type = in_text.split(' ')
            __type = int(__type)

            result = _enroll(course_id, __type, False)
            return result
        except Exception:
            print(colorama.Fore.LIGHTRED_EX + traceback.format_exc())
        time.sleep(0.1)


if __name__ == '__main__':
    do_interactive_enroll()
