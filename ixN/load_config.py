import requests
import json
import time
import sys

def load(path):
	'''
	This proc is a sample showing how to load an existing ixncfg config file with restful \r\n
	path: str local file full path
	'''
	
	requests.packages.urllib3.disable_warnings()

	# id will always be 1 when using windows platform
	session_id = "1"

	api_server = 'http://192.168.217.128:11009'

	# http request session
	session = requests.session()
	# linux optional
	#session.mount('https://', TlsAdapter())

	headers = {
		'content-type': 'application/json'
	}

	# upload config file
	with open(path, mode='rb') as file:
		configContents = file.read()

	fileName = path.split('/')[-1]

	url = api_server + "/api/v1/sessions/" + session_id + "/ixnetwork/files?filename=" + fileName
	result = session.post(url, headers=headers, data=configContents, verify=False)
	print(result.content)
			
	# load config
	url = api_server + "/api/v1/sessions/" + session_id + "/ixnetwork/operations/loadconfig"
	data = {
		'arg1': fileName
	}
	result = session.post(url, headers=headers, data=json.dumps(data), verify=False)
	# -- get action url
	state = result.json()["state"]
	url = api_server + result.json()["url"]
	# -- wait until finish
	while state == "IN_PROGRESS":
		result = session.get(url, headers=headers, verify=False)
		state = result.json()["state"]
		print(state)
		time.sleep(2)
	