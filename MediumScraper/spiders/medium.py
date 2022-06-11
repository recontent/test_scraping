import json

from scrapy import Spider, Request
from scrapy.http import HtmlResponse
from scrapy.selector import Selector

from MediumScraper.parse import ArticleParser
from MediumScraper.utils import *


def extract_article_json(selector: Selector) -> JSONData:
    """ Extract article JSON content located in <script> element. """
    script_element = selector.xpath(
        '//script[contains(text(), "ROOT_QUERY")]')
    if script_element:
        json_content = script_element.xpath(
            'normalize-space(substring-after(., "= "))'
        ).get()
        return json.loads(json_content)
    return dict()

class MediumArticleSpider(Spider):
    name = 'medium'
    custom_settings = {
        'AUTOTHROTTLE_ENABLED': True,
        'ROBOTSTXT_OBEY': False,
        'COOKIES_ENABLED': False,
        'DEFAULT_REQUEST_HEADERS': DEFAULT_REQUEST_HEADERS,
    }

    def start_requests(self):
        # NOTE: "article_url" parameter needs to be given to the spider
        article_url = getattr(self, 'article_url')
        if article_url is None:
            self.logger.error('No article URL was given.')
        else:
            yield Request(self.article_url)

    def parse(self, response: HtmlResponse):
        page_json_data = extract_article_json(response.selector)
        return ArticleParser.parse(page_json_data)
