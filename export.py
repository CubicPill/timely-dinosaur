import csv
import os
import json

ROWS = ['kch', 'kcmc', 'fzmc', 'dwmc', 'xnxqmc', 'pkrs', 'kctxmc', 'kcsxmc', 'tzdlb', 'pgtj', 'jx02id', 'sfkfxk', 'kxh',
        'bjbkx', 'sftk', 'xbyq', 'kcxzm', 'xkrs', 'kkxnxq', 'zxs', 'xnxq01id', 'jx0404id', 'xf', 'ctsm', 'szkcflmc',
        'xbyqmc', 'sksj', 'skls', 'ksfs', 'kcxzmc', 'zybkx', 'isxwkc', 'zyfx', 'syrs', 'xqid', 'skdd', 'szkcfl',
        'kkapList', 'kcsx', 'kctxid', 'kkdw', 'khfs', '__type']


def load_key_translation(path):
    translation = dict()
    if os.path.isfile(path):
        with open(path, encoding='utf8') as f:
            for line in f.readlines():
                if line and not line.startswith('#'):
                    try:

                        ori, _, chn = line.strip('\n').split(':')
                        translation[ori] = chn
                    except ValueError:
                        pass
    return translation


def main():
    data = []

    if os.path.isfile('course_data.json'):
        with open('course_data.json', encoding='utf8') as f:
            data = json.load(f)
    else:
        print('ERROR: No course data available')
        exit(1)
    if data:
        translation = load_key_translation('key_translations')
        f = open('export.csv', 'w', encoding='utf_8_sig', newline='')  # UTF-8 with BOM
        csv_writer = csv.writer(f, dialect='excel')
        csv_writer.writerow([translation.get(r) for r in ROWS])
        write_rows = list()
        for course_data in data:
            row = [None for i in range(len(ROWS))]
            for _k, _v in course_data.items():
                if type(_v) == str:
                    _v = _v.replace('<br>', ' ')
                row[ROWS.index(_k)] = _v
            write_rows.append(row)
        write_rows.sort(key=lambda r: r[0])
        csv_writer.writerows(write_rows)
        f.close()
        print('Done!')
    else:
        print('No data to export')


if __name__ == '__main__':
    main()
