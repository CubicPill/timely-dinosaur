"""
entry of the program
"""
import argparse

VERSION = 'v2.0.0'
print('Timely Dinosaur ' + VERSION + ', Author: CubicPill')

arg_parser = argparse.ArgumentParser(description='SUSTech course auto enroll')
arg_parser.add_argument('-w', '--web', help='Open local web gui', action='store_true')
args = arg_parser.parse_args()
if args.web:
    from webgui import init
else:
    from enroll import init
init()
