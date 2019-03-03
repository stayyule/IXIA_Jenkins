import paramiko

def simple_connect(cmd='ls -l'):

	hostname = '192.168.217.136'
	username = 'gns3@192.218.217.136'
	password = 'gns3'


	ssh = paramiko.client.SSHClient()
	ssh.load_system_host_keys()
	ssh.connect(hostname=hostname, username=username, password = password)
	stdin, stdout, stderr = ssh.exec_command(cmd)
	result = stdout.read()
	print(result)
	ssh.close()

	
