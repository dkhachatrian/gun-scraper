import scrapy
from scrapy.crawler import CrawlerProcess

from typing import Iterable, Dict
from urllib.parse import urlencode

import _utils  # PyCharm complains, but it imports fine...


class GunSpider(scrapy.Spider):

    name = 'gun'

    # # not quite working as expected...
    # def __init__(self, is_debug: bool=False) -> None:
    #     self.name = "gun"
    #     self.is_debug = is_debug

    def start_requests(self) -> None:
        start_url = "https://www.gunpolicy.org/firearms/region/"

        # # the callback will set self.country_options
        # self.country_options:Iterable = ...
        yield scrapy.Request(start_url, callback=self.prepare_links)

    def prepare_links(self, response: scrapy.http.Response) -> Iterable[scrapy.http.Response]:
        '''Builds queries and generates scrapy.Requests'''

        request_url_base = "https://www.gunpolicy.org/firearms/find-gun-policy-facts"
        # removing superfluous "Facts by Country"
        country_options = response.css("#find_country > option::text").getall()[1:]

        # if self.is_debug:
        #     country_options = country_options[:3] # fewer requests, to not be rude to servers

        for country in country_options:
        # for country in country_options[:3]:
            query_dict = {'country': country}  # thankfully, scraped country_options correspond to queries
            request_url = "{0}?{1}".format(request_url_base, urlencode(query_dict))
            yield scrapy.Request(request_url, callback=self.parse_data_page)

    def parse_data_page(self, response: scrapy.http.Response) -> Dict[str, Dict]:
        '''
        Parses pages received. Does *not* generate new Requests

        :param response: response received from callback
        :return:
        '''

        page_label = response.url.split('/')[-1]
        dict_page_data = {}

        # datum_dict = {} # temp

        # for datum in response.css(".dcontent , div:nth-child(1)"):
        for datum in response.css(".level2data div"):
            if not datum.xpath("self::*[string-length() > 0]"):
                continue  # skip empty divs (filtering the content isn't easy..)

            datum_dict = {}  # temp
            # the most recent ancestor with an id will have the relevant label
            # datum_dict['id'] = datum.xpath("ancestor::*[@id][1]").attrib['id']


            try:
                datum_dict['id'] = datum.xpath("descendant-or-self::*[@id][1]").attrib['id']
            except KeyError:
                datum_dict['id'] = datum.xpath("ancestor::*[@id][1]").attrib['id']


            # get text info, either a descendant (in .dcontent) or itself (if first child of .level2data)
            xpath_content = datum.xpath("descendant::*[@class='dcontent']")
            xpath_content = xpath_content if xpath_content else datum.xpath("self::*")
            
            datum_dict['content'] = xpath_content

            datum_dict = _utils.clean_dict(datum_dict)
            # list_page_data.append(datum_dict)
            try: # update if we fail assertions (to catch duds)
                assert datum_dict['id'] in dict_page_data
                assert len(datum_dict['content']) < len(dict_page_data.get(datum_dict['id'], {}))
            except (AssertionError, KeyError):
                dict_page_data[datum_dict['id']] = datum_dict['content']


        # yield {page_label: list_page_data}
        yield {page_label: dict_page_data}



## Quick testing

if __name__ == "__main__":
    process = CrawlerProcess(settings={
        'FEED_FORMAT': 'json',
        'FEED_URI': 'res.json'
    })

    process.crawl(GunSpider)
    process.start()
