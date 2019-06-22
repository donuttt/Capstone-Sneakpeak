# -*- coding: utf-8 -*-
#########################################################################################################
##  !!!!WARNING!!!!
##  This code contains crawling/scraping code which can be illegal. ( or just illegal. )
##  I use this code just for verifying my capstone project. Also not using commercially or even not publicly opened.
##  If you are a officials of target pages' company, and this code can be problem to your company, please forgive me this one time.
##  Not crawling all items, really small pages.
##  ** Not be used after 01, July. 19. **
#########################################################################################################

import json
import requests
from bs4 import BeautifulSoup
import hashlib
from urllib2 import urlopen
import sys
import csv
import time

data_skull = {
    'title': '',
    'url': '',
    'img': '',
    'img_src_url': '',
    'text': '',
    'type': '',
    'hashed_url': '', # for ID.
}

class SearchCrawler:

    def __init__(self, type, keyw):
        self.type = type
        self.url_skull = {
            'medium': 'https://medium.com/search?q=',
            'google-nws': 'https://www.google.com/search?q={}&tbm=nws&lr=lang_en',
            'reddit': 'https://www.reddit.com/search/?q={}&t=week',
            'pinterest': 'https://www.pinterest.com/resource/BaseSearchResource/get/?source_url=%2Fsearch%2Fpins%2F%3Fq%3D{0}%26rs%3Dtyped&data=%7B"options"%3A%7B"isPrefetch"%3Afalse%2C"query"%3A"{0}"%2C"scope"%3A"pins"%7D%2C"context"%3A%7B%7D%7D&_=1561092495673',
        }
        self.keyw = keyw

    def crawl(self, limit=10):
        url = self.url_skull[self.type]
        if self.type == 'medium':
            return self.crawl_medium(limit, url)

        if self.type == 'google-nws':
            return self.crawl_googlen(limit, url)

        if self.type == 'reddit':
            return self.crawl_reddit(limit, url)

        if self.type == 'pinterest':
            return self.crawl_pinterest(limit, url)

    def crawl_pinterest(self, limit, url):
        page_string = url.format(self.keyw)
        crawl_datas = []

        try:
            cookie = {}
            r = requests.get(
                url=page_string,
                cookies=cookie,
                headers={
                    'Accept': 'application/json, text/javascript, */*, q=0.01',
                    'Referer': 'https://www.pinterest.co.kr/',
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36',
                    'X-APP-VERSION': '1e815a2',
                    'X-Pinterest-AppState': 'active',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            )

            if r.status_code != 200:
                print('requests fail with' + r)
                raise Exception('Connection Failed With Code.' + r.status_code)


            response_json = json.loads(r.text)
            # s = BeautifulSoup(r.text, "html.parser")
            title = ''
            content_url = ''

            for data in response_json['resource_response']['data']['results']:
                imgs = data['images']
                if '170x' in imgs:
                    img = imgs['170x']['url']
                    img_src_url = data['link']
                    if img_src_url is not None:
                        hashed_url = hashlib.md5(img_src_url).hexdigest()
                    else:
                        hashed_url = hashlib.md5(img).hexdigest()

                    crawl_datas.append({
                        'title': '',
                        'url': '',
                        'img': img,
                        'img_src_url': img_src_url,
                        'text': '',
                        'hashed_url': hashed_url,
                        'type': 'image'
                    })

        except Exception as e:
            print 'exception occrus:' + e.message

        return crawl_datas

    def crawl_reddit(self, limit, url):
        page_string = url.format(self.keyw)
        crawl_datas = []

        try:
            cookie = {}
            r = requests.get(
                url=page_string,
                cookies=cookie,
                headers={
                    'X-Requested-With': 'XMLHttpRequest',
                    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36',
                }
            )

            if r.status_code != 200:
                print('requests fail with' + r)
                raise Exception('Connection Failed With Code.' + r.status_code)

            # response_json = json.loads(r.text)
            s = BeautifulSoup(r.text, "html.parser")
            title = ''
            content_url = ''

            for _s in s.select('.scrollerItem'):
                for contents_url in _s.select("a[data-click-id='body']"):
                    content_url = 'https://www.reddit.com' + contents_url.attrs['href']

                    for contents_title in contents_url.select("span"):
                        title = contents_title.text

                crawl_datas.append({
                    'title': title,
                    'url': content_url,
                    'text': '',
                    'hashed_url': hashlib.md5(content_url).hexdigest(),
                    'type': 'text'
                })

        except Exception as e:
            print 'exception occrus:' + e.message

        return crawl_datas

    def crawl_googlen(self, limit, url):
        page_string = url.format(self.keyw)
        crawl_datas = []

        try:
            cookie = {}
            r = requests.get(
                url=page_string,
                cookies=cookie,
                headers={
                    'X-Requested-With': 'XMLHttpRequest',
                    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36',
                }
            )
            if r.status_code != 200:
                print('requests fail with' + r)
                raise Exception('Connection Failed With Code.' + r.status_code)

            # response_json = json.loads(r.text)
            s = BeautifulSoup(r.text, "html.parser")
            title = ''
            content_url = ''

            for _s in s.select('div.ts'):
                for contents_url in _s.select("a.top"):
                    content_url = contents_url.attrs['href']

                for contents_title in _s.select("a.l"):
                    title = contents_title.text

                crawl_datas.append({
                    'title': title,
                    'url': content_url,
                    'text': '',
                    'hashed_url': hashlib.md5(content_url).hexdigest(),
                    'type': 'text'
                })

        except Exception as e:
            print 'exception occrus:' + e.message

        return crawl_datas

    def crawl_medium(self, limit, url):
        page_string = url + self.keyw

        crawl_datas = []

        try:
            cookie = {}
            r = requests.get(
                url=page_string,
                cookies=cookie,
                headers={
                    'X-Requested-With': 'XMLHttpRequest'
                }
            )
            if r.status_code != 200:
                print('requests fail with' + r)
                raise Exception('Connection Failed With Code.'+r.status_code)

            # response_json = json.loads(r.text)
            s = BeautifulSoup(r.text, "html.parser")

            for contents_url in s.select(".postArticle-readMore"):
                url = contents_url.select(".button")[0]
                content_url = url.attrs['href']
                title = ''
                content_str = ''

                r = requests.get(
                    url=content_url,
                    headers={
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                )

                _s = BeautifulSoup(r.text, "html.parser")
                for _title in _s.select('h1.graf'):
                    title = _title.text

                for content in _s.select('p.graf'):
                    content_str = content_str + content.text

                crawl_datas.append({
                    'title': title,
                    'url': content_url,
                    'text': content_str,
                    'hashed_url': hashlib.md5(content_url).hexdigest(),
                    'type': 'text'
                })

        except Exception as e:
            print 'exception occrus:' + e.message

        return crawl_datas


if __name__ == '__main__':
    start_time = time.time()

    # print SearchCrawler('medium', 'samsung').crawl(5)
    # print SearchCrawler('reddit', 'samsung').crawl(5)
    # print SearchCrawler('google-nws', 'samsung').crawl(5)
    print SearchCrawler('pinterest', 'samsung').crawl(5)

    print("end processing time: {0:.1f}".format(time.time() - start_time))