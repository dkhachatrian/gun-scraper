from gun_spider import GunSpider
from scrapy.crawler import CrawlerProcess
import _utils
import os

## FLIP FLAGS HERE
IS_DEBUG = False
IS_CRAWL = False
IS_CLEAN = False


prefix = 'debug_' if IS_DEBUG else ''

FEED_FORMAT = 'json'
FEED_URI = '{}res.json'.format(prefix)
CSV_URI = '{}spider_output.csv'.format(prefix)







if __name__ == "__main__":
    if IS_CRAWL:
        # clean up JSON file if it exists
        if os.path.exists(FEED_URI):
            os.remove(FEED_URI)
        
        process = CrawlerProcess(settings={
            'FEED_FORMAT': FEED_FORMAT,
            'FEED_URI': FEED_URI
        })
        process.crawl(GunSpider)
        process.start()  # blocking op

    if IS_CLEAN:  # clean JSON, output to CSV
        _utils.json_to_csv(_utils.post_process_json(FEED_URI), index='country', outp=CSV_URI)