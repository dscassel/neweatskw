#!/usr/bin/python

import tweepy
import config_twitter
import sqlite3
import dbhandler
import location
import os
import re

auth = tweepy.OAuthHandler(config_twitter.API_CONSUMER_KEY, config_twitter.API_SECRET)
#auth = tweepy.auth.BasicAuthHandler(config_twitter.USER, config_twitter.PASSWORD, secure=True)

def authorize():
	redirect_url = auth.get_authorization_url()

	print 'Go here: ' + redirect_url
	verifier = raw_input('Verifier')
    
	auth.get_access_token(verifier)

	return (auth.access_token.key, auth.access_token.secret)

def initialize(key, secret):
	auth.set_access_token(key, secret)

def tweet( message, latitude, longitude ):
	api = tweepy.API(auth)
	api.update_status(message, lat=latitude, long=longitude)

def tweetTopOfQueue(cursor):
	newRestaurant = dbhandler.getTopOfQueue(cursor)

	message = getMessage(newRestaurant)
	loc = location.getLocation(cursor, newRestaurant.Address, newRestaurant.City)

	tweet( message, *loc )

	dbhandler.deleteFromQueue(cursor, newRestaurant)

def getMessage(newRestaurant):

	nkfmNameRE = re.compile("^NKFM-(.*)$")
	restoName = newRestaurant.Name
	search = nkfmNameRE.search(restoName)
	if search:
		restoName = "{name} (Kitchener Farmer's Market)".format(name=search.group(1))

	message = "{name}: {address}, {city}".format( 
		name = restoName,
		address = newRestaurant.Address, 
		city = newRestaurant.City)

	return message

def main():
	import argparse
	parser = argparse.ArgumentParser()
	
	parser.add_argument("--authorize", action="store_true",
		help="Authorize this script to update your Twitter account.")
	parser.add_argument("--database", type=dbhandler.dbArgType,
		default='restaurants.db',
		help="SQLite database file for storing updates")

	args = parser.parse_args()

	db = args.database
	cursor = db.cursor()

	if args.authorize:
		(key, secret) = authorize()
		print (key, secret)
		dbhandler.storeKey(cursor, key, secret)
	else:
		(key, secret) = dbhandler.getKey(cursor)
		initialize(key, secret)

		tweetTopOfQueue(cursor)
	
	db.commit()
	db.close()
    
if __name__ == "__main__":
	main()
