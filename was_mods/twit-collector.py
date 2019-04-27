import tweepy
import json
from pymongo import MongoClient
import twitter_credentials2


LOCATION = [-127.3, 24.1, -65.9, 51.8] #USA coordinates


class StreamListener(tweepy.StreamListener):

    def __init__(self, api, keywords):
        super(StreamListener, self).__init__(api)
        self.keywords = keywords
        self.cnt = 0

    def catch_keyword(self, mention):
        k = ""
        for keyword in self.keywords:
            if keyword in mention or \
                            keyword.upper() in mention or \
                            keyword.lower() in mention:
                k = keyword
                break
        return k

    def on_connect(self):
        print("You are now connected to the streaming API.")

    def on_error(self, status_code):
        print('An Error has occured: ' + repr(status_code))
        return False

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
            }
        }

        return doc

    def on_data(self, data):
        try:
            db = client.usa_db
            datajson = json.loads(data)

            if 'retweeted_status' in datajson:
                return True

            source_doc = self.do_reformat_tweets(datajson)
            source_doc["nlp_flag"] = 0
            mention = source_doc["mention"]

            if 'is_quote_status' in datajson and datajson['is_quote_status']:
                source_doc["quote"] = self.do_reformat_tweets(datajson["quoted_status"])
                mention = source_doc["quote"]["mention"]

            k = self.catch_keyword(mention)

            if k == "":
                return True

            source_doc["search_word"] = k

            db.usa_tweets_collection.insert_one(source_doc)

            self.cnt = self.cnt + 1
            if self.cnt % 10 == 0:
                print("[{0}] {1} processed.".format(k, self.cnt))

                if self.cnt == 100:
                    print("all processed. \nfinish process.")
                    return False

        except Exception as e:
            print(e)


if __name__ == '__main__':
    MONGO_HOST = 'mongodb://admin:1234@localhost'

    consumer_key = twitter_credentials2.CONSUMER_KEY
    consumer_secret = twitter_credentials2.CONSUMER_SECRET
    access_token = twitter_credentials2.ACCESS_TOKEN
    access_token_secret = twitter_credentials2.ACCESS_TOKEN_SECRET

    client = MongoClient(MONGO_HOST)

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    keywords = ['Korean', 'North Korea', 'South Korea']
    streams = []

    listener = StreamListener(api=tweepy.API(wait_on_rate_limit=True), keywords=keywords)
    streamer = tweepy.Stream(auth=auth, listener=listener)
    streamer.filter(track=listener.keywords, languages=["en"])
