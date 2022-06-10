#!/bin/env python

import os
import sys
import boto3
import time
import argparse
import configparser

from botocore.exceptions import ClientError
from tabulate import tabulate
#from terminaltables import AsciiTable, DoubleTable, SingleTable



########COLORS#######
## tirar daqui depois
GREEN = '\033[0;32m'
RED = '\033[0;31m'
HEADER = '\033[95m'
OKBLUE = '\033[94m'
OKCYAN = '\033[96m'
OKGREEN = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'
BOLD = '\033[1m'
DIM = '\033[2m'
UNDERLINE = '\033[4m'


client = boto3.client("ec2")

config = configparser.ConfigParser()
config.read('config')

os.environ["AWS_ACCESS_KEY_ID"] = config['aws']['aws_access_key_id']
os.environ["AWS_SECRET_ACCESS_KEY"] = config['aws']['aws_secret_access_key']
os.environ["AWS_DEFAULT_REGION"] = config['aws']['default_region']

#argument parsers
parser = argparse.ArgumentParser()

options_parser = argparse.ArgumentParser(add_help=False)
options_parser.add_argument("-t", "--tag-name", action="store_true",help="Uses instance tag-name instead of ID")
options_parser.add_argument("-a", "--addresses", action="store_true",help="Print instance addresses")
options_parser.add_argument("-w", "--wait", action="store_true",help="Wait for instance to start/stop")

subparsers = parser.add_subparsers(required=True, dest='cmd')

# commands:
# start
parser_start = subparsers.add_parser('start', help='Start instances', parents=[options_parser])
parser_start.add_argument('id', nargs='+', type=str,metavar="instance_id", help='instance id\'s')
# stop
parser_stop = subparsers.add_parser('stop', help='Stop instances', parents=[options_parser])
parser_stop.add_argument('id', nargs='+', type=str,metavar="instance_id", help='instance id\'s')
# list
parser_list = subparsers.add_parser('list', help='List instances')
# configure
parser_configure = subparsers.add_parser('configure', help='Set AWS credentials')

args = parser.parse_args()

# emoticon pensativo
def loading_dots(load_msg, dot_time):
	for i in range(0,4):
		print("\033[?25l"+load_msg+"."*i, end="\r")
		time.sleep(dot_time)
		print(load_msg+"   ",end="\r")

if args.cmd == "start" or args.cmd == "stop":
	#TODO - resolver essas gambiarra
    aux = ("Starting", "running", f"is {GREEN}") if args.cmd == "start" else ("Stopping", "stopped", f"has {RED}")
    try:
        if args.cmd == "start":
            client.start_instances(InstanceIds=args.id)
        else:
            client.stop_instances(InstanceIds=args.id)
        print(f"{aux[0]} instance(s)")

    except ClientError as e:
        print(f"{RED}Error{ENDC}", e.response["Error"]['Message'])
        sys.exit(1)

    if args.wait:
        for instance_id in args.id:
            while boto3.resource('ec2').Instance(instance_id).state['Name'] != aux[1]:
                loading_dots(f"{aux[0]} {instance_id}", 2)
            print(f"\r{instance_id} {aux[2]}{aux[1]}{ENDC} \033[?25h")

	# if args.addresses:
	# 	print("ADDRESES OPTION ACTIVAET")

if args.cmd == "list":
	# TODO - checar se pode ter varias tags e como fica output com tag nula
	#	   - sort por estado, de running até terminated
	#	   - agrupar por zona

	reservations = client.describe_instances()['Reservations']
	instance_list = []
	for reservation in reservations:
		for instance in reservation["Instances"]:
			instance_id = instance["InstanceId"]
			instance_tag = instance["Tags"][0]['Value']
			instance_state = instance['State']['Name']

			if instance_state == 'running':
				instance_state = "\033[0;32m"+instance_state+"\033[0m"

			instance_list.append([instance_id, instance_state, instance_tag])
	print("\n"+tabulate(instance_list, headers=[
			'Instance Id', 'State', 'Tag'], tablefmt="simple"), "\n", sep="")

	# TABLE_DATA = (
    # ('Instance Id', 'State', 'Tag'),
    # ('i-0ccc85407f15e6271', 'stopped', 'ubuntu'),
    # ('i-09148548f15a84e47', 'stopped', 'foundry-server'),
	# )

	# title = 'us-east-2'
	# table_instance = SingleTable(TABLE_DATA, title)
	# table_instance.outer_border = True
	# table_instance.inner_column_border = True
	# table_instance.inner_footing_row_border = False
	# table_instance.inner_heading_row_border = True
	# table_instance.inner_row_border = False
	# # table_instance.justify_columns[0] = 'center'
	# print(table_instance.table)

def mask(key):
    if not key:
        return "None"
    return ("*"*16)+key[-4:]

if args.cmd == "configure":

    new_access_id = input(
        f"AWS Access Key ID [{mask(config['aws']['aws_access_key_id'])}]: ")
    if new_access_id:
        config.set('aws','aws_access_key_id', new_access_id)

    new_secret_key = input(
        f"AWS Secret Access Key ID [{mask(config['aws']['aws_secret_access_key'])}]: ")
    if new_secret_key:
        config.set('aws','aws_secret_access_key', new_secret_key)

    new_default_region = input(
        f"Default region name [{mask(config['aws']['default_region'])}]: ")
    if new_default_region:
        config.set('aws','default_region', new_default_region)

    with open('config', 'w', encoding="utf-8") as configfile:
        config.write(configfile)