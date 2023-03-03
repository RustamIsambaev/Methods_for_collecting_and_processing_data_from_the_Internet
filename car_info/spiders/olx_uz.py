import scrapy
from scrapy.http import HtmlResponse
from car_info.items import CarInfoItem
from scrapy.loader import ItemLoader


class OlxUzSpider(scrapy.Spider):
    name = "olx_uz"
    allowed_domains = ["olx.uz"]
    start_urls = ["https://www.olx.uz/d/transport/legkovye-avtomobili/"]

    def parse(self, response):
        announce_urls = response.xpath("//a[contains(@href, 'obyavlenie')]/@href").getall()
        announce_locations = response.xpath("//p[contains(@*, 'location')]/text()[1]").getall()
        zip_info = zip(announce_urls, announce_locations)
        for announce_url, announce_location in zip_info:
            announce_url_href = "https://www." + self.allowed_domains[0] + announce_url
            yield response.follow(announce_url_href, callback=self.announce_parse, cb_kwargs={"announce_location": announce_location})

        next_page = response.xpath("//a[contains(@*, 'forward')]/@href").get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def announce_parse(self, response: HtmlResponse, announce_location):
        loader = ItemLoader(item=CarInfoItem(), response=response)
        loader.add_css("announce_name", "h1::text")
        loader.add_xpath("announce_price", "(//h3)[1]/text()")
        loader.add_xpath("announce_date", "//*[contains(@*, 'ad-posted-at')]/text()")
        loader.add_value("announce_url", response.url)
        loader.add_value("announce_location", announce_location)
        announce_photos = response.xpath("//img[@data-srcset]/@data-src").getall() + response.xpath("//img[@srcset]/@src").getall()
        loader.add_value("announce_photos", announce_photos)
        loader.add_xpath("announce_description", "(//div[@data-testid='ad-price-container']/..//ul/li//*[text()]//text())[position()>1]")
        loader.add_xpath("announce_id", "//span[contains(text(), 'ID:')]/text()[2]")
        yield loader.load_item()
