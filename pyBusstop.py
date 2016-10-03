#pyBusstop.py
import sys
import urllib.request as rq
from lxml import etree
from prettytable import PrettyTable
from datetime import datetime

classtime = "'first col_godzina'"
classnumber = "'linia_autobus_bez_ikony'"
needhelp = False

class BusSchedule:
	def __init__(self, url="0", post="0", bus="0", table=True):
		self.url=url
		self.post=post
		self.bus=bus
		self.table=table
		
	def fethUrl(self, post):
		return rq.urlopen(self.url.replace("{}", post))
		
	def takeSchedule(self, classtime, classnumber):
		poststr = False
		for postint in self.post:
			if type(self.post)==str:
				poststr=True
				url = self.fethUrl(self.post)
			else:
				url = self.fethUrl(postint)
			recoveryon = etree.XMLParser(recover=True)
			tree = etree.parse(url, recoveryon)
			root = tree.getroot()
			
			lefttimes, buses = [], []
			
			for lefttime in root.xpath('//td[@class={}]'.format(classtime)):
				lefttime = lefttime.text
				if len(lefttime) == 4:
					lefttimes.append("0"+lefttime)
				else:
					lefttimes.append(lefttime)
			for bus in root.xpath('//td[@class={}]/a'.format(classnumber)):
				buses.append(bus.text.lstrip('\t\n'))
			backup = list(zip(lefttimes, buses))

			#budowanie słownika na podstawie listy
			timetable = {k:[] for k in lefttimes}
			for i in backup:
				value = timetable[i[0]]
				value.append(i[1])
				timetable[i[0]]=value

			#czyszczenie powtórzeń w słowniku
			for key in timetable.keys():
				timetable[key]=sorted(list(set(timetable[key])))
			if poststr:
				self.printSchedule(timetable, self.post)
				break
			self.printSchedule(timetable, postint)
		return 0
	
	def headPrint(func):
		def wrap(self, timetable, post):
			if self.bus is not False:
				print("Rozkład jazdy komunikacji miejskiej z przystanku o numerze: {:^10} \n \
					  \nFiltr dla lini: {:>5}\n".format(post, self.bus))
			else: 
				print("Rozkład jazdy komunikacji miejskiej z przystanku o numerze: {:^10}\n" \
					  .format(post))
			return func(self, timetable, post)
		return wrap
		
	@headPrint
	def printSchedule(self, timetable, post):
		sortedkeys = sorted(timetable)
		currenthour = str(datetime.now().hour)
		if len(sortedkeys)>0:
			if currenthour <= sortedkeys[0]:
				pass
			else:
				for key in sortedkeys:
					if key[0:2] < currenthour:
						sortedkeys = sortedkeys[1:]
						sortedkeys.append(key)
		if self.table:
			table = PrettyTable(['Godzina', 'Linia'])
			for key in sortedkeys:
				if self.bus in timetable[key] or self.bus == False:
					table.add_row([key, ', '.join(timetable[key])])
			print(table)
		else:
			for key in sortedkeys:
				if self.bus in timetable[key] or self.bus == False:
					print(" {:10} - {:>10}".format(key, ', '.join(timetable[key])))
		return 0
		
	def	takeBusList(self):
		buslist = rq.urlopen("http://komunikacja.iwroclaw.pl/Rozklady_jazdy_MPK_we_Wroclawiu")
		recoveryon = etree.XMLParser(recover=True)
		tree = etree.parse(buslist, recoveryon)
		root = tree.getroot()
		buses, trams = [], []
	
		for bus in root.xpath('//ul[@class="autobusy_list"]/li/a'):
			buses.append(bus.text)
		for tram in root.xpath('//ul[@class="tramwaje_list"]/li/a'):
			trams.append(tram.text)
		return {"buses":buses, "trams":trams}
		
	def setBus(self, bus="printschedule"):
		if not bus == "printschedule": 
			self.bus=bus.upper()
		buslist = self.takeBusList()
		if self.bus in buslist["buses"]:
			self.bustype="bus"
			return 0
		elif self.bus in buslist["trams"]:
			self.bustype="tram"
			return 0
		else:
			if not bus == "printschedule":
				print("Nie ma takiej lini!")
			print("Dostępne linie:\n\n\tTramwajowe:\n{}\n\n\tAutobusowe:\n{}" \
				  .format(', '.join(buslist["trams"]), ', '.join(buslist["buses"])))
			return 2
		
	def listPostsNames(self):
		postlist = rq.urlopen("http://www.wroclaw.pl/wszystkie-przystanki-wydruk")
		recoveryon = etree.XMLParser(recover=True)
		tree = etree.parse(postlist, recoveryon)
		root = tree.getroot()
		posts = []
		for post in root.xpath('//ul[@class="filtered-lines-list"]/li/a'):
			posts.append([post.text, post.attrib["href"]])
		return posts
		
	def fethPost(self, url):
		urllist = rq.urlopen(url)
		recoveryon = etree.XMLParser(recover=True)
		tree = etree.parse(urllist, recoveryon)
		root = tree.getroot()
		postids = []
		for postid in root.xpath('//tbody/tr/td'):
			try:
				intpostid = int(postid.text)
				postids.append(postid.text)
			except:
				pass
		return sorted(list(set(postids)))
		
	def setPost(self, post="printposts"):
		try:
			intpost = int(post)
			if len(post)>=1 and len(post)<=3:
				noid = True
				postlist = self.listPostsNames()
				for idx, postel in enumerate(postlist): 
					if idx == intpost:
						posts = self.fethPost("http://www.wroclaw.pl"+postel[1]+"-wydruk")
						self.post = posts
						noid = False
						break
				if noid:
					print("Nie ma przystanku o danym ID.")
			else:
				self.post=post	
		except:
			postlist = self.listPostsNames()
			if not post == "printposts":
				post = post.upper()
				for idx, postel in enumerate(postlist): 
					if post in postel.upper():
						print("{:5} - {:>40}".format(idx, postel[0]))
			elif post == "printposts":	
				for idx, postel in enumerate(postlist): 
					print("{:5} - {:>40}".format(idx, postel[0]))
			elif post:
				pass
		return 0
			
	def setTable(self):
		if self.table:
			self.table = False
		else: 
			self.table = True
		return 0
		
def printHelp():
	print("help")
	return 0


if __name__ == "__main__":
	www = BusSchedule("http://komunikacja.iwroclaw.pl/Rozklad_jazdy_slupek_{}_Wroclaw", "11524", False)
	# wwww = open('plik.html', "rb")
	for idx, arg in enumerate(sys.argv):
		if idx==0:
			pass
		else:
			options = {
			"-b" : www.setBus,
			"--bus" : www.setBus,
			"-p" : www.setPost,
			"--post" : www.setPost,
			"-nt" : www.setTable,
			"--notable" : www.setTable
			}
			if "-h" in sys.argv or "--help" in sys.argv:
				needhelp = True
				break 
			if arg in options.keys():
				try:
					if sys.argv[idx+1] in options.keys():
						raise
					RC = options[arg](sys.argv[idx+1])
				except: 
					try:
						RC = options[arg]()
					except:
						needhelp = True
						break
				if RC == 1:
					needhelp = True
					break
				elif RC == 2:
					sys.exit(0)
			elif sys.argv[idx-1] in options.keys():
				if sys.argv[idx-1] == "-nt" or \
				   sys.argv[idx-1] == "--notable":
					needhelp = True
					break
				pass
			else:
				needhelp = True
				break
	if needhelp:
		printHelp()
	else:
		www.takeSchedule("'first col_godzina'","'col_linie_bez_ikony'")
