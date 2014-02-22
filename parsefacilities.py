#!/usr/bin/python

from bs4 import BeautifulSoup

facilities = BeautifulSoup(open("testdata/doc.kml"), "xml")


for place in facilities.find_all("Placemark"):
    description = BeautifulSoup(''.join(place.description.contents))
    table = description.table.table
    details = dict()

    for row in table.find_all("tr"):
	cells = [x.string for x in row.find_all("td")]
	details[cells[0]] = cells[1]

    print details["CategoryStyle"]


		
