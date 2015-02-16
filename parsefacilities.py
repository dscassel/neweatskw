#!/usr/bin/python

import csv
import sqlite3
import datetime
import dbhandler
import location



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
	return  'Restaurant' in s or 'Food Take Out' in s or "Food, General - Bakery - Production" in s

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
    

def main():
	import argparse
	parser = argparse.ArgumentParser()
	parser.add_argument("--update", action="store_true", 
		help="Update the database with new restaurants from CSV")
	parser.add_argument("--datasource", type=argparse.FileType('rt'), 
		default=open('testdata/Facilities_OpenData.csv', 'rt'), 
		help="File to obtain data from (default: testdata/Facilities_OpenData.csv")
	parser.add_argument("--database", type=dbhandler.dbArgType,
		default='restaurants.db',
		help="SQLite database file for storing updates")
	parser.add_argument("--getrecent", metavar="N", action="store", type=int, 
		help="Return informaiton on the N restaurants discovered in the last N days")
	parser.add_argument("--enqueue", action="store_true",
		help="For --getrecent, store the recent additions in the database.")
	
	args = parser.parse_args()
	
	db = args.database
	cursor = db.cursor()

	if args.update:
		for facility in getFacilities(args.datasource):
			addToDB( cursor, facility )
	db.commit()

	if args.getrecent:
		for result in dbhandler.getRecent( cursor, args.getrecent ):
			print "{name}: {address}, {city} ({loc})".format( 
				name=result.Name, address=result.Address, city=result.City, 
				loc=location.getLocation(cursor, result.City, result.Address) )

			if args.enqueue:
				cursor.execute( "INSERT INTO queue (facilities_id) VALUES ( ? );", [(result.ID)] )
			
	db.commit()
	db.close()

if __name__ == '__main__':
	main()
