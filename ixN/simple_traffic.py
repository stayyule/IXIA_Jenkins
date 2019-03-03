import requests
import json
import time
import sys
import pandas as pd


def run(chassisIp, platform="windows", duration=30, csvDir = ""):
	'''
	This proc is a sample showing how to build traffic from scratch with restful \r\n
	chassisIp: the ip address of chassis, \r\n
	platform: 'windows' | 'linux'
	'''
	requests.packages.urllib3.disable_warnings()

	# difference between windows and linux server connection
	print("Server:" + platform)

	# id will always be 1 when using windows platform
	session_id = "1"
	api_server = ""

	if platform == "windows":
		api_server = 'http://192.168.217.128:11009'
	if platform == "linux":
		api_server = 'https://192.168.217.129'

	# http request session
	session = requests.session()
	# linux optional
	#session.mount('https://', TlsAdapter())

	headers = {
		'content-type': 'application/json'
	}

	# session management on linux api server
	if platform == "linux":
		body = {
			"username": "admin",
			"password": "admin"
		}
		# login, you can also create / delete / view sessions as well
		result = session.post(api_server + "/api/v1/auth/session", headers=headers, data=json.dumps(body), verify=False)
		print(result.content)
		# create session
		url = api_server + "/api/v1/sessions"
		body = {
			"applicationType": "ixnrest"
		}
		result = session.post(url, headers=headers, data=json.dumps(body), verify=False)
		print(result.content)
		session_id = str(result.json()["id"])
		# start session
		url = api_server + "/api/v1/sessions/" + session_id + "/operations/start"
		result = session.post(url, headers=headers, verify=False)
		print(result.content)
		url = result.json()["url"]
		state = result.json()["state"]
		# -- wait until finish
		while state == "IN_PROGRESS":
			result = session.get(url, headers=headers, verify=False)
			state = result.json()["state"]
			print(state)
			time.sleep(2)
	else:
		# cleanup
		result = session.post(api_server + "/api/v1/sessions/" + session_id + "/ixnetwork/operations/newconfig")
		print(result.content)
		# -- get action url
		state = result.json()["state"]
		url = api_server + result.json()["url"]
		# -- wait until finish
		while state == "IN_PROGRESS":
			result = session.get(url, headers=headers, verify=False)
			state = result.json()["state"]
			print(state)
			time.sleep(2)

	# create vports
	url = api_server + "/api/v1/sessions/" + session_id + "/ixnetwork/vport"
	body = [
		{
			"name": "port tx"
		},
		{
			"name": "port rx"
		}
	]
	result = session.post(url, headers=headers, data=json.dumps(body), verify=False)
	print("Return:", result.status_code)
	print("Content:", result.content)
	# -- get port url
	tx_port_url = result.json()["links"][0]["href"]
	rx_port_url = result.json()["links"][1]["href"]
	print(tx_port_url, rx_port_url)
	# -- set port flow control
	url = api_server + tx_port_url + "/l1Config/ethernet"
	body = {
		"enabledFlowControl": False
	}
	result = session.patch(url, headers=headers, data=json.dumps(body), verify=False)
	print(result)
	url = api_server + rx_port_url + "/l1Config/ethernet"
	result = session.patch(url, headers=headers, data=json.dumps(body), verify=False)
	print(result)

	# create traffic
	url = api_server + "/api/v1/sessions/" + session_id + "/ixnetwork/traffic/trafficItem"
	body = {
		"name": "simple_traffic",
		"trafficType": "raw"
	}
	result = session.post(url, headers=headers, data=json.dumps(body), verify=False)
	print(result.content)
	# -- get traffic handle
	simple_traffic_item = result.json()["links"][0]["href"]
	print(simple_traffic_item)
	# -- create endpoint set
	url = api_server + simple_traffic_item + "/endpointSet"
	body = {
		"sources": [
			tx_port_url + "/protocols"
		],
		"destinations": [
			rx_port_url + "/protocols"
		]
	}
	result = session.post(url, headers=headers, data=json.dumps(body), verify=False)
	print(result)
	# -- set traffic item tracking
	url = api_server + simple_traffic_item + "/tracking"
	body = {
		"trackBy": [
			"trackingenabled0"
		]
	}
	result = session.patch(url, headers=headers, data=json.dumps(body), verify=False)
	print(result)

	# Config license server(optional)
	url = api_server + "/api/v1/sessions/" + session_id + "/ixnetwork/globals/licensing"
	body = {
		"licensingServers": [
			"192.168.217.133"
		]
	}
	session.patch(url, headers=headers, data=json.dumps(body), verify=False)

	# Assign Real ports
	url = api_server + "/api/v1/sessions/" + session_id + "/ixnetwork/operations/assignports"
	body = {
		"arg1": [
			{
				"arg1": chassisIp,
				"arg2": "1",
				"arg3": "1"
			},
			{
				"arg1": chassisIp,
				"arg2": "1",
				"arg3": "2"
			}
		],
		"arg2": [],
		"arg3": [
			tx_port_url,
			rx_port_url
		],
		"arg4": True
	}
	result = session.post(url, headers=headers, data=json.dumps(body), verify=False)
	print(result.content)
	# -- get action url
	state = result.json()["state"]
	url = api_server + result.json()["url"]
	# -- wait until finish
	while state == "IN_PROGRESS":
		result = session.get(url, headers=headers, verify=False)
		state = result.json()["state"]
		print(state)
		time.sleep(2)

	# Apply traffic
	url = api_server + "/api/v1/sessions/" + session_id + "/ixnetwork/traffic/operations/apply"
	body = {
		"arg1": "/api/v1/sessions/" + session_id + "/ixnetwork/traffic"
	}
	result = session.post(url, headers=headers, data=json.dumps(body), verify=False)
	print(result.content)
	# -- get action url
	state = result.json()["state"]
	url = api_server + result.json()["url"]
	# -- wait until finish
	while state == "IN_PROGRESS":
		result = session.get(url, headers=headers, verify=False)
		state = result.json()["state"]
		print(state)
		time.sleep(2)

	# Start traffic
	url = api_server + "/api/v1/sessions/" + session_id + "/ixnetwork/traffic/operations/start"
	body = {
		"arg1": "/api/v1/sessions/" + session_id + "/ixnetwork/traffic"
	}
	result = session.post(url, headers=headers, data=json.dumps(body), verify=False)
	print(result.content)
	# -- get action url
	state = result.json()["state"]
	url = api_server + result.json()["url"]
	# -- wait until finish
	while state == "IN_PROGRESS":
		result = session.get(url, headers=headers, verify=False)
		state = result.json()["state"]
		print(state)
		time.sleep(2)

	# test duration
	print("start traffic for", duration)
	time.sleep(int(duration))

	# Stop traffic
	url = api_server + "/api/v1/sessions/" + session_id + "/ixnetwork/traffic/operations/stop"
	body = {
		"arg1": "/api/v1/sessions/" + session_id + "/ixnetwork/traffic"
	}
	result = session.post(url, headers=headers, data=json.dumps(body), verify=False)
	print(result.content)
	# -- get action url
	state = result.json()["state"]
	url = api_server + result.json()["url"]
	# -- wait until finish
	while state == "IN_PROGRESS":
		result = session.get(url, headers=headers, verify=False)
		state = result.json()["state"]
		print(state)
		time.sleep(2)

	# Fetch stats
	time.sleep(10)
	url = api_server + "/api/v1/sessions/" + session_id + "/ixnetwork/statistics/view"
	result = session.get(url, headers=headers, verify=False)
	print(result.content)
	for view in result.json():
		print(view["caption"], view["links"][0]["href"])
		if view["caption"] == "Traffic Item Statistics":
			# # get view info
			result = session.get(api_server + view["links"][0]["href"], headers=headers, verify=False)
			print(result.content)
			# # get stats
			url = api_server + view["links"][0]["href"] + "/page"
			result = session.get(url, headers=headers, verify=False)
			print(result.content)
			print(result.json()["columnCaptions"])
			print(result.json()["pageValues"])
	
	s = pd.Series(result.json()["pageValues"][0][0], index=result.json()["columnCaptions"])
	df = pd.DataFrame(s)
	
	print("save csv result to ..." + csvDir)
	df.T.to_csv(csvDir + "/stats.csv")
	if int(s['Frames Delta']) > 0:
		test_result = False
	else:
		test_result = True

	# delete session when pass leave the session to check when fail.
	if platform == "linux":
		url = api_server + "/api/v1/sessions/" + session_id + "/operations/stop"
		result = session.post(url, headers=headers, verify=False)

		# -- get action url
		state = result.json()["state"]
		url = result.json()["url"]
		# -- wait until finish
		while state == "IN_PROGRESS":
			result = session.get(url, headers=headers, verify=False)
			state = result.json()["state"]
			print(state)
			time.sleep(10)

		url = api_server + "/api/v1/sessions/" + session_id
		result = session.delete(url, headers=headers, verify=False)
		print(result)

	return test_result, s