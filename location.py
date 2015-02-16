
import urllib
import json


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


