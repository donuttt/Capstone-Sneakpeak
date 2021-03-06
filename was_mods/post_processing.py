
from pymongo import MongoClient
import spacy
import time
import string
import re
from datetime import datetime

import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

from pymongo import MongoClient
import time
import re
nltk.downloader.download('vader_lexicon')

MONGO_HOST = 'mongodb://admin:1234@54.180.122.32/usa_db'
client = MongoClient(MONGO_HOST)
db = client.usa_db

nlps = spacy.load("en_core_web_sm")
cnt=0
tag_list = ["NNP", "NN"]
removal=['ADV','PRON','CCONJ','PUNCT','PART','DET','ADP','SPACE']

class PostProcessing:

    def __init__(self, db):
        self.db = db
        self.sid = SentimentIntensityAnalyzer()
        self.stopping = False
        self.stopped = False

        self.src_coll = self.db.usa_tweets_collection
        self.nlp_coll = self.db.usa_tweets_nlp_exp
        self.nlp_others_coll = self.db.usa_tweets_nlp_others_exp
        self.sentiment_count_coll = self.db.usa_tweets_sentiment_count_exp
        self.nlp_named_coll = self.db.usa_tweets_named_exp
        self.sentiment_ts_coll = self.db.usa_tweets_sentiment_ts_exp
        self.plus_stop_words = ['sex', 'time', 'day', 'amp2', 'amp', 'today', 'yesterday', 'tomorrow', 'date', 'first']

    def stop(self):
        self.stopping = True

    def fetch(self):
        print ("Fetch 1000 items.")

        return self.src_coll.find({"nlp_flag": 0}, {'_id':1, 'mention':1, 'search_word':1, 'timestamp_ms':1}).limit(1000)

    def cleansing(self, search_word, mention):
        ret = []

        ## search keyword filtering
        search_list = search_word.split()
        new_search_list = []
        for word in search_list:
            new_search_list.append(word.lower())

        ## removes 'https'
        ml = list(mention)
        while (mention.find('https') != -1):
            s = mention.find('https')
            del ml[s:s + 24:1]
            mention = ''.join(ml)
        new_mention = ''.join(ml)

        # remove specific symbols
        nlp_mention = nlps(re.sub('\W+', ' ', new_mention))

        # text cleansing & insert keyword to db
        for token in nlp_mention:
            if token.is_stop == False and token.is_alpha and len(token) > 2 and token.pos_ not in removal and token.text.lower() not in new_search_list  and token.lemma_ not in self.plus_stop_words:
                lemma = token.lemma_
                ret.append(token)

        return ret, nlp_mention.ents


    def process(self):
        while not self.stopping:
            start_time = time.time()
            src = self.fetch()
            process_cnt = 0

            for doc in src:
                process_cnt = process_cnt + 1
                self.src_coll.update_one({'_id': doc['_id']}, {'$set': {'nlp_flag': 4}})

                search_word = doc['search_word']
                mention = doc['mention']
                timestamp_ms = doc['timestamp_ms'] if 'timestamp_ms' in doc else "-1"
                if search_word in self.plus_stop_words:
                    continue

                clean_tokens, nes = self.cleansing(search_word, mention)

                self.process_named_entity(nes, search_word)
                sentiment = self.process_sentiment(search_word, mention, timestamp_ms)
                self.process_normal_nlp_and_sentiment_count(clean_tokens, search_word, sentiment)

            if process_cnt == 0:
                time.sleep(5)

            print("end processing time: {0:.1f}".format(time.time() - start_time))

        self.stopped = True

    def process_normal_nlp_and_sentiment_count(self, tokens, search_word, sentiment):
        for token in tokens:
            lemma = token.lemma_
            keyword = lemma

            if (token.text == search_word):
                continue
            if (token.tag_ in tag_list):
                self.nlp_coll.find_one_and_update(
                    {'keyword': keyword.lower(), 'search_word': search_word},
                    {'$inc': {'val': 1}},
                    new=True, upsert=True
                )
            else:
                self.nlp_others_coll.find_one_and_update(
                    {'keyword': keyword.lower(), 'search_word': search_word},
                    {'$inc': {'val': 1}, '$set': {'tag': token.tag_}},
                    new=True, upsert=True
                )

            if sentiment != 0:
                self.sentiment_count_coll.find_one_and_update(
                    {'sentiment': sentiment, 'search_word': search_word, 'keyword': keyword.lower()},
                    {'$inc': {'val': 1}, '$set': {'tag': token.tag_}},
                    new=True, upsert=True
                )

    def process_named_entity(self, nes, search_word):
        search_list = search_word.split()
        new_search_list = []
        for word in search_list:
            new_search_list.append(word.lower())

        for ent in nes:
            if (ent.text.lower() == search_word.lower() or ent.text.lower() in new_search_list or ent.label_ == "CARDINAL"):
                continue
            self.nlp_named_coll.find_one_and_update(
                {'keyword': ent.text.lower(), 'search_word': search_word, 'entity': ent.label_},
                {'$inc': {'val': 1}},
                new=True, upsert=True
            )

    def process_sentiment(self, search_word, mention, timestamp_ms):
        print ("processing... {}".format(search_word))

        ss = self.sid.polarity_scores(mention)
        neu_score = ss['neu']
        neg_score = ss['neg']
        pos_score = ss['pos']
        compound_score = ss['compound']
        update_q = {'$inc':
                        {'compound': compound_score, 'neu': neu_score, 'pos': pos_score, 'neg': neg_score,
                         'total': 1}
                    }

        #
        # datetime = datetime.utcfromtimestamp(int(doc['timestamp_ms'][:10])).strftime("%Y.%m.%d.")
        if timestamp_ms != "-1":
            _datetime_100sec = int(timestamp_ms[:8] + '00')
        else:
            _datetime_100sec = 0

        self.sentiment_ts_coll.find_one_and_update(
            {'keyword': search_word, 'ts_hundredsec': _datetime_100sec},
            update_q,
            new=True, upsert=True
        )

        if compound_score <= 0.2:
            return 'neg'
        elif compound_score >= 0.2:
            return 'pos'
        else:
            return 'neu'

pp = PostProcessing(db)
pp.process()