#!/usr/bin/python

from bs4 import BeautifulSoup
import sqlite3

db = sqlite3.connect('restaurants.db')

cursor = db.cursor()

facilities = BeautifulSoup(open("testdata/doc.kml"), "xml")


for place in facilities.find_all("Placemark"):
    description = BeautifulSoup(''.join(place.description.contents))
    table = description.table.table
    details = dict()

    for row in table.find_all("tr"):
	cells = [x.string for x in row.find_all("td")]
	details[cells[0]] = cells[1]

    if details['CategoryStyle'] in ('Restaurant', 'Food Take Out') \
	and details['SiteCity'] in ('WATERLOO', 'KITCHENER', 'ST.+JACOBS'):

	cursor.execute("SELECT * FROM facilities WHERE id=?;", (details['FacilityMasterID'],))

	if cursor.fetchone() is None:
	    print str.format("{}: {}, {}", details['FacilityName'], details['SiteStreet'], details['SiteCity'])

    
    cursor.execute('''
	INSERT OR REPLACE INTO facilities (id, name, lastupdate, creation)
	    VALUES ( ?, ?, ?, ? );''', 
	(details['FacilityMasterID'], 
	details['FacilityName'], 
	details['LastUpdateDateTime'],
	details['CreationDateTime']))

db.commit()
db.close()
			
	
	

		
