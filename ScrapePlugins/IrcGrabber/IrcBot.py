

import os
import struct
import sys

import shlex

import ssl
import logging
import irc.buffer
import irc.client
import irc.bot
import irc.strings

from bs4 import UnicodeDammit
import re
from irc.client import ip_numstr_to_quad, ip_quad_to_numstr


# Horrible hackyclass that I'm using to monkey-patch the line decoder. Unfortunately,
# short of subclassing ALL THE THINGS, I can't very easily override the decoder.
# As such, we just stick a patched decoder into the class at runtime.
class TolerantDecodingLineBuffer(object):

	line_sep_exp = re.compile(b'\r?\n')

	def __init__(self):
		self.buffer = b''

	def feed(self, inBytes):
		self.buffer += inBytes


	def __iter__(self):
		return self.lines()

	def __len__(self):
		return len(self.buffer)

	encodings = ['utf-8', "iso-8859-1", "latin-1"]
	errors = 'strict'

	def lines(self):
		lines = self.line_sep_exp.split(self.buffer)
		# save the last, unfinished, possibly empty line
		self.buffer = lines.pop()

		for line in lines:
			ret = UnicodeDammit(line, self.encodings).unicode_markup
			if not ret:
				raise UnicodeDecodeError("Could not decode '%s'" % line)
			yield ret

class TestBot(irc.bot.SingleServerIRCBot):
	def __init__(self, nickname, realname, server, port=9999):
		ssl_factory = irc.connection.Factory(wrapper=ssl.wrap_socket)

		# Horrible monkey-patch the ServerConnection instance so we can fix some encoding issues.
		print("Old buffer class", irc.client.ServerConnection.buffer_class)
		irc.client.ServerConnection.buffer_class = TolerantDecodingLineBuffer
		print("New buffer class", irc.client.ServerConnection.buffer_class)

		irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, realname, connect_factory=ssl_factory)

		self.log = logging.getLogger("Main.Manga.IRC")
		self.received_bytes = 0

		self.welcomed = False

	def on_ctcp(self, c, e):
		"""Default handler for ctcp events.

		Replies to VERSION and PING requests and relays DCC requests
		to the on_dccchat method.
		"""

		print("On CTCP", e.arguments)
		nick = e.source.nick
		if e.arguments[0] == "VERSION":
			c.ctcp_reply(nick, "VERSION " + self.get_version())
		elif e.arguments[0] == "PING":
			if len(e.arguments) > 1:
				c.ctcp_reply(nick, "PING " + e.arguments[1])

		elif e.arguments[0] == "DCC":

			# Filenames are a giant PITA. Basically, we try to split the
			# CTCP command. If we get more then 5 items, the name must
			# have spaces, so we then try `shlex.split`. This works
			# around the issue that filenames without spaces
			# can have single quotation marks.
			args = e.arguments[1].strip().split()
			if len(args) != 5:
				args = shlex.split(e.arguments[1])
			if args[0] != "SEND":
				self.log.warning("Not DCC Send. Wat? '%s'", e.arguments)
				return

			self.log.info("Received DCC send command - '%s'", e)

			if hasattr(self, "get_filehandle"):
				self.file = self.get_filehandle(args[1])
				if not self.file:
					self.log.error("Could not get filehandle. XDCC is being dropped.")
					raise irc.client.DCCConnectionError
			else:
				self.filename = os.path.basename(args[1])

				self.log.info("Saving to '%s'", self.filename)

				if os.path.exists(self.filename):
					self.log.error("A file named '%s'", self.filename,)
					self.log.error("already exists. Refusing to save it.")
					# self.connection.quit()
				else:
					self.log.info("Saving item to '%s'", self.filename)
				self.file = open(self.filename, "wb")

			if hasattr(self, "xdcc_receive_start"):
				status = self.xdcc_receive_start()
				if not status:
					return

			peeraddress = irc.client.ip_numstr_to_quad(args[2])
			peerport = int(args[3])

			self.dcc = self.dcc_connect(peeraddress, peerport, "raw")

	def on_dccmsg(self, connection, event):
		data = event.arguments[0]
		self.file.write(data)
		self.received_bytes = self.received_bytes + len(data)
		self.dcc.send_bytes(struct.pack("!I", self.received_bytes))

	def on_dcc_disconnect(self, connection, event):
		self.file.close()
		self.log.info("Received file - %d bytes." % (self.received_bytes))
		if hasattr(self, "xdcc_receive_finish"):
			self.xdcc_receive_finish()

	def on_nicknameinuse(self, connection, event):
		connection.nick(connection.get_nickname() + "_")

	def on_welcome(self, c, e):
		self.log.info("On Welcome.")
		self.welcomed = True
		if hasattr(self, "welcome_func"):
			self.welcome_func()



	def on_privmsg(self, c, e):
		self.log.info("On Privmsg = '%s', '%s'", c, e)
		self.say_command(e, e.arguments[0])

	def on_pubmsg(self, c, e):

		a = e.arguments[0].split(":", 1)
		self.log.info("Pubmessage = %s", e.arguments)
		if len(a) > 1 and irc.strings.lower(a[0]) == irc.strings.lower(self.connection.get_nickname()):
			self.log.info("Executing command '%s'", a[1])
			self.say_command(e, a[1].strip())
		return

	def on_dccchat(self, c, e):
		self.log.info("On DccChat")
		if len(e.arguments) != 2:
			return
		args = e.arguments[1].split()
		if len(args) == 4:
			try:
				address = ip_numstr_to_quad(args[2])
				port = int(args[3])
			except ValueError:
				return
			self.dcc_connect(address, port)


	def say_command(self, e, cmd, ):
		nick = e.source.nick
		c = self.connection

		# if cmd.startswith(settings.ircBot["pubmsg_prefix"]):
		# 	c.privmsg(e.channel, str(cmd[len(settings.ircBot["pubmsg_prefix"]):]))
		if cmd == "dcc":
			dcc = self.dcc_listen()
			self.log.info("Starting DCC - Command: '%s'", "CHAT chat %s %d" % (ip_quad_to_numstr(dcc.localaddress), dcc.localport))
			c.ctcp("DCC", nick, "CHAT chat %s %d" % (ip_quad_to_numstr(dcc.localaddress), dcc.localport))
		else:
			self.log.error("Unknown command = '%s'" % cmd)


	def startup(self):
		self.log.info("Bot entering select loop")
		self.start()


def main():
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

if __name__ == "__main__":
	main()
