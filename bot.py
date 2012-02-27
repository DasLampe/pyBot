# -*- coding: utf-8 -*-

##   Copyright (C) 2011 Matthias Matousek <matou@taunusstein.net>
##
##   This program is free software; you can redistribute it and/or modify
##   it under the terms of the GNU General Public License as published by
##   the Free Software Foundation; either version 2, or (at your option)
##   any later version.
##
##   This program is distributed in the hope that it will be useful,
##   but WITHOUT ANY WARRANTY; without even the implied warranty of
##   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##   GNU General Public License for more details.

import xmpp, time, re, logging, mechanize
from threading import Thread
from random import randint

DEBUG	= True

def write_log(msg):
	if DEBUG == True:
		file		= open("/home/andre/pytalForumNotification/log.dat", "a")
		file.write("["+time.asctime()+"]"+msg+"\n")
		file.close()

class Mucbot(Thread):
	def __init__(self, jid, pwd, room, botname='', roompwd='', greeting=[], 
			quotes=[], minwait=-1, maxwait=-1, reactions={}, delay=3, 
			rcv_handler=[]):
		'''initalize bot and let it join the room'''
		Thread.__init__(self)
		
		if botname == '':
			botname = jid.getNode()
			
		# the jid of the bot
		self.jid = jid
		# the room to join
		self.room = room
		# the nick to appear with
		self.botname = botname
		# the password for the room
		self.roompwd = roompwd
		# quotes to tell periodical
		self.quotes = quotes
		# minimum and maximum time to wait before quoting something
		self.minwait = minwait
		self.maxwait = maxwait
		# a dictionary containing reactions. the keys have to be 
		# regular expressions pattern as strings and the value a list of 
		# reactions from which one will be picked randomly. it's sufficient to
		# consider the lower case since every message body will be made lower
		# case before parsingiit.
		self.reactions = reactions
		# seconds to wait before replying
		self.delay = delay
		# a list of handlers that will be executed when a message is received
		self.rcv_handler = rcv_handler
		# a list of possible greetings when the bot enters a room
		self.greeting = greeting
		
		# compile the patterns
		for key in self.reactions.keys():
			self.reactions[re.compile(key)] = self.reactions.pop(key)

		self.client = xmpp.Client(jid.getDomain(), debug=[])
		self.client.connect()
		self.client.RegisterHandler('message', self.msg_rcv)
		self.client.RegisterHandler('presence', self.pres_rcv)
		self.client.auth(jid.getNode(), pwd, resource=jid.getResource())
		
		self.join_room()

	def join_room(self):
		p = xmpp.Presence(to='%s/%s' % (self.room, self.botname))
		p.setTag('x', namespace=xmpp.NS_MUC).setTagData('password', self.roompwd)
		p.getTag('x').addChild('history', {'maxchars':'0', 'maxstanzas':'0'})
		self.client.send(p)

		self.jointime = time.time()

		logging.info('%s joined %s' % (self.botname, self.room))

	def msg_rcv(self, sess, msg):
		'''will be executed when a message arrives'''

		logging.debug('received message')

		# ignore messages that come from this bot
		sender = str(msg.getFrom())
		if len(sender.split('/')) > 1:
			sender = sender.split('/')[1]
		if sender.lower().find(self.botname) >= 0:
			return


		# first execute all given handlers
		for handler in self.rcv_handler:
			handler(self, msg.getFrom(), msg.getBody())

		self.react(msg.getBody())

	def react(self, msg):
		'''react to a message by searching for all patterns and replying with
		the matching answer'''
		logging.debug(msg)
		msg = msg.lower()
		time.sleep(self.delay)
		for pattern in self.reactions.keys():
			if pattern.search(msg):
				self.say(self.reactions[pattern][randint(0,len(self.reactions[pattern])-1)])
				return

	def pres_rcv(self, sess, pres):
		# ignore messages that come from this bot
		sender = str(pres.getFrom())
		if len(sender.split('/')) > 1:
			sender = sender.split('/')[1]
		if sender.lower().find(self.botname) >= 0:
			return

	def say(self, msg):
		'''send the given message to the room'''
		m = xmpp.Message(to=self.room, body=msg, typ='groupchat')
		self.client.send(m)

	def getClient(self):
		return self.client	

	def processing(self):
		while True:
			self.client.Process(1)

	def run(self):
		processor = Thread()
		processor.run = self.processing
		processor.start()
		time.sleep(self.delay)
		if len(self.greeting) > 0:
			self.say(self.greeting[randint(0, len(self.greeting)-1)])
		if self.minwait==-1 or self.maxwait==-1:
			return
		while True:
			r = randint(self.minwait, self.maxwait)
			logging.info('waiting %d seconds before next quote' % r)
			time.sleep(r)
			self.say(self.quotes[randint(0,len(self.quotes)-1)])

class pytalForum:
	def __init__(self):
		self.save_file				= "/home/andre/pytalForumNotification/pytalForum.dat"
		self.br						= mechanize.Browser()
		self.br.addheaders			= [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/8.0')]
		self.newest_post_username	= ""
		self.newest_post_timestamp	= 0

	def find_new_thread(self):
		write_log("Borwse to pytal.de")
		try:
			self.br.open("http://pytal.de", timeout=30.0)
		except:
			write_log("Timeout")
			return False
		write_log("Load data")
		data                = self.load_data()
		self.old_thread_url = str(data[1])
		self.last_post      = int(data[0])
		i                   = 1
		result              = ""

		write_log("Find links")
		for link in self.br.links(url_regex="topic"):
			self.newest_post(link)

			if link.url == self.old_thread_url:
				write_log("First link same the old")
				if self.newest_post_timestamp > self.last_post:
					write_log("New posts in old topic")
					if i == 1:
						write_log("Save data")
						self.save_data(self.newest_post_timestamp, link.url)
					result = str(result) + str('Neuer Post in '+link.text+' (von '+self.newest_post_username+') - http://www.pytal.de'+link.url+'\n')
					write_log("Return Link to old topic, with new post")
				return result
			else:
				if i == 1:
					write_log("Save data form new topic")
					self.save_data(self.newest_post_timestamp, link.url)
				result = str(result) + str('Neuer Post in '+link.text+' (von '+self.newest_post_username+') - http://www.pytal.de'+link.url+'\n')
			i = i +1

		if result == "":
			write_log("No to return")
			return False
		else:
			write_log("Return links to new topics/posts")
			return result
	
	def newest_post(self, link):
		write_log("Search newest post")
		self.br.follow_link(link)
		output = self.br.response().read()
		posts = re.findall(r'<span class="date">(.*)</span>', output)
		
		post_info       = posts[-1]
		post_info       = post_info.replace(' Uhr', '')
		post_info       = post_info.split(' - ')
		post_time       = post_info[1].split(':')
		post_date       = post_info[0].split('.')
		post_timestamp  = (int('20'+post_date[2]), int(post_date[1]), int(post_date[0]), int(post_time[0]), int(post_time[1]), int(post_time[2]),0,0,0)

		posts			= re.findall(r'<a class="boausr".*>(.*)</a>', output)
		post_username	= posts[-1]

		write_log("Find newest post")
		self.newest_post_timestamp	= int(time.mktime(post_timestamp))
		self.newest_post_username	= post_username

	def save_data(self, timestamp, link):
		save_file       = open(self.save_file, "w")
		save_file.write(str(timestamp)+"\n")
		save_file.write(str(link))
		save_file.close()

	def load_data(self):
		save_file       = open(self.save_file, "r")
		data            = save_file.read()
		write_log("Data loaded")
		return data.split("\n")

def main():
	write_log("Start Bot")
	jid = xmpp.JID('webmasterandre@jabber.pytal.net')
	pwd = '1Pf@df!nd3r'
	room = 'pytal@conference.jabber.pytal.net'
	examplebot = Mucbot(jid, pwd, room, 'pyBot Werner')

	forum   = pytalForum()

	while(1==1):
		try:
			posts   = forum.find_new_thread()
			if posts is not False:
				write_log("Send Message!")
				write_log(posts)
				examplebot.say(posts)
				write_log("Message sends")
			else:
				write_log("Keine neuen Beiträge!")
			time.sleep(300)
		except:
			write_log("Error - Except!")
			main()
	write_log("Close Bot")

main()
