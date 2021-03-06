#!/usr/bin/env python3
#pyBusstop.py
import sys
import os
import urllib.request as rq
from lxml import etree
from prettytable import PrettyTable
from datetime import datetime
import pickle
import argparse

classtime = "'first col_godzina'"
needhelp = False

class BusSchedule:
	def __init__(self, url="0", name="0", post="0", bus=False, table=True, canary=False):
		self.url=url
		self.name=name
		self.post=post
		self.bus=bus
		self.table=table
		self.canary=canary
		
	def fethUrl(self, post):
		return rq.urlopen(self.url.replace("{}", post))
		
	def takeSchedule(self, classtime):
		poststr = False
		for postint in self.post:
			lefttimes, buses, directions = [], [], []
			if type(self.post)==str:
				poststr=True
				url = self.fethUrl(self.post)
			else:
				url = self.fethUrl(postint)
			recoveryon = etree.XMLParser(recover=True)
			tree = etree.parse(url, recoveryon)
			root = tree.getroot()
			try:
				self.name = root.xpath('//span[@id="przyst_nazwa"]/em')[0].text
			except AttributeError:
				print ("Connection error")
				return 2
			except:
				return 2
			for lefttime in root.xpath('//td[@class={}]'.format(classtime)):
				lefttime = lefttime.text
				if len(lefttime) == 4:
					lefttimes.append("0"+lefttime)
				else:
					lefttimes.append(lefttime)
			bustable = root.xpath('//table[@id="stop_table"]/tbody/tr/td/a')
			for a, bus in enumerate(bustable):
				if len(bus.text.strip('\t\n')) == 0:
					bustable.pop(a)
			for a, bus in enumerate(bustable):
				if a % 2 == 0:
					buses.append(bus.text.lstrip('\t\n'))
				else:
					directions.append(bus.text)
			busdir = zip(buses, directions)
			backup = list(zip(lefttimes, busdir))
			
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
				print("Rozkład jazdy komunikacji miejskiej z przystanku {} o numerze: {:^10} \n \
					  \nFiltr dla lini: {:>5}\n".format(self.name, post, ", ".join(self.bus)))
			else: 
				print("Rozkład jazdy komunikacji miejskiej z przystanku {} o numerze: {:^10}\n" \
					  .format(self.name, post))
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
			if self.canary:
				canarylist = self.fetchCanary() 
				table = PrettyTable(['Godzina', 'Linia', 'Kierunek', 'Kanar'])
				for key in sortedkeys:
					for bus in timetable[key]:
						if self.bus == False:
							if bus[0] in canarylist:
								table.add_row([key, bus[0], bus[1], 'X'])
							else:
								table.add_row([key, bus[0], bus[1], ''])
						else:
							for argbus in self.bus:
								if argbus in bus:
									if bus[0] in canarylist:
										table.add_row([key, bus[0], bus[1], 'X'])
									else:
										table.add_row([key, bus[0], bus[1], ''])
			else:
				table = PrettyTable(['Godzina', 'Linia', 'Kierunek'])
				for key in sortedkeys:
					for bus in timetable[key]:
						if self.bus == False:
							table.add_row([key, bus[0], bus[1]])
						else:
							for argbus in self.bus:
								if argbus in bus:
									table.add_row([key, bus[0], bus[1]])
			print(table)
		else:
			if self.canary:
				canarylist = self.fetchCanary() 
				for key in sortedkeys:
					for bus in timetable[key]:
						if self.bus == False:
							if bus[0] in canarylist:
								print(" {:5} - {:^5} - {:5} - {:5}".format(key, bus[0], bus[1], 'X'))
							else:
								print(" {:5} - {:^5} - {:5}".format(key, bus[0], bus[1]))
						else:
							for argbus in self.bus:
								if argbus in bus:
									if bus[0] in canarylist:
										print(" {:5} - {:^5} - {:5} - {:5}".format(key, bus[0], bus[1], 'X'))
									else:
										print(" {:5} - {:^5} - {:5}".format(key, bus[0], bus[1]))
			else:
				for key in sortedkeys:
					for bus in timetable[key]:
						if self.bus == False:
							print(" {:5} - {:^5} - {:5}".format(key, bus[0], bus[1]))
						else:
							for argbus in self.bus:
								if argbus in bus:
									print(" {:5} - {:^5} - {:5}".format(key, bus[0], bus[1]))
		return 0
		
	def takeBusList(self):
		try:
			buslist = rq.urlopen("http://komunikacja.iwroclaw.pl/Rozklady_jazdy_MPK_we_Wroclawiu")
		except rq.URLError:
			print ("Connection error")
			return 2
		except:
			return 2
		recoveryon = etree.XMLParser(recover=True)
		tree = etree.parse(buslist, recoveryon)
		root = tree.getroot()
		buses, trams = [], []
	
		for bus in root.xpath('//ul[@class="autobusy_list"]/li/a'):
			buses.append(bus.text)
		for tram in root.xpath('//ul[@class="tramwaje_list"]/li/a'):
			trams.append(tram.text)
		return {"buses":buses, "trams":trams}
		
	def setBus(self, *bus):
		buslist = self.takeBusList()
		if buslist == 2:
			return 2
		if not bus:
			print("Dostępne linie:\n\n\tTramwajowe:\n{}\n\n\tAutobusowe:\n{}" \
				.format(', '.join(buslist["trams"]), ', '.join(buslist["buses"])))
			return 2
		if not bus == "printschedule": 
			bus=[x.upper() for x in bus]
			self.bus=bus
		for argbus in self.bus:
			if argbus in buslist["buses"]:
				self.bustype="bus"
			elif argbus in buslist["trams"]:
				self.bustype="tram"
			else:
				print("Nie ma takiej lini!")
				print("Dostępne linie:\n\n\tTramwajowe:\n{}\n\n\tAutobusowe:\n{}" \
					.format(', '.join(buslist["trams"]), ', '.join(buslist["buses"])))
				return 2
		return 0
		
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
		
	def setPost(self, *post):
		if not post:
			post="printposts"
		elif len(post) > 1:
			return 1
		else:
			post=post[0]
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
					return 2
			else:
				self.post=post
		except:
			postlist = self.listPostsNames()
			if len(post) == 1:
				post = post.upper()
				print("Lista przystanków zaczynających się na literę '{}':".format(post))
				for idx, postel in enumerate(postlist): 
					postel[0].lstrip('\t\n')
					if postel[0][0].upper()==post:
						print("{:5} - {:>40}".format(idx, postel[0]))
						if idx % 25 == 24:
							print("kliknij 'Q' aby wyjść, lub dowolny klawisz, aby pokazać resztę dostępnych przystanków.")
							if sys.platform.startswith("win"):
								import msvcrt
								x = msvcrt.getch()
							else:
								import getch
								x = getch.getch()
							if x.upper() == "Q":
								break
			elif not post == "printposts":
				post = post.upper()
				for idx, postel in enumerate(postlist): 
					if post in str(postel).upper():
						print("{:5} - {:>40}".format(idx, postel[0]))
			elif post == "printposts":
				for idx, postel in enumerate(postlist):
					print("{:5} - {:>40}".format(idx, postel[0]))
					if idx % 25 == 24:
						print("kliknij 'Q' aby wyjść, lub dowolny klawisz, aby pokazać resztę dostępnych przystanków.")
						if sys.platform.startswith("win"):
							import msvcrt
							x = msvcrt.getch()
						else:
							import getch
							x = getch.getch()
						if x.upper() == "Q":
							break
			return 2
		return 0
			
	def setTable(self, *params):
		if params:
			return 1
		if self.table:
			self.table = False
		else:
			self.table = True
		return 0
	
	def setCanary(self, *params):
		if params:
			return 1
		if self.canary:
			self.canary = False
		else:
			self.canary = True
		return 0
	
	def fetchCanary(self):
		day = datetime.now().day
		canary = rq.urlopen("http://www.wroclaw.pl/kontrola-biletow-mpk-wroclaw-gdzie-sa-dzisiaj-kontrole")
		recoveryon = etree.XMLParser(recover=True)
		tree = etree.parse(canary, recoveryon)
		root = tree.getroot()
		canares = []
		for canary in root.xpath('//div[@class="article_content"]/h3'):
			if str(day) in canary.text:
				canary=canary.xpath('following::p[1]')
				canary=next(iter(canary or []), None)
				if canary == None:
					canares.append('Brak Danych')
				else:
					canary=canary.text.split(" - ")[1]
					canares=canary.split(", ")
				break
		return canares
	
def setFav(*post):
	favPosts = {
	"z pracy" : "12149",
	"tramwajowa do Rynku" : "11454",
	"tramwajowa do FAT" : "11453",
	"136 do Pracy" : "11553",
	"z kruczej do JP2" : "11536",
	"z kruczej do Arkad" : "11522"
	}
	if not post:
		with open('favorites.dat', 'rb') as f:
			favPosts = pickle.load(f)
		table = PrettyTable(['LP', 'Opis przystanku', 'Numer przystanku'])
		for idx, key in enumerate(sorted(favPosts.keys())):
			table.add_row([idx+1, key, favPosts[key]])
		print(table)
		return 2
	if post[0].upper() == "RESET" and len(post) == 1:
		with open("favorites.dat", "wb") as f:
			pickle.dump(favPosts, f, pickle.HIGHEST_PROTOCOL)
		return 2
	if post[0].upper() == "ADD" and len(post) == 3 and \
		len(post[2]) == 5 and post[2].isdigit():
		with open('favorites.dat', 'rb') as f:
			favPosts = pickle.load(f)
		if post[1] in favPosts:
			print("Już istnieje przystanek '{}'.".format(post[1]))
			return 2
		elif post[2] in favPosts.values():
			print("Już istnieje przystanek o id: '{}'.".format(post[2]))
			return 2
		favPosts[post[1]]=post[2]
		with open("favorites.dat", "wb") as f:
			pickle.dump(favPosts, f, pickle.HIGHEST_PROTOCOL)
		return 2
	if post[0].upper() in ("REM", "REMOVE", "DEL", "DELETE"):
		with open('favorites.dat', 'rb') as f:
			favPosts = pickle.load(f)
		for arg in post[1:]:
			if not arg.isdigit():
				return 1
		removed = False
		postSorted=sorted(post[1:])
		for arg in postSorted[::-1]:
			for idx, key in enumerate(sorted(favPosts.keys())):
				if idx+1 == int(arg):
					del favPosts[key]
					removed = True
					break
				if arg == favPosts[key]:
					del favPosts[key]
					removed = True
					break
		if removed:
			with open("favorites.dat", "wb") as f:
				pickle.dump(favPosts, f, pickle.HIGHEST_PROTOCOL)
				return 2
		else:
			return 2
	else:
		return 1

if __name__ == "__main__":
	if not os.path.isfile("favorites.dat"):
		setFav("reset")
	with open('favorites.dat', 'rb') as f:
		favPosts = pickle.load(f)
	anotherPost = False
	www = BusSchedule(url="http://komunikacja.iwroclaw.pl/Rozklad_jazdy_slupek_{}_Wroclaw", table=True)
	arguments = argparse.ArgumentParser(description='Znajdź swój autobus.')
	arguments.add_argument('-b', '--bus', nargs='*', help='Wywołane bez parametra - pokazuje wszystkie linie; Wywołane z parametrem - filtrowanie lini')
	arguments.add_argument('-p', '--post', nargs='*', help='Wywołane bez parametra - pokazuje wszystkie przystanki; Wywołane z parametrem - filtrowanie przystanków')
	arguments.add_argument('-f', '--favorite', nargs='*', help='Wywołane bez parametra - pokazuje liste ulubionyh przystanków; Wywołane z parametrem ADD - dodawanie przystanku; Wywołane z parametrem REM/REMOVE/DEL/DELETE - usuwanie przystanku; Wywołane z parametrem RESET - resetowanie listy do domyślnej')
	arguments.add_argument('-nt', '--notable', action='store_true', help='Wyłącza widok tabelki')
	arguments.add_argument('-c', '--cannar', action='store_true', help='Sprawdź czy jest zapowiedziana kontrola biletów')
	
	args = vars(arguments.parse_args())
	if args['notable']:
		www.setTable()
	if args['cannar']:
		www.setCanary()
	if args['bus'] != None:
		RC = www.setBus(*args['bus'])
		if RC == 2:
			sys.exit(0)
	if args['post'] != None:
		RC = www.setPost(*args['post'])
		anotherPost = True
		if RC == 2:
			sys.exit(0)
	if args['favorite'] != None:
		RC = setFav(*args['favorite'])
		anotherPost = True
		if RC == 2:
			sys.exit(0)
	if anotherPost:
		www.takeSchedule("'first col_godzina'")
	else:
		for post in sorted(favPosts.keys()):
			print("Komunikacja {}:".format(post))
			www.post=favPosts[post]
			www.takeSchedule("'first col_godzina'")
