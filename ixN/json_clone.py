# Python    JSON
# dict      object
# list      array
# str       string
# int       number
# True      true
# False     false


# API Browser python code snippet
import requests
import json
import time
import pandas as pd

def clone_topology(chassisIp, topology_number=2):

	print('chassis', chassisIp)
	false = False
	true = True

	api_server = '192.168.217.128'
	print('Export json object...')
	headers = {
		'content-type': 'application/json'
	}
	body = {
		'arg1': '/api/v1/sessions/1/ixnetwork/resourceManager',
		'arg2': [
			'/topology[1]/descendant-or-self::*'
		],
		'arg3': False,
		'arg4': 'json'
	}
	result = requests.request('POST', 'http://' + api_server + ':11009/api/v1/sessions/1/ixnetwork/resourceManager/operations/exportconfig', headers=headers, data=json.dumps(body), verify=False)
	print(result.content)
	url = 'http://' + api_server + ':11009' + result.json()["url"]
	state = result.json()["state"]
	# -- wait until finish
	while state == "IN_PROGRESS":
		result = requests.request('GET', url, headers=headers, verify=False)
		state = result.json()["state"]
		print(state)
		time.sleep(2)
		
	# To get response json dict
	print("RESPONSE:")
	response_json = result.json()
	print(response_json)

	# To get result json dict
	print("RESULT:")
	result_json = eval(response_json["result"])

	print(result_json)
	print(result_json["topology"])

	# To get topology json dict
	print("TOPOLOGY:")
	topo_json = eval(str(result_json["topology"][0]))
	print(topo_json["name"])
	print(topo_json["vports"])

	# Copy dict to create new topology
	print("NEW TOPOLOGY:")
	new_topo = topo_json.copy()
	# Change x-path and port
	new_topo = eval(str(new_topo).replace('topology[1]','topology['+ str(topology_number) + ']'))
	new_topo["name"]="BGP_" + str(topology_number) + " Topology"
	new_topo["vports"]=['/vport[{0}]'.format(topology_number)]

	print(new_topo)
	# Append new topo to original
	#result_json["topology"].clear()
	result_json["topology"].append(new_topo)
	print(result_json)

	# Import json again
	body = {
		'arg1': '/api/v1/sessions/1/ixnetwork/resourceManager',
		'arg2': json.dumps(result_json),
		'arg3': False,
	}
	response = requests.request('POST', 'http://' + api_server + ':11009/api/v1/sessions/1/ixnetwork/resourceManager/operations/importconfig', headers=headers, data=json.dumps(body), verify=False)
	print(response.content)
	
	# Assign Real ports
	url = 'http://' + api_server + ":11009/api/v1/sessions/1/ixnetwork/operations/assignports"
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
			"/api/v1/sessions/1/ixnetwork/vport/1",
			"/api/v1/sessions/1/ixnetwork/vport/2"
		],
		"arg4": True
	}
	result = requests.request('POST', url, headers=headers, data=json.dumps(body), verify=False)
	print(result.content)
	# -- get action url
	state = result.json()["state"]
	url ='http://' + api_server + ":11009" + result.json()["url"]
	# -- wait until finish
	while state == "IN_PROGRESS":
		result = requests.request('GET', url, headers=headers, verify=False)
		state = result.json()["state"]
		print(state)
		time.sleep(2)
	print(result.content)

	
def config_topology(topology_number, mac_address, ip_address, gateway_address, bgp_id, dut_ip, router_id, network_address):

	ixnetwork_api_server = 'http://192.168.217.128:11009'

	headers = {
		'content-type': 'application/json'
	}
	
	# mac_address = "18:03:73:c7:6c:a1"
	# ip_address = "20.20.20.1"
	# gateway_address = "20.20.20.2"
	# bgp_id = "192.0.0.2"
	# dut_ip = "20.20.20.2"
	# router_id = "192.0.0.2"
	# network_address = "201.1.0.0"

	# Ethernet Mac
	response = requests.request('GET', ixnetwork_api_server + '/api/v1/sessions/1/ixnetwork/topology/'+ str(topology_number) +'/deviceGroup/1/ethernet/1', headers=headers, verify=False)
	print(response.content)
	mac_multivalue = response.json()["mac"]

	body = {
		"value": mac_address
	}
	patchUrl = ixnetwork_api_server + mac_multivalue + '/singleValue'

	response = requests.request('PATCH', patchUrl, headers=headers, data=json.dumps(body), verify=False)
	print(response)

	# IPv4 addr and gw
	response = requests.request('GET', ixnetwork_api_server + '/api/v1/sessions/1/ixnetwork/topology/'+str(topology_number)+'/deviceGroup/1/ethernet/1/ipv4/1', headers=headers, verify=False)
	addr_multivalue = response.json()["address"]
	gw_multivalue = response.json()["gatewayIp"]
	body = {
		"value": ip_address
	}
	patchUrl = ixnetwork_api_server + addr_multivalue + '/singleValue'
	response = requests.request('PATCH', patchUrl, headers=headers, data=json.dumps(body), verify=False)
	print(response)
	body = {
		"value": gateway_address
	}
	patchUrl = ixnetwork_api_server + gw_multivalue + '/singleValue'
	response = requests.request('PATCH', patchUrl, headers=headers, data=json.dumps(body), verify=False)
	print(response)

	# BGP
	response = requests.request('GET', ixnetwork_api_server + '/api/v1/sessions/1/ixnetwork/topology/' + str(topology_number) + '/deviceGroup/1/ethernet/1/ipv4/1/bgpIpv4Peer/1', headers=headers, verify=False)
	bgpId_multivalue = response.json()["bgpId"]
	dutIp_multivalue = response.json()["dutIp"]
	body = {
		"value": bgp_id
	}
	patchUrl = ixnetwork_api_server + bgpId_multivalue + '/singleValue'
	response = requests.request('PATCH', patchUrl, headers=headers, data=json.dumps(body), verify=False)
	print(response)
	body = {
		"value": dut_ip
	}
	patchUrl = ixnetwork_api_server + dutIp_multivalue + '/singleValue'
	response = requests.request('PATCH', patchUrl, headers=headers, data=json.dumps(body), verify=False)
	print(response)

	# DeviceGroup
	response = requests.request('GET', ixnetwork_api_server + '/api/v1/sessions/1/ixnetwork/topology/' + str(topology_number) + '/deviceGroup/1/routerData/1', headers=headers, verify=False)
	rid_multivalue = response.json()["routerId"]
	body = {
		"value": router_id
	}
	patchUrl = ixnetwork_api_server + rid_multivalue + '/singleValue'
	response = requests.request('PATCH', patchUrl, headers=headers, data=json.dumps(body), verify=False)
	print(response)

	# Route Range
	response = requests.request('GET', ixnetwork_api_server + '/api/v1/sessions/1/ixnetwork/topology/' + str(topology_number) + '/deviceGroup/1/networkGroup/1/ipv4PrefixPools/1', headers=headers, verify=False)
	na_multivalue = response.json()["networkAddress"]
	body = {
		"value": network_address
	}
	patchUrl = ixnetwork_api_server + na_multivalue + '/singleValue'
	response = requests.request('PATCH', patchUrl, headers=headers, data=json.dumps(body), verify=False)
	print(response)

	# Start all protocols
	startProtocolUrl = ixnetwork_api_server + "/api/v1/sessions/1/ixnetwork/operations/startallprotocols"
	response = requests.request('POST', startProtocolUrl, headers=headers, verify=False)
	print(response.content)

	time.sleep(30)

	# Collect stats
	url = api_server + "/api/v1/sessions/" + session_id + "/ixnetwork/statistics/view"
	result = session.get(url, headers=headers, verify=False)
	print(result.content)
	for view in result.json():
		print(view["caption"], view["links"][0]["href"])
		if view["caption"] == "BGP Peer Per Port":
			# # get view info
			result = session.get(api_server + view["links"][0]["href"], headers=headers, verify=False)
			print(result.content)
			# # get stats
			url = api_server + view["links"][0]["href"] + "/page"
			result = session.get(url, headers=headers, verify=False)
			columnCaptions = response.json()["columnCaptions"]
			pageValues = response.json()["pageValues"]
	

	df = pd.DataFrame([pageValues[0][0],pageValues[1][0]], columns=columnCaptions)
	print(df)
	