import praw
import getopt
import sys
import sqlite3
import re
import logging
import time
from imgurpython import ImgurClient
from imgurpython.helpers.error import ImgurClientRateLimitError

CLIENT_ID = "33d1b2294b375a6"
CLIENT_SECRET = "a8d4befc31b112e45f98314b38bca8b8729ba3d6"
AUTH = {"Authorization": "Client-ID " + CLIENT_ID}
REDDIT_AUTH = {'User-Agent': '/u/haha-forcedlaugh'}



class RedditItem:
    def __init__(self, url, score, subid):
        self.url = url
        self.score = score
        self.subid = subid


client = ImgurClient(CLIENT_ID, CLIENT_SECRET)


def process_imgur_link(item):
    result = []
    if re.match('.*\.(?:png|jpg|gif)', item.url):
        result += [item]
    elif re.match('.*imgur.com/a/.*$', item.url) or re.match('.*imgur.com/gallery/.*$', item.url):

        if len(item.url.split('imgur.com/a/')) > 1:
            itemId = item.url.split('imgur.com/a/')[1]
        else:
            itemId = item.url.split('imgur.com/gallery/')[1]

        try:
            images = client.get_album_images(itemId)
            for child in images:
                child_item = RedditItem(child.link, item.score, item.subid)
                result += parse_item(child_item)
        except ImgurClientRateLimitError as e:
            time.sleep(10)
            logging.exception("Hit the rate limit!")
        except Exception as ex:
            logging.exception("Something happened getting the album!")
    elif re.match('.*imgur.com/.*$', item.url):
        itemId = item.url.split('imgur.com/')[1]
        try:
            image = client.get_image(itemId)
            item = RedditItem(image.link, item.score, item.subid)
            result += [item]
        except ImgurClientRateLimitError as e:
            logging.exception("Hit the rate limit!")
            time.sleep(10)
        except Exception as ex:
            logging.exception("Something happened getting the album!")
    return result


def parse_item(item):
    result = []
    if re.match('.*imgur.com/.*$', item.url):
        result = process_imgur_link(item)
    else:
        result += [item]
    return result


def main(argv):
    try:
        opts, args = getopt.getopt(argv, "d:t:l:", ["db=", "table=", "limit="])
    except getopt.GetoptError:
        print "Usage: redditCrawler.py -d <db_name> -t <tablename> -l <limit> <subreddit1> <subreddit2> <...>"
        sys.exit(2)
    if len(argv) < 7:
        print "Usage: redditCrawler.py -d <db_name> -t <tablename> -l <limit> <subreddit1> <subreddit2> <...>"
        sys.exit(2)

    table_name = "images"
    db = "reddit.sqlite"

    for opt, arg in opts:
        if opt in ("-d", "--db"):
            db = arg
        elif opt in ("-t", "--table"):
            table_name = arg
    subnames = argv[6:]

    db = sqlite3.connect(db)
    cur = db.cursor()

    sql = 'create table if not exists ' + table_name + ' (id INTEGER PRIMARY  KEY, ' \
                                                       'link varchar(255), ' \
                                                       'score INTEGER, ' \
                                                       'subid varchar(255))'
    cur.execute(sql)
    db.commit()

    for sub in subnames:
        print "Searching %s ..." % sub

        r = praw.Reddit(user_agent='Custom Site Example for PRAW')
        for c in praw.helpers.submissions_between(r, sub):
            try:
                sql = "SELECT subid FROM " + table_name + " WHERE subid = ?"
                cur.execute(sql, (c.id,))
                data = cur.fetchone()
                if data is None:
                    items = []
                    crawl_item = RedditItem(c.url, c.score, c.id)
                    items += parse_item(crawl_item)
                    if len(items) is 0:
                        continue
                    for item in items:
                        sql = "INSERT INTO " + table_name + " (link, score, subid) VALUES (?, ?, ?)"
                        cur.execute(sql, (item.url, item.score, item.subid))
                        db.commit()
                else:
                    print('Sub %s skipped: %s' % (c.id, c.title))
            except sqlite3.Error as er:
                print("Unexpected error:", er)


if __name__ == '__main__':
    main(sys.argv[1:])
