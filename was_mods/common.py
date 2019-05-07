
import pymongo.errors

class Tweetmanager():

	def __init__(self, mongo_cli, keywords, _type='r'):
		self.mongo_cli = mongo_cli
		self.keywords = keywords
		self._type = _type
		if isinstance(self.keywords, type('str')):
			self.keywords = [keywords]

	def process(self, source):
		if 'retweeted_status' in source:
			return None, "Remove retweets."

		reform_src = self._do_reformat_tweets(source)

		mention = reform_src["mention"]

		if 'is_quote_status' in source and 'quoted_status' in source:
			reform_src["quote"] = self._do_reformat_tweets(source["quoted_status"])
			mention = reform_src["quote"]["mention"]

		reform_src["search_word"] = self.catch_keyword(mention)
		if reform_src["search_word"] == "":
			return None, "Remove which is not contain source keyword."

		return self.insert_tweets(reform_src)

	def do_reformat_realtime(self, source):
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

	def do_reformat_search(self, source):
		mention = source["full_text"]
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
		try:
			ret = db.usa_tweets_collection.insert_one(reform_src)
			return ret, ""

		except pymongo.errors.DuplicateKeyError:
			return True, "Key duplicated"

	def _do_reformat_tweets(self, source):
		if self._type == 'r':
			return self.do_reformat_realtime(source)
		elif self._type == 's':
			return self.do_reformat_search(source)

		return None