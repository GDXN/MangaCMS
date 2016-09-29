

import ScrapePlugins.RetreivalDbBase
import ScrapePlugins.IrcGrabber.IrcBot
import irc.client
import irc.bot
import irc.events

import threading
import nameTools as nt
import settings
import os
import os.path
import queue
import time
import json
import runStatus
import traceback
import multiprocessing

import processDownload

import abc
import random
random.seed()

EMOTICONS = {
	'flip-table' : r'(╯°□°）╯︵ ┻━┻',
	'FLIP-TABLE' : r'(ノಠ益ಠ)ノ彡┻━┻',
	'fix-table' : r'┬──┬ ノ( ゜-゜ノ)',
	'table-flip' : r'┬─┬ ︵ /(.□. ）',
	'lenny' : r'( ͡° ͜ʖ ͡°)',
	'shrug' : r'¯\_(ツ)_/¯',
	'lenny-swarm' : r'( ͡°( ͡° ͜ʖ( ͡° ͜ʖ ͡°)ʖ ͡°) ͡°)',
	'lenny-spider' : r'/╲/\\╭( ͡° ͡° ͜ʖ ͡° ͡°)╮/\\╱\\',
	'whry' : r'ლ(ಠ益ಠლ)',
	'kiss' : r'(づ￣ ³￣)づ',
	'grin' : r'☜(⌒▽⌒)☞',
	'happy' : r'( ͡ᵔ ͜ʖ ͡ᵔ )',
	'barrel-roll' : r'(._.) ( l: ) ( .-. ) ( :l ) (._.)',
	'peek' : r'┬┴┬┴┤ ͜ʖ ͡°) ├┬┴┬┴',
	'unsure' : r'(ಥ﹏ಥ)',
	'rpeek' : r'┬┴┬┴┤(･_├┬┴┬┴',
	'smile' : r'(͡ ͡° ͜ つ ͡͡°)',
	'SHOVE' : r'༼ つ ಥ_ಥ ༽つ',
	'shove' : r'༼ つ ͡° ͜ʖ ͡° ༽つ',
	'ORLY' : r'﴾͡๏̯͡๏﴿ O\'RLY?',
	'sad' : r'(；一_一)',
	'flip-tables' : r'┻━┻ ︵ヽ(`Д´)ﾉ︵ ┻━┻',
	'point' : r'(☞ﾟ∀ﾟ)☞',
	'dealwithit' : r'(•_•) ( •_•)>⌐■-■ (⌐■_■)',

	# '' : r'ʕ•ᴥ•ʔ',
	# '' : r'(▀̿Ĺ̯▀̿ ̿)',
	# '' : r'(ง ͠° ͟ل͜ ͡°)ง',
	# '' : r'ಠ_ಠ',
	# '' : r'༼ つ ◕_◕ ༽つ',
	# '' : r'(づ｡◕‿‿◕｡)づ',
	# '' : r'(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧ ✧ﾟ･: *ヽ(◕ヮ◕ヽ)',
	# '' : r'(ง\'̀-\'́)ง',
	# '' : r'(• ε •)',
	# '' : r'(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧',
	# '' : r'(¬‿¬)',
	# '' : r'(◕‿◕✿)',
	# '' : r'(ᵔᴥᵔ)',
	# '' : r'♥‿♥',
	# '' : r'ಠ╭╮ಠ',
	# '' : r'♪~ ᕕ(ᐛ)ᕗ',
	# '' : r'| (• ◡•)| (❍ᴥ❍ʋ)',
	# '' : r'(;´༎ຶД༎ຶ`)',
	# '' : r'◉_◉',
	# '' : r'~(˘▾˘~)',
	# '' : r'ヾ(⌐■_■)ノ♪',
	# '' : r'\ (•◡•) /',
	# '' : r'(~˘▾˘)~',
	# '' : r'( ͡°╭͜ʖ╮͡° )',
	# '' : r'ᕙ(⇀‸↼‶)ᕗ',
	# '' : r'⚆ _ ⚆',
	# '' : r'༼ ºل͟º ༼ ºل͟º ༼ ºل͟º ༽ ºل͟º ༽ ºل͟º ༽',
	# '' : r'༼ʘ̚ل͜ʘ̚༽',
	# '' : r'ᕦ(ò_óˇ)ᕤ',
	# '' : r'(｡◕‿‿◕｡)',
	# '' : r'ಥ_ಥ',
	# '' : r'(｡◕‿◕｡)',
	# '' : r'⌐╦╦═─',
	# '' : r'¯\(°_o)/¯',
	# '' : r'(•ω•)',
	# '' : r'(☞ຈل͜ຈ)☞',
	# '' : r'ヽ༼ຈل͜ຈ༽ﾉ',
	# '' : r'（╯°□°）╯︵( .o.)',
	# '' : r'☜(˚▽˚)☞',
	# '' : r'(ง°ل͜°)ง',
	# '' : r'˙ ͜ʟ˙',
	# '' : r'ಠ⌣ಠ',
	# '' : r'(°ロ°)☝',
	# '' : r'(っ˘ڡ˘ς)',
	# '' : r'ლ(´ڡ`ლ)',
	# '' : r'｡◕‿‿◕｡',
	# '' : r'(─‿‿─)',
	# '' : r'╚(ಠ_ಠ)=┐',
	# '' : r'(¬_¬)',
	# '' : r'( ಠ ͜ʖರೃ)',
	# '' : r'｡◕‿◕｡',
	# '' : r'( ⚆ _ ⚆ )',
	# '' : r'(ʘᗩʘ\')',
	# '' : r'Ƹ̵̡Ӝ̵̨̄Ʒ',
	# '' : r'(ʘ‿ʘ)',
	# '' : r'ლ,ᔑ•ﺪ͟͠•ᔐ.ლ',
	# '' : r'ಠ‿↼',
	# '' : r'ƪ(˘⌣˘)ʃ',
	# '' : r'(´・ω・`)',
	# '' : r'ʘ‿ʘ',
	# '' : r'ಠ_ಥ',
	# '' : r'┬─┬ノ( º _ ºノ)',
	# '' : r'(´・ω・)っ由',
	# '' : r'ಠ~ಠ',
	# '' : r'(&gt;ლ)',
	# '' : r'(° ͡ ͜ ͡ʖ ͡ °)',
	# '' : r'ರ_ರ',
	# '' : r'ಠoಠ',
	# '' : r'(▰˘◡˘▰)',
	# '' : r'(✿´‿`)',
	# '' : r'(ღ˘⌣˘ღ)',
	# '' : r'◔̯◔',
	# '' : r'¬_¬',
	# '' : r'｡゜(｀Д´)゜｡',
	# '' : r'ب_ب',
	# '' : r'◔ ⌣ ◔',
	# '' : r'(ó ì_í)=óò=(ì_í ò)',
	# '' : r'°Д°',
	# '' : r'( ﾟヮﾟ)',
	# '' : r'☼.☼',
	# '' : r'≧☉_☉≦',
	# '' : r'(>人<)',
	# '' : r'٩◔̯◔۶',
	# '' : r'〆(・∀・＠)',
	# '' : r'(･.◤)',
}

KEYS = list(EMOTICONS.keys())

class NotifierBot(ScrapePlugins.IrcGrabber.IrcBot.TestBot):


	def __init__(self, message_queue, runstate, *args, **kwargs):
		self.runState = runstate
		self.message_queue     = message_queue
		self.run      = True
		super(NotifierBot, self).__init__(*args, **kwargs)

		self.connection.execute_every(5, self.alive)

		self.channel = "#madokami"

	def do_auth(self):
		ret = self.connection.privmsg("NickServ", "IDENTIFY %s" % settings.notifierBot["password"])


	def alive(self):
		self.log.info("Alive loop!")
		print("Current channels: ", self.channels)

		if not '#madokami' in self.channels:
			self.connection.join(self.channel)
			self.log.info("Joined channel: %s", self.channel)

		else:
			self.check_message()
		if self.runState.value == 0:
			self.connection.close()

	def on_pubmsg(self, c, e):
		self.log.info("On pubmsg = '%s', '%s'", c, e)
		if e.arguments:
			if len(e.arguments) == 1:
				if len(e.arguments[0]):
					self.handle_argstr(e.arguments[0])

		print((type(e), e))
		print(e.arguments)

	def handle_argstr(self, argstr):

		if argstr == "%s blocked uploads" % settings.notifierBot["name"]:
			self.say_in_channel(self.channel, "Blocked series uploads:")
			for bad in settings.mkSettings['noUpload']:
				self.say_in_channel(self.channel, "	'{}'".format(bad))

		if argstr == ".boolean":
			if random.randrange(2):
				self.say_in_channel(self.channel, "Yes")
			else:
				self.say_in_channel(self.channel, "No")


		first, vals = argstr.split(" ")[0], argstr.split(" ")[1:]
		if first == settings.notifierBot["name"] and vals:
			if any([all([val == key for val in vals]) for key in KEYS]):
				msg = " ".join([EMOTICONS[vals[0]]]*len(vals))
				self.say_in_channel(self.channel, msg)

		if len(first) > 2 and first[0] == ".":
			if first[1:] in EMOTICONS:
				print("Dot command: '%s' (%s)" % (first[1:], first))
				self.say_in_channel(self.channel, EMOTICONS[first[1:]])


	def on_privmsg(self, c, e):
		self.log.info("On Privmsg = '%s', '%s'", c, e)
		print((type(e), e))
		# self.say_command(e, e.arguments[0])
		cmd = e.arguments[0]
		if cmd.startswith(settings.ircBot["pubmsg_prefix"]):
			self.connection.privmsg(self.channel, str(e.arguments[0][len(settings.ircBot["pubmsg_prefix"]):]))
		else:
			super().on_privmsg(c, e)

	def check_message(self):
		while True:
			try:
				message = self.message_queue.get_nowait()
				# self.say_in_channel(self.channel, message)
			except queue.Empty:
				break

	def on_currenttopic(self, c, e):
		if '#madokami' in e.arguments :
			self.log.info("Joined to channel!")


	def welcome_func(self, c, e):
		# Tie periodic calls to on_welcome, so they don't back up while we're connecting.

		# self.reactor.execute_every(2.5,     self.processQueue)
		self.log.info("IRC Interface connected to server %s", self.server_list)

		self.do_auth()





class IrcNotifierInterface(object):
	def __init__(self, message_queue, runstate):
		server = "irc.rizon.net"
		self.msg_queue = message_queue
		self.bot = NotifierBot(self.msg_queue, runstate, settings.notifierBot["name"], settings.notifierBot["rName"], server)

		for event in irc.events.all:
			self.bot.connection.add_global_handler(event, self.event)


	def event(self, c, e):
		print("Event handler!")
		print("Connection: ", c)
		print("Event: ", e)

	def startBot(self):

		self.ircThread = threading.Thread(target=self.bot.startup, daemon=True)
		self.ircThread.start()

	def stopBot(self):
		print("Calling stopBot")
		self.bot.connection.quit()
		self.bot.run = False
		print("StopBot Called")

	def notify(self, message):
		self.msg_queue.put(message)

	@classmethod
	def go(cls, message_queue, runState):

		# signal.signal(signal.SIGINT, signal.SIG_IGN)
		instance = cls(message_queue, runState)
		instance.startBot()
		return instance

def start_notifier():
	queue = multiprocessing.Queue()
	IrcNotifierInterface.go(queue, runStatus.run_state)
	return queue




if __name__ == "__main__":
	import logSetup
	import signal

	print(dir(runStatus))

	queue = multiprocessing.Queue()
	IrcNotifierInterface.go(queue, runStatus.run_state)


	def signal_handler(dummy_signal, dummy_frame):
		if runStatus.run:
			runStatus.run = False
			runStatus.run_state.value = 0
			print("Telling threads to stop")
		else:
			print("Multiple keyboard interrupts. Raising")
			raise KeyboardInterrupt


	signal.signal(signal.SIGINT, signal_handler)
	logSetup.initLogging()






