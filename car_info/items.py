# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class CarInfoItem(scrapy.Item):
    announce_name = scrapy.Field()
    announce_model = scrapy.Field()
    announce_price = scrapy.Field()
    announce_year = scrapy.Field()
    announce_mileage = scrapy.Field()
    announce_location = scrapy.Field()
    announce_date = scrapy.Field()
    announce_url = scrapy.Field()
    _id = scrapy.Field()
