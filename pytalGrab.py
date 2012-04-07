import xmpp, mechanize, re, os, time

class pytalGrab:
	def __init__(self, bot, room):
		self.save_file				= os.path.dirname(os.path.realpath(__file__))+"/pytalForum.dat"
		self.br						= mechanize.Browser()
		self.br.addheaders			= [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/8.0')]
		self.newest_post_username	= ""
		self.newest_post_timestamp	= 0
		
		self.bot					= bot
		self.room					= room
		
		self.run()

	def find_new_thread(self):
		try:
			self.br.open("http://pytal.de", timeout=30.0)
		except:
			return False
		data                = self.load_data()
		self.old_thread_url = str(data[1])
		self.last_post      = int(data[0])
		i                   = 1
		result              = ""

		for link in self.br.links(url_regex="topic"):
			self.newest_post(link)

			if link.url == self.old_thread_url:
				if self.newest_post_timestamp > self.last_post:
					if i == 1:
						self.save_data(self.newest_post_timestamp, link.url)
					result = str(result) + str('Neuer Post in '+link.text+' (von '+self.newest_post_username+') - http://www.pytal.de'+link.url+'\n')
				return result
			else:
				if i == 1:
					self.save_data(self.newest_post_timestamp, link.url)
				result = str(result) + str('Neuer Post in '+link.text+' (von '+self.newest_post_username+') - http://www.pytal.de'+link.url+'\n')
			i = i +1

		if result == "":
			return False
		else:
			return result
	
	def newest_post(self, link):
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
		return data.split("\n")
	
	def run(self):
		while 1:
			try:
				posts	= self.find_new_thread()
				if posts is not False:
					self.bot.send(xmpp.protocol.Message(to=self.room, body=posts, typ='groupchat'))
				time.sleep(300)
			except:
				continue
