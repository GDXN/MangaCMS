
import sys

import os.path
import runStatus
from utilities.dedupDir import DirDeduper
import signal
import activePlugins


def customHandler(dummy_signum, dummy_stackframe):
	if runStatus.run:
		runStatus.run = False
		print("Telling threads to stop")
	else:
		print("Multiple keyboard interrupts. Raising")
		raise KeyboardInterrupt

def install_signal_handler():

	signal.signal(signal.SIGINT, customHandler)

def get_plugins():
	ret = {}
	for plugin_module, dummy_interval in activePlugins.scrapePlugins.values():
		plugin = plugin_module.Runner
		print("plugin.pluginName: ", plugin.pluginName)
		# print(dir(plugin))
		if not hasattr(plugin, 'pluginName'):
			print("No pluginName: ", plugin)
			continue

		if not hasattr(plugin, 'feedLoader'):
			print("No feedLoader: ", plugin)
			continue
		if not hasattr(plugin, 'contentLoader'):
			print("No contentLoader: ", plugin)
			continue

		if not hasattr(plugin.feedLoader, 'tableKey'):
			print("No tableKey in feedLoader: ", plugin.feedLoader)
			continue

		if plugin.feedLoader.tableKey != "mk":
			assert plugin.feedLoader.tableKey not in ret, "Duplicate keys? Key: %s, for %s, matches %s" % (
				plugin.feedLoader.tableKey, plugin, ret[plugin.feedLoader.tableKey]['name'])
		ret[plugin.feedLoader.tableKey] = {
			'feedLoader'    : plugin.feedLoader,
			'contentLoader' : plugin.contentLoader,
			'runner'        : plugin,
			'name'          : plugin.pluginName,
			"is_h"          : ".H." in plugin_module.__name__
		}
	return ret

def print_plgs(keylist, plugins):
	for plg_key in keylist:

		print("	key: '{}'".format(plg_key))
		print("		Name: ", plugins[plg_key]['name'])
		print("		Runner Module: ", plugins[plg_key]['runner'])


def listPlugins():
	plgs = get_plugins()
	keys = list(plgs.keys())
	keys.sort()

	mk = [key for key in keys if not plgs[key]["is_h"]]
	hk = [key for key in keys if plgs[key]["is_h"]]

	print("Manga Scrapers:")
	print_plgs(mk, plgs)
	print("")
	print("Hentai Scrapers:")
	print_plgs(hk, plgs)

def runPlugin(plug):
	install_signal_handler()

	plgs = get_plugins()
	if not plug in plgs:
		print("Key {} not in available plugins!".format(plug))
		for key, plgd in plgs.items():
			print("	Plugin {} -> {}!".format(key, plgd['name']))
		return

	to_run = plgs[plug]
	runner = to_run['runner']()
	runner.go()


def retagPlugin(plug):
	install_signal_handler()

	plgs = get_plugins()
	if not plug in plgs:
		print("Key {} not in available plugins ({})!".format(plug, list(plgs.keys())))
		return

	print("NOT IMPLEMENTED YET (OR EVER?)")
	# to_run = plgs[plug]
	# runner = to_run['runner']()
	# runner.go()






