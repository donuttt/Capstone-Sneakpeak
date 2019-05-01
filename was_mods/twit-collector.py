import tweepy
import json
from pymongo import MongoClient
import twitter_credentials2
import time
import redis

LOCATION = [-127.3, 24.1, -65.9, 51.8] #USA coordinates

class Tweetmanager():

    def __init__(self, mongo_cli, keywords):
        self.mongo_cli = mongo_cli
        self.keywords = keywords
        if type(self.keywords) == type('str'):
            self.keywords = [].append(keywords)


    def process(self, source):
        if 'retweeted_status' in source:
            return None

        reform_src = self.do_reformat_tweets(source)
        keyw = self.catch_keyword(self.keywords)

        mention = reform_src["mention"]

        if 'is_quote_status' in source and source['is_quote_status']:
            reform_src["quote"] = self.do_reformat_tweets(source["quoted_status"])
            mention = reform_src["quote"]["mention"]

        reform_src["search_word"] = self.catch_keyword(mention)
        if reform_src["search_word"] == "":
            return None

        return self.insert_tweets(reform_src)

    def do_reformat_tweets(self, source):
        mention = source["text"]
        if source['truncated']:
            mention = source['extended_tweet']['full_text']
        doc = {
            "mention": mention,
            "timestamp_ms": source["timestamp_ms"] if 'timestamp_ms' in source else '-1',
            "place": source["place"],
            "geo": source["geo"],
            "favorite_count": source["favorite_count"],
            "hashtags": source["entities"]["hashtags"],
            "id_str": source["id_str"],
            "coordinates": source["coordinates"],
            "retweet_count": source["retweet_count"],
            "reply_count": source["reply_count"],
            "quote_count": source["quote_count"],
            "user": {
                "favourites_count": source["user"]["favourites_count"],
                "followers_count": source["user"]["followers_count"],
                "friends_count": source["user"]["friends_count"],
                "statuses_count": source["user"]["statuses_count"],
                "location": source["user"]["location"],
            },
            "nlp_flag": 0
        }

        return doc

    def catch_keyword(self, mention):
        k = ""
        for keyword in self.keywords:
            if keyword in mention or \
                            keyword.upper() in mention or \
                            keyword.lower() in mention:
                k = keyword
                break
        return k

    def insert_tweets(self, reform_src):
        db = self.mongo_cli.usa_db
        return db.usa_tweets_collection.insert_one(reform_src)

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
            processed = self.tw_manager.process(datajson)

            if processed is None:
                return not self.stoping

            self.cnt = self.cnt + 1

            print("[{0}] {1} processed.".format(k, self.cnt))

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


def search_tweets_with(mongo_cli, api, keyword):
    # Find 'new' tweets (under hashtags/search terms)
    # TODO: pages
    tws = tweepy.Cursor(api.search, q=keyword, result_type="recent", lang="en").items()
    print("Searching under term..." + keyword)

    tw_mn = Tweetmanager(mongo_cli, keyword)

    # Like 'new' tweets (only if the user has more than 100 followers & less than 2500 tweets)
    for tweet in tws:
        tw_mn.process(tweet._json)


if __name__ == '__main__':
    MONGO_HOST = 'mongodb://admin:1234@ec2-13-125-208-40.ap-northeast-2.compute.amazonaws.com'

    consumer_key = twitter_credentials2.CONSUMER_KEY
    consumer_secret = twitter_credentials2.CONSUMER_SECRET
    access_token = twitter_credentials2.ACCESS_TOKEN
    access_token_secret = twitter_credentials2.ACCESS_TOKEN_SECRET

    client = MongoClient(MONGO_HOST)
    redis_cli = redis.Redis(host='localhost', port=6379, db=0)

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    search_tweets_with(client, tweepy.API(auth), "Korean")

    while(False):
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
