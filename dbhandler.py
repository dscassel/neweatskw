import sqlite3
from collections import namedtuple

Facility = namedtuple('Facility', ['ID', 'Name', 'LastUpdate', 'Created', 'Address', 'City'] )
	
def createDB( cursor):
	cursor.execute("""
		CREATE TABLE facilities (
			id PRIMARY KEY ON CONFLICT REPLACE, 
			name, lastupdate, creation, address, city 
		);
		""")
	cursor.execute("CREATE TABLE settings (key PRIMARY KEY ON CONFLICT REPLACE, value);")
	cursor.execute("CREATE TABLE locations (city, address, latitude, longitude );")
	cursor.execute("CREATE TABLE queue (facilities_id);")
	cursor.execute("INSERT INTO settings VALUES ('version', 3);")


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
		    SELECT id, name, lastseen as lastupdate, 
			firstseen as creation, NULL as address, 
			NULL as city FROM facilities;""")
		cursor.execute("DROP TABLE facilities;")
		cursor.execute("ALTER TABLE facilities_new RENAME TO facilities;")
	if version < 2:
		cursor.execute("CREATE TABLE locations (city, address, latitude, longitude );")

	if version < 3:
		cursor.execute("""
		CREATE TABLE facilities_new (
		    id PRIMARY KEY ON CONFLICT REPLACE, 
		    name, lastupdate, creation, address, city);
		""")
		cursor.execute("INSERT INTO facilities_new SELECT id, name, lastupdate, creation FROM facilities;")
		cursor.execute("DROP TABLE facilities;")
		cursor.execute("ALTER TABLE facilities_new RENAME TO facilities;")

		cursor.execute("CREATE TABLE settings_new (key PRIMARY KEY ON CONFLICT REPLACE, value);")
		cursor.execute("INSERT INTO settings_new SELECT key, value FROM settings;")
		cursor.execute("DROP TABLE settings;")
		cursor.execute("ALTER TABLE settings_new RENAME TO settings;")
		
		cursor.execute("CREATE TABLE queue (facilities_id);")

		cursor.execute("UPDATE settings SET value = 3 WHERE key = 'version';")


def storeKey( cursor, key, secret ):
	cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('twitter.access_key', ?);", [key])
	cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('twitter.access_secret', ?);", [secret])

def getKey( cursor ):
	cursor.execute("SELECT value FROM settings WHERE key = 'twitter.access_key';")
	keyRow = cursor.fetchone()

	cursor.execute("SELECT value FROM settings WHERE key = 'twitter.access_secret';")
	secretRow = cursor.fetchone();

	return ( keyRow[0], secretRow[0] )

def getRecent( cursor, ndays = 7 ):
	cursor.execute("SELECT * FROM facilities WHERE creation > date('now','-{ndays} days')".format( ndays=float(ndays) ))
	for row in cursor.fetchall():
		yield Facility( *row )

def getTopOfQueue( cursor ):
	
	cursor.execute("SELECT facilities.* FROM queue, facilities WHERE facilities.ID = queue.facilities_id;") 

	row = cursor.fetchone()
	return Facility(*row)

def deleteFromQueue( cursor, facility ):
	cursor.execute("DELETE FROM facilities WHERE facilities_id = ?;", [facility.ID])

