
from common import Tweetmanager
import tweepy
import tweepy.error
import twitter_credentials2
import redis
from pymongo import MongoClient
import time


def fetch_keyw_from(redis_cli):
	ret = None
	member_key = "search"

	# fetch list with key
	ll = redis_cli.smembers(member_key)

	for keyword in ll:
		redis_cli.srem(member_key, keyword)
		_k = redis_cli.get(member_key + "_" + keyword)

		if _k == None:
			redis_cli.set(member_key + "_" + keyword, 1)
			ret = keyword
			break

	return ret


def search_tweets_with(mongo_cli, api, keyword):
	# Find 'new' tweets (under hashtags/search terms)
	# TODO: pages
	tws = tweepy.Cursor(api.search, q=keyword+ " -filter:retweets", result_type="mixed", lang="en", tweet_mode='extended').items(100)
	print("Searching under term..." + keyword)

	tw_mn = Tweetmanager(mongo_cli, keyword, 's')
	processed_cnt = 0

	try:
		for tweet in tws:
			ret, reason = tw_mn.process(tweet._json)
			if ret == None:
				print("Not handled: {0}".format(reason))

			processed_cnt = processed_cnt + 1
			print ("{} processed.".format(processed_cnt))

	except tweepy.error.TweepError as e:
		print str(e)


if __name__ == '__main__':
	MONGO_HOST = 'mongodb://admin:1234@localhost'

	consumer_key = twitter_credentials2.CONSUMER_KEY
	consumer_secret = twitter_credentials2.CONSUMER_SECRET
	access_token = twitter_credentials2.ACCESS_TOKEN
	access_token_secret = twitter_credentials2.ACCESS_TOKEN_SECRET

	client = MongoClient(MONGO_HOST)
	redis_cli = redis.Redis(host='localhost', port=6379, db=0)

	auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
	auth.set_access_token(access_token, access_token_secret)

	while(True):
		ret = fetch_keyw_from(redis_cli)
		if ret is None:
			time.sleep(1)
			continue

		search_tweets_with(client, tweepy.API(auth), ret)
