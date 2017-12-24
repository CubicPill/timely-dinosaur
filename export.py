import csv
import os
import json


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
    print(translation)
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
        rows = [k for k in data[0].keys()]
        translation = load_key_translation('key_translations')
        f = open('export.csv', 'w', encoding='utf8')
        csv_writer = csv.writer(f)
        csv_writer.writerow([r or translation.get(r) for r in rows])
        for course_data in data:
            csv_writer.writerow(course_data.values())


if __name__ == '__main__':
    main()
