#!/usr/bin/python

import csv
import sqlite3
import datetime
import dbhandler


def getFacilities(datasource):
	facilities = csv.DictReader(datasource)

	for place in facilities:
		details = {
			'Type': place['SUBCATEGORY'].decode('latin-1'),
			'City': place['CITY'].upper().decode('latin-1'),
			'Address': place['ADDR'].decode('latin-1'),
			'ID': place['FACILITYID'].upper().decode('latin-1'),
			'Name': place['BUSINESS_NAME'].decode('latin-1')
		}
		
		yield details

def restaurantRecognizer( s ):
	return  'Restaurant' in s or 'Food Take Out' in s or 'Baked Goods - Retail' in s or 'Ice Cream / Yogurt Vendor' in s

def cityRecognizer( c ):
	return c in ('WATERLOO', 'KITCHENER', 'ST.+JACOBS')

def addToDB(cursor, details, date):
	if restaurantRecognizer( details['Type'] ) and cityRecognizer( details['City'] ):
		cursor.execute("SELECT * FROM facilities WHERE id=?;", (details['ID'],))

		if cursor.fetchone() is None:
			print u"{Name}: {Address}, {City}".format(**details)
			cursor.execute('''
			INSERT INTO facilities (id, name, lastupdate, creation, address, city)
				VALUES ( ?, ?, ?, ?, ?, ? );''', 
				(details['ID'], 
				details['Name'], 
				date,
				date,
				details['Address'],
				details['City']))
			
		else:
			print "Updating time on {}".format( details['Name'])
			cursor.execute( "UPDATE facilities SET lastupdate = ? WHERE id = ?;", 
				( date, details['ID']) )

def valid_date(s):
    try:
        return datetime.datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)    

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
	parser.add_argument("--date", type=valid_date, 
		help="The date of the update - format YYYY-MM-DD") 
                    
	
	args = parser.parse_args()
	
	db = args.database
	cursor = db.cursor()

	if args.date:
		date = datetime.date(args.date.year, args.date.month, args.date.day)
	else:
		date = datetime.date.today()

	if args.update:
		for facility in getFacilities(args.datasource):
			addToDB( cursor, facility, date )
	db.commit()

	if args.getrecent:
		for result in dbhandler.getRecent( cursor, args.getrecent ):
			print "{name}: {address}, {city}".format( 
				name=result.Name, address=result.Address, city=result.City)

			if args.enqueue:
				cursor.execute( "INSERT INTO queue (facilities_id) VALUES ( ? );", [(result.ID)] )
			
	db.commit()
	db.close()

if __name__ == '__main__':
	main()
