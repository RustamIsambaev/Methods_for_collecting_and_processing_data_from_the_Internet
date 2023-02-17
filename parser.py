"""
для корректной работы скрипта необходимо наличие установленных библиотек:
1) requests
2) lxml
3) pandas
4) openpyxl
5) numpy

скрит выполняет парсинг главных новостей с сайтов: dzen.ru и lenta.ru на выбор
"""
import requests
import pandas as pd
from lxml import html

#заголовки и адреса сайтов
headers = {'User_Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/110.0.0.0 Safari/537.36'}
dzen = 'https://dzen.ru/?sso_failed=error'
lenta = 'https://www.lenta.ru/'

# парсинг lenta.ru
def parse_lenta():
    response_lenta = requests.get(url=lenta, headers=headers) #формируем запрос
    dom = html.fromstring(response_lenta.text) #получаем объектную модель главной страницы сайта
    parse_info = {'source': [], 'title': [],
                  'href': dom.xpath('''//a[contains(@class, "topnews") and not(contains(@class, "button"))]/@href'''),
                  'ann_date': []} #создаем струкиру данных и сохраняем в нее ссылки по главным новостям сайта
    for i in range(len(parse_info['href'])): #дополняем внутренние ссылки сайта для создания полноценных ссылок
        if parse_info['href'][i][0:4] != 'http':
            parse_info['href'][i] = lenta + parse_info['href'][i]
    for url in parse_info['href']: #для получения остальных данных нужно дополнительно пропарсить страницы с новостями
        sub_response_lenta = requests.get(url=url, headers=headers)
        sub_dom = html.fromstring(sub_response_lenta.text)
        if url.find('moslenta') != -1: #в случае с moslenta отдельный запрос
            parse_info['ann_date'].append(sub_dom.xpath('''(//div[contains(@data-qa, 'topic-header')]//div
            [contains(text(), ':')])[1]/text()'''))
            parse_info['title'].append(sub_dom.xpath('''(//div[contains(@data-qa, 'topic-header')]/h1)[1]/text()'''))
            parse_info['source'].append(sub_dom.xpath('''((//div[contains(@data-qa, 'lb-block')])[1]//a
            [contains(@href, 'http')])[1]/@href'''))
        else: #в случае с lenta.ru - большинство страниц с новостями именно здесь
            parse_info['ann_date'].append(sub_dom.xpath('''//a[contains(@class, "topic-header__time")]/text()'''))
            parse_info['title'].append(sub_dom.xpath('''(//span[@class="topic-body__title"])[1]/text()'''))
            parse_info['source'].append(sub_dom.xpath('''(//div[@class = "topic-body__content"]//a
            [contains(@href, "http")])[1]/@href'''))
    return parse_info #возвращаем словарь с данными


# парсинг dzen.ru
# так как сайт защищен от парсинга при отправке запроса будем использовать специальный параметр для обхода ограничений
# {'sso_failed': 'error'}:
def parse_dzen():
    # формируем запрос:
    response_dzen = requests.get(url='https://dzen.ru', headers=headers, params={'sso_failed': 'error'})
    # получаем объектную модель главной страницы сайта:
    dom_dzen = html.fromstring(response_dzen.text)
    # создаем струкиру данных и сохраняем в нее ссылки по главным новостям сайта и сохраняем в нее ссылки по
    # главным новостям сайта и заголовки новостей:
    parse_info_dzen = {'source': [], 'title': dom_dzen.xpath('''//span[contains(@class, 'news-story')]/text()[1]'''),
                       'href': dom_dzen.xpath('''//a[contains(@class, 'news-story')]/@href'''), 'ann_date': []}
    # для получения остальных данных нужно дополнительно пропарсить страницы с новостями
    for url in parse_info_dzen['href']:
        # формируем запрос, также применяя параметр - {'sso_failed': 'error'}:
        sub_response_dzen = requests.get(url=url, headers=headers, params={'sso_failed': 'error'})
        # получаем объектную модель главной страницы сайта:
        sub_dom_dzen = html.fromstring(sub_response_dzen.text)
        parse_info_dzen['source'].append(sub_dom_dzen.xpath('''(//article//a)[1]/@href'''))
        parse_info_dzen['ann_date'].append(sub_dom_dzen.xpath('''//div[contains(@class, 'source')]/div[2]//span
        [contains(@class, 'time')]/text()'''))
    return parse_info_dzen #возвращаем словарь с данными


choice = int(input('1 - parse lenta.ru\n2 - parse dzen.ru\n')) #запрос параметра для дальнейшей работы программы
if choice == 1:
    df = pd.DataFrame(parse_lenta())
    df.to_excel('lenta.xlsx') #записываем результат в стандартный эксель файл
    print('result file is in current dyrectory')
elif choice == 2:
    df = pd.DataFrame(parse_dzen())
    df.to_excel('dzen.xlsx') #записываем результат в стандартный эксель файл
    print('result file is in current dyrectory')
else:
    print('wrong input\n buy!') #сообщение о неверном вводе параметра программы
