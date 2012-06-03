# -*- coding: utf-8 -*-
import xmpp, re

class commandBot:
	def __init__(self, bot, botname, room):
		#write_log("Start commandBot")
		self.cache		= []
		self.bot		= bot
		self.botname	= botname
		self.room		= room
		
		#write_log("register handler")
		self.bot.RegisterHandler('message', self.messageCB)
		self.bot.RegisterHandler('presence', self.presenceCB)
		
		while(1 == 1):
			self.bot.Process(1)
	
	#if user come online or go offline
	def presenceCB(self, conn,msg):
		#write_log("User activity changed")
		prs_type=msg.getType()
		jid=msg.getFrom()
		if jid.getResource() not in self.cache:
			#write_log("User isn't in cache, add him")
			self.cache.append(jid.getResource())
		
		if prs_type == "unavailable":
			#write_log("User leave the room")
			if jid.getResource() in self.cache:
				self.cache.remove(jid.getResource())

	#grab messages and do something
	def messageCB(self, bot,msg):
		text = msg.getBody()
		user = msg.getFrom()
		
		if text != None:
			if user.getResource() != self.botname and re.match(u'Werner', text, re.IGNORECASE):
				if re.search(u'online', text, re.IGNORECASE) != None:
					online_msg	= "Zur Zeit sind "
					for user in self.cache:
						if user == self.botname:
							user = "Ich (der coole Bot)"
						online_msg += user+", "
					online_msg += " online"
					bot.send(xmpp.protocol.Message(to=self.room, body=online_msg, typ="groupchat"))
				elif re.search(u'Keks', text, re.IGNORECASE) != None:
					username = user.getResource()
					bot.send(xmpp.protocol.Message(to=self.room, body="/me gibt " + username + " einen Keks", typ="groupchat"))
					bot.send(xmpp.protocol.Message(to=self.room, body=("Bitte, " + username + "!"), typ="groupchat"))
				else:
					bot.send(xmpp.protocol.Message(to=self.room, body="Ja was gibt's", typ="groupchat"))
