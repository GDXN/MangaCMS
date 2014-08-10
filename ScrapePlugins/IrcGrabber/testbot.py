#! /usr/bin/env python
#
# Example program using irc.bot.
#
# Joel Rosdahl <joel@rosdahl.net>

"""A simple example bot.

This is an example bot that uses the SingleServerIRCBot class from
irc.bot.  The bot enters a channel and listens for commands in
private messages and channel traffic.  Commands in channel messages
are given by prefixing the text by the bot name followed by a colon.
It also responds to DCC CHAT invitations and echos data sent in such
sessions.

The known commands are:

	stats -- Prints some channel information.

	disconnect -- Disconnect the bot.  The bot will try to reconnect
				  after 60 seconds.

	die -- Let the bot cease to exist.

	dcc -- Let the bot invite you to a DCC CHAT connection.
"""

import os
import struct
import sys

import ssl

import irc.logging
import irc.bot
import irc.strings

from irc.client import ip_numstr_to_quad, ip_quad_to_numstr

class TestBot(irc.bot.SingleServerIRCBot):
	def __init__(self, channel, nickname, server, port=9999):
		ssl_factory = irc.connection.Factory(wrapper=ssl.wrap_socket)
		irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname, connect_factory=ssl_factory)
		self.channel = channel

		self.received_bytes = 0

	def on_ctcp(self, c, e):
		"""Default handler for ctcp events.

		Replies to VERSION and PING requests and relays DCC requests
		to the on_dccchat method.
		"""
		nick = e.source.nick
		if e.arguments[0] == "VERSION":
			c.ctcp_reply(nick, "VERSION " + self.get_version())
		elif e.arguments[0] == "PING":
			if len(e.arguments) > 1:
				c.ctcp_reply(nick, "PING " + e.arguments[1])

		elif e.arguments[0] == "DCC":

			args = event.arguments[1].split()
			if args[0] != "SEND":
				return
			self.filename = os.path.basename(args[1])
			if os.path.exists(self.filename):
				print("A file named", self.filename,)
				print("already exists. Refusing to save it.")
				self.connection.quit()
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
		print("Received file %s (%d bytes)." % (self.filename,
												self.received_bytes))
		self.connection.quit()

	def on_nicknameinuse(self, connection, event):
		connection.nick(connection.get_nickname() + "_")

	def on_welcome(self, c, e):
		print("On Welcome. Joining", self.channel)
		c.join(self.channel)
		print("Joined ", self.channel)


	def on_privmsg(self, c, e):
		print("On Privmsg")
		self.do_command(e, e.arguments[0])

	def on_pubmsg(self, c, e):
		print("On Pubmsg")
		a = e.arguments[0].split(":", 1)
		print("Name = ", a)
		if len(a) > 1 and irc.strings.lower(a[0]) == irc.strings.lower(self.connection.get_nickname()):
			print("Executing command", a[1])
			self.say_command(e, a[1].strip())
		return

	def on_dccmsg(self, c, e):
		print("On Dccmsg")
		c.privmsg("You said: " + e.arguments[0])

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

	def do_command(self, e, cmd):
		nick = e.source.nick
		c = self.connection

		if cmd == "disconnect":
			self.disconnect()
		elif cmd == "die":
			self.die()
		elif cmd == "stats":
			for chname, chobj in self.channels.items():
				c.notice(nick, "--- Channel statistics ---")
				c.notice(nick, "Channel: " + chname)
				users = chobj.users()
				# users.sort()
				c.notice(nick, "Users: " + ", ".join(users))
				opers = chobj.opers()
				# opers.sort()
				c.notice(nick, "Opers: " + ", ".join(opers))
				voiced = chobj.voiced()
				# voiced.sort()
				c.notice(nick, "Voiced: " + ", ".join(voiced))
		elif cmd == "dcc":
			dcc = self.dcc_listen()
			c.ctcp("DCC", nick, "CHAT chat %s %d" % (
				ip_quad_to_numstr(dcc.localaddress),
				dcc.localport))
		else:
			c.notice(nick, "Not understood: " + cmd)

	def say_command(self, e, cmd):
		nick = e.source.nick
		c = self.connection

		if cmd == "disconnect":
			self.disconnect()
		elif cmd == "die":
			self.die()
		elif cmd == "stats":
			for chname, chobj in self.channels.items():
				c.notice(self.channel, "--- Channel statistics ---")
				c.notice(self.channel, "Channel: " + chname)
				users = chobj.users()
				# users.sort()
				c.notice(self.channel, "Users: " + ", ".join(users))
				opers = chobj.opers()
				# opers.sort()
				c.notice(self.channel, "Opers: " + ", ".join(opers))
				voiced = chobj.voiced()
				# voiced.sort()
				c.notice(self.channel, "Voiced: " + ", ".join(voiced))
		elif cmd == "dcc":
			dcc = self.dcc_listen()
			c.ctcp("DCC", nick, "CHAT chat %s %d" % (
				ip_quad_to_numstr(dcc.localaddress),
				dcc.localport))
		else:
			c.notice(self.channel, "Not understood: " + cmd)


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
