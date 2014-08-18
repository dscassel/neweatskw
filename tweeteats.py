#!/usr/bin/python

import tweepy
import config_twitter
import sqlite3
import dbhandler
import location
import os

auth = tweepy.OAuthHandler(config_twitter.API_CONSUMER_KEY, config_twitter.API_SECRET, secure=True)
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

	message = "{name}: {address}, {city}".format( 
		name = newRestaurant.Name, 
		address = newRestaurant.Address, 
		city = newRestaurant.City)

	loc = location.getLocation(cursor, newRestaurant.Address, newRestaurant.City)


	tweet( message, *loc )


def main():
	import argparse
	parser = argparse.ArgumentParser()
	
	parser.add_argument("--authorize", action="store_true",
	help="Authorize this script to update your Twitter account.")

	args = parser.parse_args()

	db = sqlite3.connect( 'restaurants.db' )
	cursor = db.cursor()

	if args.authorize:
		(key, secret) = authorize()
		print (key, secret)
		dbhandler.storeKey(cursor, key, secret)
	else:
		(key, secret) = dbhandler.getKey(cursor)
		print (key, secret)
		initialize(key, secret)

		tweetTopOfQueue(cursor)
    
if __name__ == "__main__":
	main()
