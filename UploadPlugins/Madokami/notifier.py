

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


class NotifierBot(ScrapePlugins.IrcGrabber.IrcBot.TestBot):


	def __init__(self, message_queue, runstate, *args, **kwargs):
		self.runState = runstate
		self.message_queue     = message_queue
		self.run      = True
		super(NotifierBot, self).__init__(*args, **kwargs)

		self.connection.execute_every(5, self.alive)
		self.joined = False

		self.channel = "#madokami"

	def do_auth(self):
		ret = self.connection.privmsg("NickServ", "IDENTIFY %s" % settings.notifierBot["password"])


	def alive(self):
		self.log.info("Alive loop!")

		if not self.joined:
			self.connection.join(self.channel)
			self.log.info("Joined channel: %s", self.channel)

		else:
			self.check_message()
		if self.runState.value == 0:
			self.connection.close()

	def on_privmsg(self, c, e):
		self.log.info("On Privmsg = '%s', '%s'", c, e)
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
				self.say_in_channel(self.channel, message)
			except queue.Empty:
				break

	def on_currenttopic(self, c, e):
		if '#madokami' in e.arguments :
			self.joined = True
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






