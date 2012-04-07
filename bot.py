# -*- coding: utf-8 -*-

import xmpp, time, threading, sys, commandBot, pytalGrab
DEBUG	= False #Set True for Log

def write_log(msg):
	if DEBUG == True:
		print("["+time.asctime()+"]"+msg+"\n")
	file		= open("log.dat", "a")
	file.write("["+time.asctime()+"]"+msg+"\n")
	file.close()

def main():
	def sendMessage(bot,room,message):
		bot.send(xmpp.Message(room, body=message, typ='groupchat'))

	global done
	write_log("Start Bot")
	jid = xmpp.protocol.JID(sys.argv[1]+"@jabber.pytal.net") #Your jid
	pwd = sys.argv[2] #Your Password
	room = sys.argv[3]+'@conference.jabber.pytal.net'
	botname	= sys.argv[4] #Displayname for bot
	
	if len(sys.argv) > 4:
		DEBUG = True
	
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
	
	write_log("Jabber Bot successfuly started")
	
	botcommand	= threading.Thread(target=commandBot.commandBot, args=(bot,botname,room,))
	botcommand.setDaemon(True)
	botcommand.start()
	
	pytal	= threading.Thread(target=pytalGrab.pytalGrab, args=(bot,room))
	pytal.setDaemon(True)
	pytal.start()
	
	
	write_log("End Init. Go into while")

	while 1:
		#user_input = str(raw_input())
		#if user_input == "quit":
		#		sendMessage(bot, room, "DasLampe hat gesagt, dass ich jetzt gehen muss. Bis dann!")
		#		break
		pass
	exit()

main()
