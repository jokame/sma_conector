#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
from tweepy.streaming import StreamListener
from words.tokenizer import vector
import tweepy


class Conector(object):
    def __init__(self, id):
        self.id = id
        self.key = "d2AzpHUpjwSUvdLBcZFg"
        self.secret = "rFumqdgQslgGf8ugtxkoO1ZZS02bplyCj9LI90zuFKw"
        self.token = "88300413-CW6VDJAYGBUM4RtZTXOqQqK2BYIZYtPajTeC7sMby"
        self.tSecret = "xr1RZpvCCsSuZiLnhvfdawj77JoTEgqXiGlXvWIkGY"


class Monitor():
    def __init__(self, conector):
        self.id = conector.id
        self.key = conector.key
        self.secret = conector.secret
        self.token = conector.token
        self.tSecret = conector.tSecret
        self.auth = tweepy.OAuthHandler(self.key, self.secret)
        self.auth.set_access_token(self.token, self.tSecret)
        self.api = tweepy.API(self.auth)
        self.keys = ""

    def setStream(self, listener):
        self.stream = tweepy.Stream(self.auth, listener)


class Stream(StreamListener):

    def __init__(self):
        self.arch = ""
        self.keys = ""
        self.queue = None

    def on_data(self, data):
        self.liveStream(data, self.keys, self.queue)
        return True

    def on_error(self, status):
        print status

    def liveStream(self, obj, keys, queue):
        tweet = json.loads(obj)
        queue[0].sink(vector(tweet['text'], queue[0].path, keys))
        queue[1].sink(tweet['user']['lang'])
        print tweet['text'].encode('utf-8')
