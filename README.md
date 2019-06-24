
![License MIT](https://img.shields.io/badge/License-MIT-red.svg)
![License MIT](https://img.shields.io/badge/data-web-blue.svg)

# Peeping Tom
제시된 검색어로부터 Social Media 에서 데이터를 수집하여, real-time으로 유저에게 분석된 결과를 보여주는 연구 프로젝트입니다.
___
## 3 step flow
### Data Collecting
데이터 수집은 Twitter API와 Scraping, 두가지 방식을 이용하고 있습니다.
Twitter API는 무료로 사용할경우 1 Connection만을 제공하기 때문에, 상시 Connection을 관리하는 Process가 떠있습니다. (Search API, Stream API 총 2개의 Process)
Scraping은  On Demand Request 형식으로, 총 10초 정도 소요됩니다.

### Data Processing
nltk와 spacy를 이용하여 POS-Tagging 정보와 Named Entity 정보를 추출하여 이용하고 있습니다.
명사어구는 real-time으로 검색어를 확장하는곳에 사용하기위해 따로 저장하고,  그 외 형용어구는 유저의 분석 이해를 높이기 위해 따로 저장하고 있습니다. 

### Visualize
Highchart를 이용하여 데이터를 Visualize 합니다.
___
## Utilization
0. 설정
configs/config.py: 이용 주소 변경
was_mods/twitter_credentials2.py: twitter key 발급해서 변경
templates/main.html: 서버 주소 변경

1. flask 서버 실행 (app.py)
2. daemon 실행 (twit_collector.py, twit_searcher.py, post_processing.py)
3. web root 접근 ('http://host:30303/')

___
### References
* [spacy](https://github.com/explosion/spaCy) ![License MIT](https://img.shields.io/badge/License-MIT-red.svg)
* [nltk](https://github.com/nltk/nltk) ![License Apache2.0](https://img.shields.io/badge/License-Apache%202.0-yellowgreen.svg)
* [tweepy](https://github.com/tweepy/tweepy) ![License MIT](https://img.shields.io/badge/License-MIT-red.svg)
* [beautifulsoup](https://www.crummy.com/software/BeautifulSoup/) ![License MIT](https://img.shields.io/badge/License-CC-orange.svg)
* [flask](http://flask.pocoo.org/docs/1.0/) ![License MIT](https://img.shields.io/badge/License-BSD-brightgreen.svg)
* [mongodb](https://www.mongodb.com)
* [highchart](https://www.highcharts.com)

