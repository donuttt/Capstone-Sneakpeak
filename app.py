#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

from flask import Flask, render_template, request
import logging
from logging import Formatter, FileHandler
import json
from pymongo import MongoClient
import redis
import os

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
app.config.from_object('config')

MONGO_HOST = 'mongodb://admin:1234@localhost'

mongo_cli = MongoClient(MONGO_HOST)
redis_cli = redis.Redis(host='localhost', port=6379, db=0)

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def home():
    return render_template('index.html')

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


@app.route('/fetch', methods=['GET'])
def get_stats_with_keyword(keyword):
    # retain keyword expire time
    redis_cli.set(keyword, keyword)
    redis_cli.expire(keyword, 40)
    redis_cli.sadd("keys", keyword)

    # fetch stats data from mongod
    db = mongo_cli.usa_db
    coll = db.usa_tweets_nlp
    dat = coll.find({"from": keyword})

    # resp
    ret = {
        "code": 1000,
        "message": "Statistic datum from {}".format(keyword),
        "data": dat
    }

    return json.dumps(ret), 200

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
