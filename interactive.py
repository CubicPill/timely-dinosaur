import logging
import colorama
import re


def do_interactive_enroll():
    """
    interactive enroll. user will enter the course_ids manually
    :return:
    """
    success = list()
    failed = list()
    print(colorama.Fore.LIGHTYELLOW_EX +
          '警告: 交互式单项选课仅作为调试用途, 输入格式错误可能导致选课失败或程序崩溃, 请谨慎使用')
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
            if not re.match('\d{15}$', course_id):
                print(colorama.Fore.LIGHTYELLOW_EX + '输入格式不匹配. 是否继续?(Y/N) ', end='')
                cont = input()
                if cont.lower() == 'y':
                    pass
                else:
                    continue
            __type = int(__type)
            course_name_map[course_id] = dict()
            course_name_map[course_id]['type'] = __type
            course_name_map[course_id]['name'] = '<id: {}>'.format(course_id)
            course_name_map[course_id]['cid'] = 'DUMMY001'

            result = _enroll(course_id, __type, False)
            if result['success']:
                success.append(result)
            else:
                failed.append(result)
        except Exception:
            logging.error('Error occurred in interactive enrolling')
            logging.error(traceback.format_exc())
            print(colorama.Fore.LIGHTRED_EX + traceback.format_exc())
        time.sleep(0.1)

    return success, failed
