
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

from pymongo import MongoClient
import time
import re
nltk.downloader.download('vader_lexicon')

MONGO_HOST = 'mongodb://admin:1234@ec2-54-180-32-117.ap-northeast-2.compute.amazonaws.com'
client = MongoClient(MONGO_HOST)
db = client.usa_db
src_coll = db.usa_tweets_collection
target_coll = db.usa_tweets_sentiment

sid = SentimentIntensityAnalyzer()

while(True):
    start_time = time.time()

    docs = src_coll.find({"nlp_flag": 1}).limit(1000)

    print ("start processing 1000 items")

    for doc in docs:
        print ("processing... {}".format(doc['search_word']))
        db.usa_tweets_collection.update_one({'_id': doc['_id']}, {'$set': {'nlp_flag': 2}})

        ss = sid.polarity_scores(doc['mention'])

        neu_score = ss['neu']
        neg_score = ss['neg']
        pos_score = ss['pos']
        update_q = {'$inc':
                        {'neu': neu_score, 'pos': pos_score, 'neg': neg_score}
                    }


        # best_score = max(pos_score, neg_score, neu_score)
        # if neu_score == best_score:
        #     update_q = {'$inc': {'neu': 1}}
        # elif pos_score == best_score:
        #     update_q = {'$inc': {'pos': 1}}
        # else:
        #     update_q = {'$inc': {'neg': 1}}

        target_coll.find_and_modify(
            query={'keyword':doc['search_word']},
            update=update_q,
            new=True,
            upsert=True
        )

    print("end processing time: {0:.1f}".format(time.time() - start_time))
