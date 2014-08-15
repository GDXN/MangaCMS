

import os
import struct
import sys

import ssl

import irc.logging
import irc.bot
import irc.strings

from irc.client import ip_numstr_to_quad, ip_quad_to_numstr

class TestBot(irc.bot.SingleServerIRCBot):
	def __init__(self, nickname, server, port=9999):
		ssl_factory = irc.connection.Factory(wrapper=ssl.wrap_socket)
		irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname, connect_factory=ssl_factory)


		self.received_bytes = 0

		self.welcomed = False

	def on_ctcp(self, c, e):
		"""Default handler for ctcp events.

		Replies to VERSION and PING requests and relays DCC requests
		to the on_dccchat method.
		"""

		print("On CTCP", c, e, e.arguments)
		nick = e.source.nick
		if e.arguments[0] == "VERSION":
			c.ctcp_reply(nick, "VERSION " + self.get_version())
		elif e.arguments[0] == "PING":
			if len(e.arguments) > 1:
				c.ctcp_reply(nick, "PING " + e.arguments[1])

		elif e.arguments[0] == "DCC":

			args = e.arguments[1].split()
			if args[0] != "SEND":
				print("Not DCC Send. Wat? '%s'" % e.arguments)
				return
			self.filename = os.path.basename(args[1])

			print("Saving to '%s'" % self.filename)

			if os.path.exists(self.filename):
				print("A file named", self.filename,)
				print("already exists. Refusing to save it.")
				# self.connection.quit()
			else:
				print("Saving item to ", self.filename)
			self.file = open(self.filename, "wb")
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
		print("Received file %s (%d bytes)." % (self.filename, self.received_bytes))

	def on_nicknameinuse(self, connection, event):
		connection.nick(connection.get_nickname() + "_")

	def on_welcome(self, c, e):
		print("On Welcome.")
		self.welcomed = True
		# c.join(self.channel)
		# print("Joined ", self.channel)


	def on_privmsg(self, c, e):
		print("On Privmsg", c, e)
		self.say_command(e, e.arguments[0])

	def on_pubmsg(self, c, e):

		a = e.arguments[0].split(":", 1)
		print("Name = ", a)
		if len(a) > 1 and irc.strings.lower(a[0]) == irc.strings.lower(self.connection.get_nickname()):
			print("Executing command", a[1])
			self.say_command(e, a[1].strip())
		return

	def on_dccchat(self, c, e):
		print("On DccChat")
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

		if cmd.startswith("say "):
			c.privmsg(self.channel, str(cmd[4:]))
		elif cmd == "dcc":
			dcc = self.dcc_listen()
			print("Starting DCC - Command: '%s'", "CHAT chat %s %d" % (ip_quad_to_numstr(dcc.localaddress), dcc.localport))
			c.ctcp("DCC", nick, "CHAT chat %s %d" % (ip_quad_to_numstr(dcc.localaddress), dcc.localport))
		else:
			print("Unknown command = '%s'" % cmd)

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

if __name__ == "__main__":
	main()
