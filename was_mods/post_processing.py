
from pymongo import MongoClient
import spacy
import time
import string
import re

MONGO_HOST = 'mongodb://admin:1234@ec2-52-78-95-18.ap-northeast-2.compute.amazonaws.com'
client = MongoClient(MONGO_HOST)
db = client.usa_db
source_collection = db.usa_tweets_collection
target_collection = db.usa_tweets_named

nlps = spacy.load("en_core_web_sm")
cnt=0
tag_list = ["NNP", "NN"]
removal=['ADV','PRON','CCONJ','PUNCT','PART','DET','ADP','SPACE']

while(True):
    start_time = time.time()
    
    docs = source_collection.find({"nlp_flag": 0}).limit(100)

    print ("start processing 100 items")

    for doc in docs:
        print ("processing... {}".format(doc['search_word']))
        db.usa_tweets_collection.update_one({'_id': doc['_id']}, {'$set': {'nlp_flag': 1}})

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

        # remove specific symbols
        nlp_mention = nlps(re.sub('\W+', ' ', new_mention))

        # text cleansing & insert keyword to db
        for token in nlp_mention:
            if token.is_stop == False and token.is_alpha and len(token) > 2 and token.pos_ not in removal and token.text.lower() not in new_search_list :
                lemma = token.lemma_
                if (token.text == doc["search_word"]):
                    continue
                if (token.tag_ in tag_list):
                    keyword = lemma
                    db.usa_tweets_nlp.find_and_modify(
                        query={'keyword': keyword.lower(), 'search_word': doc["search_word"]},
                        update={'$inc': {'val': 1}},
                        new=True,
                        upsert=True
                    )
        # extract named entities
        for ent in nlp_mention.ents:
            if(ent.text.lower()==doc["search_word"].lower() or ent.text.lower() in new_search_list or ent.label_=="CARDINAL"):
                continue
            db.usa_tweets_named.find_and_modify(
                query={'keyword':ent.text.lower(),'search_word':doc["search_word"],'entity':ent.label_},
                update={'$inc': {'val':1}},
                new = True,
                upsert = True
            )

    print("end processing time: {0:.1f}".format(time.time() - start_time))