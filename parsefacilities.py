#!/usr/bin/python

import csv
import sqlite3
import os
import datetime
from collections import namedtuple
import urllib
import json

import tweeteats


Facility = namedtuple('Facility', ['ID', 'Name', 'LastUpdate', 'Created', 'Address', 'City'] )

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
			INSERT INTO facilities (id, name, lastupdate, creation, address, city)
				VALUES ( ?, ?, ?, ?, ?, ? );''', 
				(details['ID'], 
				details['Name'], 
				datetime.datetime.now(),
				datetime.datetime.now(),
				details['Address'],
				details['City']))
			
		else:
			print "Updating time on {}".format( details['Name'])
			cursor.execute( "UPDATE facilities SET lastupdate = ? WHERE id = ?;", 
				( datetime.datetime.now(), 
					details['ID']) )
    
	
def createDB( cursor):
	cursor.execute("CREATE TABLE facilities (id, name, lastupdate, creation, address, city );")
	cursor.execute("CREATE TABLE settings (key, value);")
	cursor.execute("CREATE TABLE locations (city, address, latitude, longitude );")
	cursor.execute("INSERT INTO settings VALUES ('version', 2);")


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
		cursor.execute("INSERT INTO settings VALUES ('version', 2);")
		cursor.execute("ALTER TABLE facilities ADD COLUMN address;")
		cursor.execute("ALTER TABLE facilities ADD COLUMN city;")
	elif version == 1:
		cursor.execute("""
CREATE TABLE facilities_new AS 
	SELECT id, name, lastseen as lastupdate, firstseen as creation, NULL as address, NULL as city FROM facilities;""")
		cursor.execute("DROP TABLE facilities;")
		cursor.execute("ALTER TABLE facilities_new RENAME TO facilities;")
		cursor.execute("UPDATE settings SET value = 2 WHERE key = 'version';")
	if version < 2:
		cursor.execute("CREATE TABLE locations (city, address, latitude, longitude );")


def getRecent( cursor, ndays = 7 ):
	cursor.execute("SELECT * FROM facilities WHERE creation > date('now','-{ndays} days')".format( ndays=float(ndays) ))
	for row in cursor.fetchall():
		yield Facility( *row )

def getLocation( cursor, address, city ):
	cursor.execute("SELECT latitude, longitude FROM locations WHERE city = ? AND address = ?", (city, address) )
	row = cursor.fetchone()
	if row is None:
		# We don't have a location for this address; look one up via Google
		fulladdress = "{address}, {city}, Ontario, Canada".format( address=address, city=city)
		rawdata = urllib.urlopen( 
			"http://maps.googleapis.com/maps/api/geocode/json?address={}&sensor=false".format( 
				urllib.quote( fulladdress ) ) ).read()
		data = json.loads( rawdata )
		location = data['results'][0]['geometry']['location']
		lat, lng = location['lat'], location['lng']
		cursor.execute("INSERT INTO locations (city, address, latitude, longitude) VALUES (?,?,?,?);",
			(city, address, lat, lng))
		return lat, lng
	return row

def storeKey( cursor, key, secret ):
	cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('twitter.access_key', ?);", [key])
	cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('twitter.access_secret', ?);", [secret])


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
	parser.add_argument("--authorize", action="store_true",
		help="Authorize this script to update your Twitter account.")
	
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

	if args.authorize:
		(key, secret) = tweeteats.authorize()
		storeKey(cursor, key, secret)

	if args.getrecent:
		for result in getRecent( cursor, args.getrecent ):
			print "{name}: {address}, {city} ({loc})".format( 
				name=result.Name, address=result.Address, city=result.City, 
				loc=getLocation(cursor, result.City, result.Address) )
	db.commit()
	db.close()
		
if __name__ == '__main__':
	main()
