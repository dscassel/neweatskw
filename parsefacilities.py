#!/usr/bin/python

from bs4 import BeautifulSoup
import sqlite3
import os
import datetime

def getColStrings( tr ):
	return tuple( col.string for col in tr.find_all("td") )

def getFacilities():
	facilities = BeautifulSoup(open("testdata/doc.kml"), "xml")

	for place in facilities.find_all("Placemark"):
		description = BeautifulSoup(''.join(place.description.contents))
		table = description.table.table
		
		rows = table.find_all("tr")
		details = dict( getColStrings( row ) for row in rows)
		yield details


def addToDB(cursor, details):

	if details['CategoryStyle'] in ('Restaurant', 'Food Take Out') \
		and details['SiteCity'] in ('WATERLOO', 'KITCHENER', 'ST.+JACOBS'):

		cursor.execute("SELECT * FROM facilities WHERE id=?;", (details['FacilityMasterID'],))

		if cursor.fetchone() is None:
			print str.format("{FacilityName}: {SiteStreet}, {SiteCity}", **details )
			cursor.execute('''
			INSERT INTO facilities (id, name, lastupdate, creation, firstseen, lastseen)
				VALUES ( ?, ?, ?, ?, ?, ? );''', 
				(details['FacilityMasterID'], 
				details['FacilityName'], 
				details['LastUpdateDateTime'],
				details['CreationDateTime'],
				datetime.datetime.now(),
				datetime.datetime.now()))
			
		else:
			print "Updating time on {}".format( details['FacilityName'])
			cursor.execute( "UPDATE facilities SET lastseen = ? WHERE id = ?;", 
				( datetime.datetime.now(), 
					details['FacilityMasterID']) )
    
	
def createDB( cursor):
	cursor.execute("CREATE TABLE facilities (id, name, lastupdate, creation, firstseen, lastseen);")
	cursor.execute("CREATE TABLE settings (key, value);")
	cursor.execute("INSERT INTO settings VALUES ('version', 1);")


def tryUpgradeDB( cursor ):
	try:
		cursor.execute("SELECT * from settings;");
	except sqlite3.OperationalError as ex:
		print ("Original database detected; upgrading")
		cursor.execute("CREATE TABLE settings (key, value);")
		cursor.execute("INSERT INTO settings VALUES ('version', 1);")		
		cursor.execute("ALTER TABLE facilities ADD COLUMN firstseen;")
		cursor.execute("ALTER TABLE facilities ADD COLUMN lastseen;")

def main():
	# Track whether we need to create the DB or not.
	noDB = not os.path.exists( 'restaurants.db' )
	db = sqlite3.connect( 'restaurants.db' )
	cursor = db.cursor()
	
	if noDB:
		createDB( cursor )
		db.commit()
	else:
		tryUpgradeDB( cursor )

	for facility in getFacilities():
		addToDB( cursor, facility )
	db.commit()
	db.close()
		
if __name__ == '__main__':
	main()
