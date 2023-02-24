"""
Данная программа производит парсинг по вакансиям на сайте hh.ru и сохраняет результаты в базу данных hh коллекцию hh_ru.
Так же в базу данных можно импортировать данные из файла *.csv.
Структура файла должна соответствовать файлу hh_custom_2.csv расположенному в одной директории с данным скриптом
Cтруктура данных состоbn из следующих полей:
1) Наименование вакансии
2) Минимальная заработная плата
3) Максимальная заработная плата
4) Валюта заработной платы
5) Ссылка на вакансию
6) Ссылка на источник (сайт работодателя) (а в случае отсутствия ссылки - наименование организации)
Для корректной работы программы требуется установленный сервер mongodb и необходимо наличие установленных библиотек:
1) requests
2) lxml
3) pandas
4) pymongo
5) pprint
"""

# импорт библиотек
import requests
import pandas as pd
from lxml import html
from pymongo import MongoClient
from pprint import pprint


# функция парсинга - возвращает данные в виде списка документов (словарей)
def parse(position, period):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
                    AppleWebKit/537.36 (KHTML, like Gecko) \
                    Chrome/110.0.0.0 Safari/537.36'}
    url = 'https://hh.ru/search/vacancy'
    data = []
    parse_info = {'vacancy_name': [],
                  'salary_min': [],
                  'salary_max': [],
                  'salary_curr': [],
                  'href': [],
                  'source': []}
    page = 0
    while True:
        if page == 0:
            params = {'text': position,
                      'search_period': str(period)}
        else:
            params = {'text': position,
                      'search_period': str(period),
                      'page': str(page)}
        response = requests.get(url=url, headers=headers, params=params)
        if response.status_code != 200:
            break
        dom = html.fromstring(response.text)
        vacancy_hrefs = dom.xpath('''//a[contains(@data-qa, 'serp-item')]/@href''')
        if len(vacancy_hrefs) == 0:
            break
        print(f'страница {page + 1}, количество {len(vacancy_hrefs)}')
        for vacancy_href in vacancy_hrefs:
            parse_info['href'] = vacancy_href
            sub_response = requests.get(url=vacancy_href, headers=headers)
            sub_dom = html.fromstring(sub_response.text)
            parse_info['vacancy_name'] = sub_dom.xpath('''//*[@data-qa='vacancy-title']/text()''')[0]
            salary_info = sub_dom.xpath('''//span[contains(@data-qa, 'salary')]/text()''')
            if len(salary_info) == 6:
                parse_info['salary_min'] = int(salary_info[1].replace('\xa0', ''))
                parse_info['salary_max'] = int(salary_info[3].replace('\xa0', ''))
                parse_info['salary_curr'] = salary_info[5]
            elif len(salary_info) == 4:
                if salary_info[0] == 'от ':
                    parse_info['salary_min'] = int(salary_info[1].replace('\xa0', ''))
                    parse_info['salary_max'] = None
                elif salary_info[0] == 'до ':
                    parse_info['salary_max'] = int(salary_info[1].replace('\xa0', ''))
                    parse_info['salary_min'] = None
                parse_info['salary_curr'] = salary_info[3]
            else:
                parse_info['salary_min'] = None
                parse_info['salary_max'] = None
                parse_info['salary_curr'] = None
            employer_info = sub_dom.xpath('''(//a[contains(@data-qa, 'vacancy-company')]/@href)[1]''')
            if len(employer_info) != 0:
                parse_info['source'] = ''.join(
                    sub_dom.xpath('''(//a[contains(@data-qa, 'vacancy-company')])[1]//span/text()'''))
                employer_href = 'https://hh.ru' + sub_dom.xpath('''(//a[contains(@data-qa, 
                'vacancy-company')]/@href)[1]''')[0]
                sub_sub_response = requests.get(url=employer_href, headers=headers)
                sub_sub_dom = html.fromstring(sub_sub_response.text)
                company_site_info = sub_sub_dom.xpath('''//a[contains(@data-qa, 'company-site')]/@href''')
                if len(company_site_info) != 0:
                    parse_info['source'] = company_site_info[0]
            else:
                parse_info['source'] = None
            data.append(parse_info.copy())
        page += 1
    return data


# функция чтения данных из *.csv файла и преобразования их в список словарей
def read_from_file(file_name):
    try:
        # значения Nan заменены на "-" для корректного импорта данных
        data = pd.read_csv(file_name).drop('Unnamed: 0', axis=1).fillna('-').to_dict('records')
    except FileNotFoundError:
        data = []
        print('file is not found')
    except UnicodeDecodeError:
        data = []
        print('wrong data - must be *.csv')
    return data


# функция для сохранения информации в базу данных
# при импорте данных проводится контроль за их уникальностью
# при попытке импорта уже имеющихся данных программа осуществляет
# их вывод. это означает, что данные не были импортированы дважды
def save_to_db(data):
    client = MongoClient('mongodb://localhost:27017/')
    db = client.hh
    for i in data:
        if db.hh_ru.find_one({'vacancy_name': i['vacancy_name'], 'salary_min': i['salary_min'],
                              'salary_max': i['salary_max'], 'salary_curr': i['salary_curr'],
                              'href': i['href'], 'source': i['source']}) is not None:
            pprint(i)
        else:
            db.hh_ru.insert_one(i)


# функция для ввода документов по критерию не ниже заданного размера заработной платы
# если на вход подается нулевое значение то происходит вывод всех документов
def min_salary_rate(salary_min):
    client = MongoClient('mongodb://localhost:27017/')
    db = client.hh
    if salary_min == 0:
        for i in db.hh_ru.find():
            pprint(i)
    else:
        for i in db.hh_ru.find({'$or': [{'salary_min': {'$gt': salary_min}}, {'salary_max': {'$gt': salary_min}}]}):
            pprint(i)


# простейший интерфейс взаимодействия
choice = int(input('1 - import data from file\n2 - parse and import\n3 - find by min.salary rate\n'))
if choice == 1:
    save_to_db(read_from_file(input('enter file name: ')))
elif choice == 2:
    search_period = int(input('input search period\n0 - all time\n1 - last day\n3 - last thee days\n7 - last week\n30 '
                              '- last month\n: '))
    if search_period in [0, 1, 3, 7, 30]:
        save_to_db(parse(input('input position name: '), search_period))
    else:
        print('wrong input\n buy!')
elif choice == 3:
    min_salary_rate(int(input('enter min.salary: ')))
else:
    print('wrong input\n buy!')
