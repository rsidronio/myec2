#!/bin/env python

import boto3
import time
import argparse
from tabulate import tabulate

client = boto3.client("ec2")

#argument parsers
parser = argparse.ArgumentParser()

options_parser = argparse.ArgumentParser(add_help=False)
options_parser.add_argument("-t", "--tag-name", action="store_true",help="uses instance tag-name instead of id")
options_parser.add_argument("-a", "--addresses", action="store_true",help="print instance addresses")
options_parser.add_argument("-w", "--wait", action="store_true",help="wait for instance to start/stop")

subparsers = parser.add_subparsers(required=True, dest='cmd')

# commands:
# start
parser_start = subparsers.add_parser('start', help='start instances', parents=[options_parser])
parser_start.add_argument('start_id', nargs='+', type=str,metavar="instance_id", help='instance id\'s')
# stop
parser_stop = subparsers.add_parser('stop', help='stop instances', parents=[options_parser])
parser_stop.add_argument('stop_id', nargs='+', type=str,metavar="instance_id", help='instance id\'s')
# list
parser_list = subparsers.add_parser('list', help='list instances', parents=[options_parser])

args = parser.parse_args()

# emoticon pensativo
def loading_dots(load_msg, dot_time):
	for i in range(0,4):
		print(load_msg+"."*i, end="\r")
		time.sleep(dot_time)
		print(load_msg+"   ",end="\r")

if args.cmd == "start":
	#TODO - resolver essas gambiarra repetida

	client.start_instances(InstanceIds=args.start_id)
	print("Starting instance(s)")

	if args.wait:
		for instance_id in args.start_id:
			while boto3.resource('ec2').Instance(instance_id).state['Name'] != "running":
				loading_dots(f"Starting {instance_id}", 2)
			print(f"\r{instance_id} is \033[0;32mrunning\033[0m ")

	# if args.addresses:
	# 	print("ADDRESES OPTION ACTIVAET")

if args.cmd == "stop":

	client.stop_instances(InstanceIds=args.stop_id)
	print("Stopping instance(s)")

	if args.wait:
		for instance_id in args.stop_id:
			while boto3.resource('ec2').Instance(instance_id).state['Name'] != "stopped":
				loading_dots(instance_id, 2)
			print(f"\r{instance_id} has \033[0;31mstopped\033[0m ")

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

	print("\n", tabulate(instance_list, headers=[
			'Instance Id', 'State', 'Tag'], tablefmt="simple"), "\n", sep="")

if args.tag_name:
    print('TAG NAME ATIVADA')
