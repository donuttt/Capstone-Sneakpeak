import tweepy
import json
from pymongo import MongoClient
import twitter_credentials2
import time
import redis
from common import Tweetmanager
import os

LOCATION = [-127.3, 24.1, -65.9, 51.8] #USA coordinates


class StreamListener(tweepy.StreamListener):

    def __init__(self, api, mongo_cli, keywords):
        super(StreamListener, self).__init__(api)
        self.keywords = keywords
        self.cnt = 0
        self.stoping = False
        self.mongo_cli = mongo_cli
        self.tw_manager = Tweetmanager(self.mongo_cli, keywords)

    def stop(self):
        self.stoping = True

    def on_connect(self):
        print("You are now connected to the streaming API with K: {0}".format(map(str, self.keywords)))

    def on_error(self, status_code):
        print('An Error has occured: ' + repr(status_code))
        return False

    def on_data(self, data):
        try:
            datajson = json.loads(data)
            processed, reason = self.tw_manager.process(datajson)

            if processed is None:
                return not self.stoping

            self.cnt = self.cnt + 1

            print("{0} processed.".format(self.cnt))

        except Exception as e:
            print(e)


def fetch_keyw_from(redis_cli):
    ret = []
    member_key = "keys"

    # fetch list with key
    ll = redis_cli.smembers(member_key)

    for keyword in ll:
        _k = redis_cli.get(keyword)
        if _k == None:
            redis_cli.srem(member_key, keyword)
        else:
            ret.append(_k)

    return ret


if __name__ == '__main__':
    env = 'dev' if os.getenv('CAPSTONE_DEV_ENV') else 'prod'
    if env == 'dev':
        MONGO_HOST = 'mongodb://admin:1234@54.180.122.32/usa_db'
        MONGO_CLI = MongoClient(MONGO_HOST)
        REDIS_CLI = redis.Redis(host='54.180.122.32', port=6379, db=0)
    else:
        MONGO_HOST = 'mongodb://admin:1234@127.0.0.1/usa_db'
        MONGO_CLI = MongoClient(MONGO_HOST)
        REDIS_CLI = redis.Redis(host='127.0.0.1', port=6379, db=0)


    consumer_key = twitter_credentials2.CONSUMER_KEY
    consumer_secret = twitter_credentials2.CONSUMER_SECRET
    access_token = twitter_credentials2.ACCESS_TOKEN
    access_token_secret = twitter_credentials2.ACCESS_TOKEN_SECRET

    client = MONGO_CLI
    redis_cli = REDIS_CLI

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    while(True):
        keywords = fetch_keyw_from(redis_cli)
        streams = []

        listener = StreamListener(api=tweepy.API(wait_on_rate_limit=True), mongo_cli=client, keywords=keywords)
        streamer = tweepy.Stream(auth=auth, listener=listener)
        streamer.filter(track=listener.keywords, languages=["en"], is_async=True)

        t_limit = 30
        t = 0
        while(True):
            t = t + 1
            time.sleep(1)
            if t == t_limit:
                print("STREAM STOP")
                streamer.disconnect()
                listener.stop()
                streamer._thread.join()
                break
