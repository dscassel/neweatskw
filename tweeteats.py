#!/usr/bin/python

import tweepy
import config_twitter

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


