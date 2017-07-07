
import os.path
import json

from plumbum.machines.paramiko_machine import ParamikoMachine
from paramiko.client import MissingHostKeyPolicy
from rpyc.utils.zerodeploy import DeployedServer


# will raise exception
class ignoreIt(MissingHostKeyPolicy):
	def missing_host_key(self, client, hostname, key):
		pass


# You have to figure this part out
# Protip: You need a folder called 'deploy.shim', and a settings file in json format.
def getCreds():
	fpath = os.path.join(os.path.split(__file__)[0], 'deploy.shim', 'settings.json')
	with open(fpath) as fp:
		creds = json.loads(fp.read())

	creds['remote key'] = os.path.join(os.path.split(__file__)[0], 'deploy.shim', creds['remote key'])
	return creds

def go():

	creds = getCreds()

	print("Connecting...")
	mach = ParamikoMachine(creds['remote address'], user=creds['remote user'], keyfile=creds['remote key'], missing_host_policy=ignoreIt())
	print("Deploying RPC interface...")
	server = DeployedServer(mach)
	print("Connected.")

	conn = server.classic_connect()

	import webFunctions
	webFunctions.urllib.request = conn.modules['urllib.request']

	wg = webFunctions.WebGetRobust()
	print(wg.getpage('http://api.ipify.org?format=json'))

	import ScrapePlugins.H.SadPandaLoader.Run

	ScrapePlugins.H.SadPandaLoader.Run.test()

if __name__ == "__main__":
	go()
