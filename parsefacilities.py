#!/usr/bin/python

import csv
import sqlite3
import os
import datetime
from collections import namedtuple

Facility = namedtuple('Facility', ['ID', 'Name', 'LastUpdate', 'Created', 'Address'] )

def getColStrings( tr ):
	return tuple( col.string for col in tr.find_all("td") )

def getFacilities(datasource):
	facilities = csv.DictReader(datasource)

	for place in facilities:
		details = {
			'Type': place['DESCRIPTION'],
			'City': place['CITY'],
			'Address': place['ADDR'],
			'ID': place['FACILITYID'],
			'Name': place['BUSINESS_NAME']
		}
		yield details

def restaurantRecognizer( s ):
	return  'Restaurant' in s or 'Food Take Out' in s

def addToDB(cursor, details):
	if restaurantRecognizer( details['Type'] ) \
		and details['City'] in ('WATERLOO', 'KITCHENER', 'ST.+JACOBS'):

		cursor.execute("SELECT * FROM facilities WHERE id=?;", (details['ID'],))

		if cursor.fetchone() is None:
			print str.format("{Name}: {Address}, {City}", **details )
			cursor.execute('''
			INSERT INTO facilities (id, name, lastupdate, creation, address)
				VALUES ( ?, ?, ?, ?, ? );''', 
				(details['ID'], 
				details['Name'], 
				datetime.datetime.now(),
				datetime.datetime.now(),
				details['Address']))
			
		else:
			print "Updating time on {}".format( details['Name'])
			cursor.execute( "UPDATE facilities SET lastupdate = ? WHERE id = ?;", 
				( datetime.datetime.now(), 
					details['ID']) )
    
	
def createDB( cursor):
	cursor.execute("CREATE TABLE facilities (id, name, lastupdate, creation );")
	cursor.execute("CREATE TABLE settings (key, value);")
	cursor.execute("INSERT INTO settings VALUES ('version', 1);")


def tryUpgradeDB( cursor ):

	try:
		cursor.execute("SELECT value from settings WHERE key = 'version';");
		row = cursor.fetchone()
		version = row[0]

		
	except sqlite3.OperationalError as ex:
		version = 0

	if version == 0:
		print ("Original database detected; upgrading")
		cursor.execute("CREATE TABLE settings (key, value);")
		cursor.execute("INSERT INTO settings VALUES ('version', 1);")
		cursor.execute("ALTER TABLE facilities ADD COLUMN address;")
	elif version == 1:
		cursor.execute("""f
CREATE TABLE facilities_new AS 
	SELECT id, name, lastseen as lastupdate, firstseen as creation, NULL as address FROM facilities;""")
		cursor.execute("DROP TABLE facilities;")
		cursor.execute("ALTER TABLE facilities_new RENAME TO facilities;")
		cursor.execute("UPDATE settings SET value = 2 WHERE key = 'version';")



def getRecent( cursor, ndays = 7 ):
	cursor.execute("SELECT * FROM facilities WHERE creation > date('now','-{ndays} days')".format( ndays=float(ndays) ))
	for row in cursor.fetchall():
		yield Facility( *row )


def main():
	import argparse
	parser = argparse.ArgumentParser()
	parser.add_argument("--update", action="store_true", 
		help="Update the database with new restaurants from CSV")
	parser.add_argument("--datasource", type=argparse.FileType('rt'), 
		default=open('testdata/Facilities_OpenData.csv', 'rt'), 
		help="File to obtain data from (default: testdata/Facilities_OpenData.csv")
	parser.add_argument("--getrecent", metavar="N", action="store", type=int, 
		help="Return informaiton on the N restaurants discovered in the last N days")
	args = parser.parse_args()
	# Track whether we need to create the DB or not.
	noDB = not os.path.exists( 'restaurants.db' )
	db = sqlite3.connect( 'restaurants.db' )
	cursor = db.cursor()
	
	if noDB:
		createDB( cursor )
		db.commit()
	else:
		tryUpgradeDB( cursor )

	if args.update:
		for facility in getFacilities(args.datasource):
			addToDB( cursor, facility )
	db.commit()

	if args.getrecent:
		print list( getRecent( cursor, args.getrecent ) )
	db.close()
		
if __name__ == '__main__':
	main()
