

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
src_coll = db.usa_tweets_collection
target_coll = db.usa_tweets_sentiment_ts

sid = SentimentIntensityAnalyzer()

while(True):
    start_time = time.time()

    docs = src_coll.find({"nlp_flag": 3}).limit(1000)

    print ("start processing 1000 items")

    for doc in docs:
        print ("processing... {}".format(doc['search_word']))
        # db.usa_tweets_collection.update_one({'_id': doc['_id']}, {'$set': {'nlp_flag': 3}})


        if doc['timestamp_ms'] == "-1":
            continue
        #
        # datetime = datetime.utcfromtimestamp(int(doc['timestamp_ms'][:10])).strftime("%Y.%m.%d.")
        _datetime_100sec = int(doc['timestamp_ms'][:8] + '00')
        ss = sid.polarity_scores(doc['mention'])
        neu_score = ss['neu']
        neg_score = ss['neg']
        pos_score = ss['pos']
        compound_score = ss['compound']
        update_q = {'$inc':
                        {'compound': compound_score, 'neu': neu_score, 'pos': pos_score, 'neg': neg_score, 'total':1}
                    }

        target_coll.find_and_modify(
            query={'keyword':doc['search_word'], 'ts_hundredsec': _datetime_100sec},
            update=update_q,
            new=True,
            upsert=True
        )

    print("end processing time: {0:.1f}".format(time.time() - start_time))



