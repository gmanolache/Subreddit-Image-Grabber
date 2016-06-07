'''
Created on Mar 13, 2014

@author: Kyle Moy
'''
import requests, re, sys
import praw

CLIENT_ID = "33d1b2294b375a6"
AUTH = {"Authorization": "Client-ID " + CLIENT_ID};
REDDIT_AUTH = {'User-Agent': '/u/Vindicator209'}


def parseItem(item):
    result = []
    url = item.url
    if re.match('.*imgur.com/a/.*$', url) or re.match('.*imgur.com/gallery/.*$', url):
        '''
        Imgur Album
        '''
        itemid = url.split('imgur.com/a/')[1]
        api = 'https://api.imgur.com/3/album/'
        source = requests.get(api + itemid, headers=AUTH)
        json = source.json()
        if json['status'] != 200:
            return
        for child in json['data']['images']:
            item = redditItem(child['link'], item.score)
            result += parseItem(item)
    elif re.match('.*\.(?:png|jpg|gif)', url):
        '''
        Image
        '''
        result += [item]
    elif re.match('.*imgur.com/.*$', url):
        '''
        Imgur Link
        '''
        itemid = url.split('imgur.com/')[1]
        api = 'https://api.imgur.com/3/image/'
        source = requests.get(api + itemid, headers=AUTH)
        json = source.json()
        if 'data' not in json or 'link' not in json['data']:
            return
        link = json['data']['link']
        item = redditItem(link, item.score)
        result += [item]
    else:
        print "UNKNOWN: %s" % url
    return result


def parse(sub, limit):
    '''
    Parse Subreddit
    '''
    items = []

    r = praw.Reddit(user_agent='Custom Site Example for PRAW')
    for c in praw.helpers.submissions_between(r, sub):
        item = redditItem(c.url, c.score)
        try:
            items += parseItem(item)
        except:
            print("Unexpected error:", sys.exc_info()[0])

    return items


class redditItem(object):
    '''
    Do I actully need this? Nope!
    '''

    def __init__(self, url, score):
        '''
        Constructor
        '''
        self.url = url
        self.score = score

    def display(self):
        print self.url
