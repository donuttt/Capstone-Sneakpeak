#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

from flask import Flask, render_template, request, jsonify
import logging
from logging import Formatter, FileHandler
import json
from pymongo import MongoClient
import redis
from bson.json_util import dumps
import os
from configs.config import config_via_env

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
env = 'dev' if os.getenv('CAPSTONE_DEV_ENV') else 'prod'

app.config.from_object(config_via_env[env])

mongo_cli = app.config['MONGO_CLI']
redis_cli = app.config['REDIS_CLI']

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def home():
    return render_template('main.html')

@app.route('/test', methods=['GET', 'POST'])
def test_method():
    ret = {
        "message": "Hi",
        "data": {"p":"q"}
    }
    return json.dumps(ret), 200

@app.errorhandler(500)
def internal_error(error):
    #db_session.rollback()
    return render_template('errors/500.html'), 500


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

@app.route('/sentiment/ts', methods=['POST'])
def post_sentiment_ts_with_keywords():
    data = json.loads(request.data)
    keywords = data['keywords']
    ts_idx_each_keyw = data['ts_idx_each_keyw']

    if type(keywords) != list or len(keywords) == 0:
        ret = {
            "code": -1000,
            "message": "Please serve keyword with your request!!",
            "data": {}
        }
        return json.dumps(ret), 200

    ret_dat = {}
    for keyword in keywords:
        ts_idx = 0
        if keyword in ts_idx_each_keyw:
            ts_idx = ts_idx_each_keyw[keyword]

        # fetch stats data from mongod
        db = mongo_cli.usa_db
        coll = db.usa_tweets_sentiment_ts
        dat = list(coll.find({"keyword": keyword.lower(), "ts_hundredsec": {'$gt': ts_idx}}).sort('ts_hundredsec', -1).limit(10))
        ret_dat[keyword] = []
        for d in dat:
            ret_dat[keyword].insert(0, {
                'val': d['pos']/d['total'] - d['neg']/d['total'],
                'ts': d['ts_hundredsec'],
            })

    # resp
    ret = {
        "code": 1000,
        "message": "Statistic datum from {}".format(keyword),
        "data": dumps(ret_dat),
    }
    resp = jsonify(ret)
    resp.headers.add('Access-Control-Allow-Origin', '*')

    return resp, 200


@app.route('/fetch/list', methods=['POST'])
def get_stats_with_keywords():
    data = json.loads(request.data)
    keywords = data['keywords']
    if type(keywords) != list or len(keywords) == 0:
        ret = {
            "code": -1000,
            "message": "Please serve keyword with your request!!",
            "data": {}
        }
        return json.dumps(ret), 200

    ret_dat = []
    denoms_per_dat = {}

    for keyword in keywords:
        keyword = keyword.lower()
        print keyword
        if keyword not in ["samsung", "north korea", "south korea", "apple"]:
            # retain keyword expire time
            redis_cli.set(keyword, keyword)
            redis_cli.expire(keyword, 40)
            redis_cli.sadd("keys", keyword)
            redis_cli.sadd("search", keyword)

        # fetch stats data from mongod
        db = mongo_cli.usa_db
        coll = db.usa_tweets_named
        dat = list(coll.find({"search_word": keyword}, {"search_word": 1, "keyword": 1, "val": 1, "_id": 0}).sort('val', -1).limit(6))
        denoms_per_dat[keyword] = 0
        for i in dat:
            denoms_per_dat[keyword] = denoms_per_dat[keyword] + i['val']
        ret_dat += dat

    # resp
    ret = {
        "code": 1000,
        "message": "Statistic datum from {}".format(keyword),
        "denoms": dumps(denoms_per_dat),
        "data": dumps(ret_dat),
    }
    resp = jsonify(ret)
    resp.headers.add('Access-Control-Allow-Origin', '*')

    return resp, 200


@app.route('/fetch', methods=['GET'])
def get_stats_with_keyword():
    keyword = request.args.get('k')
    if keyword is None or keyword == "":
        ret = {
            "code": -1000,
            "message": "Please serve keyword with your request!!",
            "data": {}
        }
        return json.dumps(ret), 200

    if keyword not in ["Samsung", "North Korea", "South Kroea"]:
        # retain keyword expire time
        redis_cli.set(keyword, keyword)
        redis_cli.expire(keyword, 40)
        redis_cli.sadd("keys", keyword)
        redis_cli.sadd("search", keyword)

    # fetch stats data from mongod
    db = mongo_cli.usa_db
    coll = db.usa_tweets_nlp
    dat = coll.find({"search_word": keyword}, {"keyword":1, "val":1, "_id":0}).sort('val', -1).limit(10)

    # resp
    ret = {
        "code": 1000,
        "message": "Statistic datum from {}".format(keyword),
        "keyword": keyword,
        "data": dumps(dat)
    }
    resp = jsonify(ret)
    resp.headers.add('Access-Control-Allow-Origin', '*')

    return resp, 200

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=30303)
