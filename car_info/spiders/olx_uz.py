import scrapy
from scrapy.http import HtmlResponse
from car_info.items import CarInfoItem


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
        announce_name = response.css("h1::text").get()
        announce_model = response.xpath("//*[contains(text(), 'Модель:')]/text()").get()
        announce_price = response.xpath("(//h3)[1]/text()").getall()
        announce_year = response.xpath("//*[contains(text(), 'Год выпуска:')]/text()").get()
        announce_mileage = response.xpath("//*[contains(text(), 'Пробег:')]/text()").get()
        announce_date = response.xpath("//*[contains(@*, 'ad-posted-at')]/text()").get()
        announce_url = response.url

        yield CarInfoItem(
            announce_name=announce_name,
            announce_model=announce_model,
            announce_price=announce_price,
            announce_year=announce_year,
            announce_mileage=announce_mileage,
            announce_location=announce_location,
            announce_date=announce_date,
            announce_url=announce_url
        )
