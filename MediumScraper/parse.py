from typing import List, Tuple, Optional
from datetime import datetime
from urllib.parse import urljoin

from dotty_dict import Dotty, dotty
from pandas import DataFrame

from MediumScraper.utils import (
    JSONData,
    BASE_IMG_URL
)


class ArticleParser:
    
    @classmethod
    def parse(cls, json_data: JSONData) -> JSONData:
        # Get data for current post, with its key
        post_key, post = cls._get_current_post(json_data)
        if post_key is None or not post:
            return

        # Get data for paragraphs in this post
        paragraphs = cls._get_paragraphs_for_post(
            json_data, 
            post)

        article = {
            'dataframe': cls.extract_sections(paragraphs),
            **cls.extract_details(post)
        }
        return article

    @staticmethod
    def _get_current_post(json_data: JSONData) -> Tuple[Optional[str], Dotty]:
        """ Find and extract JSON data for current article. """
        for key, data in json_data.items():
            details = data.get('responseRootPost', {})
            if details.get('__typename') == 'ResponseRootPost':
                return key.split(':')[-1], dotty(data)
        return None, Dotty({})

    @staticmethod
    def _get_paragraphs_for_post(json_data: JSONData, post: Dotty) -> List[JSONData]:
        data = post.get('content({\"postMeteringOptions\":null})')
        if data is None:
            return list()

        # Extract keys for paragraphs in this post,
        # as specified directly inside the post
        paragraph_keys = list()        
        for item in dotty(data).get('bodyModel.paragraphs', list()):
            key = item.get('__ref')
            if key is not None:
                paragraph_keys.append(key)
        
        # Extract data for each paragraph,
        # spread across the article JSON data
        paragraphs = list()
        for key, data in json_data.items():
            if key in paragraph_keys:
                paragraphs.append(data)
        return paragraphs

    @classmethod
    def extract_details(cls, post: Dotty) -> dict:
        """ Extract general details about the article. """
        publish_date = post.get('firstPublishedAt')
        if publish_date is not None:
            # Format from timestamp (in milliseconds)
            publish_date = datetime.fromtimestamp(
                publish_date/1000).isoformat()

        details = {
            'title': post.get('title'),
            'subtitle': post.get('previewContent.subtitle'),
            'publish_date': publish_date,
            'clap_number': post.get('clapCount'),
        }
        return details

    @classmethod
    def extract_sections(cls, paragraphs: List[JSONData]) -> DataFrame:
        sections = list()

        current = {
            'topic': None,
            'header type': None,
            'context': list(),
            'image urls': list(),
            'image captions': list()
        }
        for p in paragraphs:
            text = p.get('text')
            tag = p.get('type')
            
            if tag.startswith('H'):
                # A header means the end of current section
                if None not in (current['topic'], current['header type']):
                    sections.append(current)
                
                # A new header means a new section
                header = {
                    'topic': text,
                    'header type': tag
                }
                current = {
                    **header,
                    'context': list(),
                    'image urls': list(),
                    'image captions': list()
                }
            else:
                if tag == 'IMG':
                    value = dotty(p).get('metadata.__ref')
                    if value is None:
                        continue
                    img_source = urljoin(BASE_IMG_URL, value.split(':')[-1])
                    
                    current['image urls'].append(img_source)
                    current['image captions'].append(text)
                # NOTE: you might want to extend this list,
                # or eventually use an "else" directly
                elif tag in ('P', 'OLI', 'ULI'):
                    current['context'].append(text)
        
        # No more headers, add last dataframe
        sections.append(current)

        # NOTE: possible to add links when present

        dataframe = DataFrame.from_dict(sections)
        return dataframe