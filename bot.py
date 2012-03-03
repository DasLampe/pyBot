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

import xmpp, time, re, mechanize, threading, os
DEBUG	= False

def write_log(msg):
	if DEBUG == True:
		print("["+time.asctime()+"]"+msg+"\n")
	file		= open(os.path.dirname(os.path.realpath(__file__))+"/log.dat", "a")
	file.write("["+time.asctime()+"]"+msg+"\n")
	file.close()

class pytalForum:
	def __init__(self):
		self.save_file				= os.path.dirname(os.path.realpath(__file__))+"/pytalForum.dat"
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
	
def commandBot(bot,botname):
	write_log("Start commandBot")
	cache = []
	room  = "pybottest@conference.jabber.pytal.net"
	
	#if user come online or go offline
	def presenceCB(conn,msg):
		write_log("User activity changed")
		prs_type=msg.getType()
		jid=msg.getFrom()
		if jid.getResource() not in cache:
			write_log("User isn't in cache, add him")
			cache.append(jid.getResource())
		
		if prs_type == "unavailable":
			write_log("User leave the room")
			if jid.getResource() in cache:
				cache.remove(jid.getResource())

	#grab messages and do something
	def messageCB(bot,msg):
		text = msg.getBody()
		user = msg.getFrom()
		
		if user is not botname and re.match(r'Werner', str(text), re.IGNORECASE):
			write_log("Speaks to Werner")
			if re.search(r'online', str(text), re.IGNORECASE) != None:
				write_log("Show online User")
				online_msg	= "Zur Zeit sind "
				for user in cache:
					online_msg += user+", "
				online_msg += " online"
				bot.send(xmpp.protocol.Message(to=room, body=online_msg, typ="groupchat"))
			else:
				write_log("no action for bot. Say it")
				bot.send(xmpp.protocol.Message(to=room, body="Ja was gibt's", typ="groupchat"))

	write_log("register handler")
	bot.RegisterHandler('message', messageCB)
	bot.RegisterHandler('presence', presenceCB)
	
	while(1 == 1):
		bot.Process(1)

def main():
	write_log("Start Bot")
	jid = xmpp.protocol.JID('webmasterandre@jabber.pytal.net')
	pwd = '1Pf@df!nd3r'
	room = 'pybottest@conference.jabber.pytal.net'
	botname	= "pyBot Test"
	
	write_log("Start Jabber Bot")
	
	bot	= xmpp.Client(jid.getDomain(), debug=[])
	if bot.connect() == "":
		write_log("Connection failed! Wait 5 min and try again.")
		time.sleep(300)
		main()
		exit(0)

	if bot.auth(jid.getNode(), pwd) == None:
		write_log("Auth fail!")
		exit(0)
	
	write_log("Join room")
	join	= xmpp.Presence(to='%s/%s' % (room, botname))
	join.setTag('x', namespace=xmpp.NS_MUC).setTagData('password', "")
	join.getTag('x').addChild('history',{'maxchars':'0','maxstanzas':'0'})
	bot.send(join)
	
	bot.Process(1)
	
	write_log("Jabber Bot successfuly starts")

	forum   = pytalForum()
	
	botcommand	= threading.Thread(target=commandBot, args=(bot,botname,))
	botcommand.start()
	
	write_log("End Init. Go into while")
	while(1==1):
		try:
			posts   = forum.find_new_thread()
			if posts is not False:
				write_log("Send Message!")
				write_log(posts)
				bot.send(xmpp.protocol.Message(to=room, body=posts, typ='groupchat'))
				write_log("Message sends")
			else:
				write_log("Keine neuen Beiträge!")
			write_log("Done ... wait 5 min and do again")
			time.sleep(300)
		except:
			write_log("Error - Except!")
			main()
	bot.disconnect()
	write_log("Close Bot")

main()
