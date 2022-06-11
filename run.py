from scrapyscript import Job, Processor
from scrapy.settings import Settings
import pandas as pd
from MediumScraper.spiders import medium


def get_json_from_url(url: str):
    """ Allows running the spider from a script, for a given URL. """
    # Cf. https://stackoverflow.com/a/62902603
    job = Job(medium.MediumArticleSpider, article_url=url)
    
    settings = Settings(values={'LOG_LEVEL': 'ERROR'})
    processor = Processor(settings=settings)
    
    results = processor.run(job)
    
    output = list()
    if len(results) > 0:
        output = results[0]
    
    return output

if __name__ == '__main__':
    url = "https://medium.com/dair-ai/an-illustrated-guide-to-graph-neural-networks-d5564a551783 z"
    data = get_json_from_url(url= url)
    print(data)
    print(data.keys())
    print(data['title'])
    print(data['dataframe'])
    print(data['clap_number'])
    data['dataframe']['page_link'] = url
    data['dataframe'].to_csv('dataframe.csv')

