# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from itemloaders.processors import Compose, TakeFirst


def get_price(value):
    try:
        value = int(value[0].replace(" ", ""))
    except:
        return value
    return value


def get_description(value):
    try:
        params_dict = {}
        i = 1
        for parametr in value:
            if parametr.find(":") == -1:
                param_name = f'param_{i}'
                params_dict[param_name] = parametr
                i += 1
            else:
                params_dict[parametr.split(":", 1)[0]] = parametr.split(":", 1)[1]
        value = params_dict
    except:
        return value
    return value


class CarInfoItem(scrapy.Item):
    announce_name = scrapy.Field(output_processor=TakeFirst())
    announce_price = scrapy.Field(input_processor=Compose(get_price), output_processor=TakeFirst())
    announce_date = scrapy.Field(output_processor=TakeFirst())
    announce_url = scrapy.Field(output_processor=TakeFirst())
    announce_location = scrapy.Field(output_processor=TakeFirst())
    announce_photos = scrapy.Field()
    announce_description = scrapy.Field(input_processor=Compose(get_description), output_processor=TakeFirst())
    announce_id = scrapy.Field(output_processor=TakeFirst())
    _id = scrapy.Field()
