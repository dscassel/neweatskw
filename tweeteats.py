#!/usr/bin/python

import tweepy
import config_twitter
import sqlite3
import dbhandler
import location

auth = tweepy.OAuthHandler(config_twitter.API_CONSUMER_KEY, config_twitter.API_SECRET, secure=True)

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
	api.update_status(message, None, latitude, longitude)

def main():
	import argparse
	parser = argparse.ArgumentParser()
	
	parser.add_argument("--authorize", action="store_true",
	help="Authorize this script to update your Twitter account.")

	if args.authorize:
		(key, secret) = authorize()
		dbhandler.storeKey(cursor, key, secret)
    
