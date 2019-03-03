import requests
import json
import time
import sys
import pandas as pd

class QuickTest:
	
	def __init__(self):		
		self.session_id = "1"
		self.api_server = ""
		self.platform = ""
		self.session = ""
		self.headers = ""

		
	def __waitSuccess(self, result, addServer=False):
		print(result.content)
		url = result.json()["url"]
		if addServer:
			url = self.api_server + url
		state = result.json()["state"]
		# -- wait until finish
		while state == "IN_PROGRESS":
			result = self.session.get(url, headers=self.headers, verify=False)
			state = result.json()["state"]
			print(state)
			time.sleep(2)

			
	def connect(self, platform="windows"):
	
		requests.packages.urllib3.disable_warnings()
		self.platform = platform
		# difference between windows and linux server connection
		print("Server:" + self.platform)
		
		if self.platform == "windows":
			self.api_server = 'http://192.168.217.128:11009'
		if self.platform == "linux":
			self.api_server = 'https://192.168.217.129'
		
		# http request session
		self.session = requests.session()
		# linux optional
		#session.mount('https://', TlsAdapter())

		self.headers = {
			'content-type': 'application/json'
		}
		
		# session management on linux api server
		if self.platform == "linux":
			body = {
				"username": "admin",
				"password": "admin"
			}
			# login, you can also create / delete / view sessions as well
			result = self.session.post(self.api_server + "/api/v1/auth/session", headers=self.headers, data=json.dumps(body), verify=False)
			print(result.content)
			# create session
			url = self.api_server + "/api/v1/sessions"
			body = {
				"applicationType": "ixnrest"
			}
			result = self.session.post(url, headers=self.headers, data=json.dumps(body), verify=False)
			print(result.content)
			self.session_id = str(result.json()["id"])
			# start session
			url = self.api_server + "/api/v1/sessions/" + self.session_id + "/operations/start"
			result = self.session.post(url, headers=self.headers, verify=False)
			
			self.__waitSuccess(result)
		else:
			# cleanup
			result = self.session.post(self.api_server + "/api/v1/sessions/" + self.session_id + "/ixnetwork/operations/newconfig")
			
			self.__waitSuccess(result)
	
	
	def createTraffic(self, chassisIp, duration=30, csvDir=""):
		# create vports
		url = self.api_server + "/api/v1/sessions/" + self.session_id + "/ixnetwork/vport"
		body = [
			{
				"name": "port tx"
			},
			{
				"name": "port rx"
			}
		]
		result = self.session.post(url, headers=self.headers, data=json.dumps(body), verify=False)
		print("Return:", result.status_code)
		print("Content:", result.content)
		# -- get port url
		tx_port_url = result.json()["links"][0]["href"]
		rx_port_url = result.json()["links"][1]["href"]
		print(tx_port_url, rx_port_url)
		# -- set port flow control
		url = self.api_server + tx_port_url + "/l1Config/ethernet"
		body = {
			"enabledFlowControl": False
		}
		result = self.session.patch(url, headers=self.headers, data=json.dumps(body), verify=False)
		print(result)
		url = self.api_server + rx_port_url + "/l1Config/ethernet"
		result = self.session.patch(url, headers=self.headers, data=json.dumps(body), verify=False)
		print(result)

		# create traffic
		url = self.api_server + "/api/v1/sessions/" + self.session_id + "/ixnetwork/traffic/trafficItem"
		body = {
			"name": "simple_traffic",
			"trafficType": "raw"
		}
		result = self.session.post(url, headers=self.headers, data=json.dumps(body), verify=False)
		print(result.content)
		# -- get traffic handle
		simple_traffic_item = result.json()["links"][0]["href"]
		print(simple_traffic_item)
		# -- create endpoint set
		url = self.api_server + simple_traffic_item + "/endpointSet"
		body = {
			"sources": [
				tx_port_url + "/protocols"
			],
			"destinations": [
				rx_port_url + "/protocols"
			]
		}
		result = self.session.post(url, headers=self.headers, data=json.dumps(body), verify=False)
		print(result)
		# -- set traffic item tracking
		url = self.api_server + simple_traffic_item + "/tracking"
		body = {
			"trackBy": [
				"trackingenabled0"
			]
		}
		result = self.session.patch(url, headers=self.headers, data=json.dumps(body), verify=False)
		print(result)

		# Config license server(optional)
		url = self.api_server + "/api/v1/sessions/" + self.session_id + "/ixnetwork/globals/licensing"
		body = {
			"licensingServers": [
				chassisIp
			]
		}
		self.session.patch(url, headers=self.headers, data=json.dumps(body), verify=False)

		# Assign Real ports
		url = self.api_server + "/api/v1/sessions/" + self.session_id + "/ixnetwork/operations/assignports"
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
		result = self.session.post(url, headers=self.headers, data=json.dumps(body), verify=False)

		self.__waitSuccess(result, True)
		
		# Apply traffic
		url = self.api_server + "/api/v1/sessions/" + self.session_id + "/ixnetwork/traffic/operations/apply"
		body = {
			"arg1": "/api/v1/sessions/" + self.session_id + "/ixnetwork/traffic"
		}
		result = self.session.post(url, headers=self.headers, data=json.dumps(body), verify=False)
		
		self.__waitSuccess(result)
		

		# Start traffic
		url = self.api_server + "/api/v1/sessions/" + self.session_id + "/ixnetwork/traffic/operations/start"
		body = {
			"arg1": "/api/v1/sessions/" + self.session_id + "/ixnetwork/traffic"
		}
		result = self.session.post(url, headers=self.headers, data=json.dumps(body), verify=False)
		self.__waitSuccess(result)
		

		# test duration
		print("start traffic for", duration)
		time.sleep(int(duration))

		# Stop traffic
		url = self.api_server + "/api/v1/sessions/" + self.session_id + "/ixnetwork/traffic/operations/stop"
		body = {
			"arg1": "/api/v1/sessions/" + self.session_id + "/ixnetwork/traffic"
		}
		result = self.session.post(url, headers=self.headers, data=json.dumps(body), verify=False)
		self.__waitSuccess(result)
		

		# Fetch stats
		time.sleep(10)
		url = self.api_server + "/api/v1/sessions/" + self.session_id + "/ixnetwork/statistics/view"
		result = self.session.get(url, headers=self.headers, verify=False)
		print(result.content)
		for view in result.json():
			print(view["caption"], view["links"][0]["href"])
			if view["caption"] == "Traffic Item Statistics":
				# # get view info
				result = self.session.get(self.api_server + view["links"][0]["href"], headers=self.headers, verify=False)
				print(result.content)
				# # get stats
				url = self.api_server + view["links"][0]["href"] + "/page"
				result = self.session.get(url, headers=self.headers, verify=False)
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


		return test_result, s
		

	def runQuickTest(self):

		# create quick test
		url = self.api_server + "/api/v1/sessions/" + self.session_id + "/ixnetwork/quickTest/rfc2544throughput"
		body = [
			{
				"mode": "existingMode",
				"name": "demo_2544_thput"
			}
		]
		result = self.session.post(url, headers=self.headers, data=json.dumps(body), verify=False)
		print(result.content)
		qt_id = result.json()["links"][0]["href"]
		print("id", qt_id)
		
		# create traffic selection
		url = self.api_server + qt_id + "/trafficSelection"
		body = [
			{
				"__id__": "/api/v1/sessions/" + self.session_id + "/ixnetwork/traffic/trafficItem/1"
			}
		]
		result = self.session.post(url, headers=self.headers, data=json.dumps(body), verify=False)
		print(result.content)

		# modify test config
		url = self.api_server + qt_id + "/testConfig"
		body = {
			"framesizeList": [
				"128",
				"1518"
			],
			"frameSizeMode": "custom",
			"initialBinaryLoadRate": 100,
			"minBinaryLoadRate": 70,
			"maxBinaryLoadRate": 100
		}
		result = self.session.patch(url, headers=self.headers, data=json.dumps(body), verify=False)
		print(result)

		# run the test
		url = self.api_server + qt_id + "/operations/run"
		body = {
			"arg1": qt_id,
			"arg2": ""
		}
		result = self.session.post(url, headers=self.headers, data=json.dumps(body), verify=False)
		print(result.content)
		# -- get action url
		state = result.json()["state"]
		url = self.api_server + result.json()["url"]
		# -- wait until finish
		while state == "IN_PROGRESS":
			result = self.session.get(url, headers=self.headers, verify=False)
			state = result.json()["state"]
			progress = result.json()["progress"]
			test_result = result.json()["result"]
			test_result_url = result.json()["resultUrl"]
			print(state, progress)
			time.sleep(10)

		print(test_result, test_result_url)		
		
		# delete session when pass leave the session to check when fail.
		if self.platform == "linux":
			url = self.api_server + "/api/v1/sessions/" + self.session_id + "/operations/stop"
			result = self.session.post(url, headers=self.headers, verify=False)

			self.__waitSuccess(result)
			
			url = self.api_server + "/api/v1/sessions/" + self.session_id
			result = self.session.delete(url, headers=self.headers, verify=False)
			print(result)
