
from gensim.models import Word2Vec
import numpy
import nltk
from nltk.tokenize import RegexpTokenizer
retokenize = RegexpTokenizer("[\w]+")
nltk.download('punkt')

from pymongo import MongoClient
import time
import re

MONGO_HOST = 'mongodb://admin:1234@54.180.122.32'
client = MongoClient(MONGO_HOST)
db = client.usa_db
source_collection = db.usa_tweets_collection
target_collection = db.usa_tweets_named

total_cnt=0


start_time = time.time()

docs = source_collection.find({"search_word": "samsung"})

tokens = []

print ("start tokenizing from tweets")


for doc in docs:
    if total_cnt % 200 == 0:
        print("processing.... {0}".format(total_cnt))

    ## search keyword filtering
    search_list = doc["search_word"].split()
    new_search_list = []
    for word in search_list:
        new_search_list.append(word.lower())

    ## removes 'https'
    ml = list(doc["mention"])
    while (doc["mention"].find('https') != -1):
        s = doc["mention"].find('https')
        del ml[s:s + 24:1]
        doc["mention"] = ''.join(ml)
    new_mention = ''.join(ml)

    _tokens = retokenize.tokenize(new_mention)
    # tokens = tokens + _tokens
    tokens.append(_tokens)

    total_cnt = total_cnt+1

print("Total processed tweets: {0}, Tokens: {1}".format(total_cnt, len(tokens)))

embedding = Word2Vec(tokens, min_count=10, window=3, iter=20, size=100, sg=1)

print(embedding.most_similar(positive=["samsung"], topn=100))

print("end processing time: {0:.1f}".format(time.time() - start_time))