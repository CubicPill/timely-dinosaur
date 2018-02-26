"""
entry of the program
"""
import argparse
from webgui import init as w_init
from enroll import init as e_init

VERSION = 'v1.2.2'
print('Timely Dinosaur ' + VERSION + ', Author: CubicPill')

arg_parser = argparse.ArgumentParser(description='SUSTech course auto enroll')
arg_parser.add_argument('-w', '--web', help='Open local web gui', action='store_true')
args = arg_parser.parse_args()
if args.web:
    w_init()
else:
    e_init()
