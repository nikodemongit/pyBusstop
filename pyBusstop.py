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
	def __init__(self, url=0, post=0, bus=0, table=False):
		self.url=url
		self.post=post
		self.bus=bus
		self.table=table
		
	def fethUrl(self):
		return rq.urlopen(self.url.replace("{}", str(self.post)))
		
	def takeSchedule(self, url, classtime, classnumber):
		recoveryon = etree.XMLParser(recover=True)
		tree = etree.parse(url, recoveryon)
		root = tree.getroot()
		
		lefttimes, buses = [], []
		
		for lefttime in root.xpath('//td[@class={}]'.format(classtime)):
			lefttimes.append(lefttime.text)
	
		for bus in root.xpath('//a[@class={}]'.format(classnumber)):
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
			timetable[key]=list(set(timetable[key]))
		
		return timetable
	
	def headPrint(func):
		def wrap(self, timetable):
			if self.bus is not False:
				print("Rozkład jazdy komunikacji miejskiej z przystanku o numerze: {:^10} \n \
					  \nFiltr dla lini: {:>5}\n".format(self.post, self.bus))
			else: 
				print("Rozkład jazdy komunikacji miejskiej z przystanku o numerze: {:^10}\n" \
					  .format(self.post))
			return func(self, timetable)
		return wrap
		
	@headPrint
	def printSchedule(self, timetable):
		sortedkeys = sorted(timetable)
		currenthour = str(datetime.now().hour)
		currenthour = "15"
		if len(sortedkeys)>0:
			if currenthour <= sortedkeys[0]:
				pass
			else:
				for key in sortedkeys:
					if key[0:2] < currenthour:
						sortedkeys = sortedkeys[1:]
						sortedkeys.append(key)
		
		if self.table:
			table = PrettyTable(['Godzina', 'Linie'])
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
		
	def setBus(self, bus):
		self.bus=bus.upper()
		buslist = self.takeBusList()
		if self.bus in buslist["buses"]:
			self.bustype="bus"
			return 0
		elif self.bus in buslist["trams"]:
			self.bustuype="tram"
			return 0
		else:
			print("Nie ma takiej lini!")
			sys.exit()
		
	def setPost(self, post):
		try:
			post=int(post)
		except:
			return 1
		self.post=post
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
	www = BusSchedule("http://komunikacja.iwroclaw.pl/Rozklad_jazdy_slupek_{}_Wroclaw", 11524, False, True)
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
					if options[arg](sys.argv[idx+1]) == 1:
						needhelp = True
						break
				except: 
					try:
						if options[arg]() == 1:
							needhelp = True
							break
					except:
						needhelp = True
						break
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
		wwww = www.fethUrl()
		d = www.takeSchedule(wwww,"'first col_godzina'","'linia_autobus_bez_ikony'")
		www.printSchedule(d)
		
		
	
