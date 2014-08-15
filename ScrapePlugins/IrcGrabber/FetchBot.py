

import ScrapePlugins.IrcGrabber.IrcBot
import sys
import threading
import settings

class FetcherBot(ScrapePlugins.IrcGrabber.IrcBot.TestBot):
	pass


class IrcRetreivalInterface(object):
	def __init__(self):
		server = "irc.irchighway.net"
		self.bot = FetcherBot(settings.ircBot["name"], server)

	def startBot(self):




def main():
	import sys
	print("Sys argv length = ", len(sys.argv))
	if len(sys.argv) != 4:
		print("Usage: testbot <server[:port]> <channel> <nickname>")
		sys.exit(1)

	s = sys.argv[1].split(":", 1)
	server = s[0]
	if len(s) == 2:
		try:
			port = int(s[1])
		except ValueError:
			print("Error: Erroneous port.")
			sys.exit(1)
	else:
		port = 9999
	channel = sys.argv[2]
	nickname = sys.argv[3]

	bot = TestBot(channel, nickname, server, port)
	print("Bot created. Connecting")
	bot.start()
