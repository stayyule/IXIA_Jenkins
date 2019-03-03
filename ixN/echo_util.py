import pandas as pd
import json

def int_brief(echo, csvDir = ""):
	'''
	this proc is a sample showing how to get information from interface brief echo
	'''
	print(echo)
	# read echo line by line
	echo_lines = echo.split("\r\n")
	print(len(echo_lines))
	
	# get start point of each captions
	ip_index = echo_lines[0].find('IP-Address')
	ok_index = echo_lines[0].find('OK?')
	method_index = echo_lines[0].find('Method')
	status_index = echo_lines[0].find('Status')
	pro_index = echo_lines[0].find('Protocol')
	
	# insert a ',' ahead of each captions except the first
	new_line = ""
	for line in echo_lines[:-1]:
		line_list = list(line)
		line_list.insert(pro_index, ",")
		line_list.insert(status_index, ",")
		line_list.insert(method_index, ",")
		line_list.insert(ok_index, ",")
		line_list.insert(ip_index, ",")
		new_line = new_line + "".join(line_list) + "\r\n"
	
	print(new_line)
	# save new line to csv format
	with open(csvDir + '/int_brief.csv', 'w') as f:
		f.write(new_line)
	
	# read csv file to pandas
	df = pd.read_csv(csvDir + "/int_brief.csv")
	
	# strip table
	df.columns = df.columns.str.strip()
	for i in range(df.shape[0]):
		df.loc[i,:] = df.loc[i,:].str.strip()

	# get information from data frame
	print(df)
	link = df.at[1,'Status']
	protocol = df.at[1,'Protocol']
	
	print("link:" + link, "protocol:" + protocol)
	return link, protocol 
	
	