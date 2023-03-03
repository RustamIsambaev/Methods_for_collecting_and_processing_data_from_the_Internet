# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import scrapy
# useful for handling different item types with a single interface
# from itemadapter import ItemAdapter
from pymongo import MongoClient
from scrapy.pipelines.images import ImagesPipeline


class CarInfoPipeline:
    def __init__(self):
        client = MongoClient('localhost', 27017)
        self.mongobase = client.car_info

    def process_item(self, item, spider):
        collection = self.mongobase[spider.name]
        collection.insert_one(item)
        return item


class CarPhotosPipeline(ImagesPipeline):

    def get_media_requests(self, item, info):
        if item["announce_photos"]:
            for img in item["announce_photos"]:
                try:
                    yield scrapy.Request(img)
                except Exception as e:
                    print(e)

    def item_completed(self, results, item, info):
        print(results)
        item["announce_photos"] = [itm[1] for itm in results if itm[0]]
        return item

    def file_path(self, request, response=None, info=None, *, item=None):
        image_perspective = request.url.split('/')[-2]
        image_filename = f'{item["announce_id"]}/{image_perspective}.jpg'
        return image_filename
