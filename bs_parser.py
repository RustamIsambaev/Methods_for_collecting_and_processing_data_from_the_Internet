"""
Данная программа производит парсинг по вакансиям на сайтах hh.ru или superjob.ru на выбор.
Можно запустить парсинг со значениями по умолчанию.
Результат работы программы структура данных состоящая из следующих полей:
1) Наименование вакансии
2) Минимальная заработная плата
3) Максимальная заработная плата
4) Валюта заработной платы
5) Ссылка на вакансию
6) Ссылка на источник (сайт работодателя)
После успешного парсинга в текущей директории будет сохранен файл - *.csv с результатом ее работы.
(в случае возникновения ошибки для получения результата следует повторно перезапустить программу)
Для корректной работы программы необходимо наличие установленных библиотек:
1) requests
2) re
3) pandas
4) bs4
"""

import requests
import re
import pandas as pd
from bs4 import BeautifulSoup as bs


def hh_parse(position):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
                AppleWebKit/537.36 (KHTML, like Gecko) \
                Chrome/110.0.0.0 Safari/537.36'}
    url = 'https://hh.ru/search/vacancy'

    # инициализируем структуру данных
    parse_info = {'vacance_name': [],
                  'salary_min': [],
                  'salary_max': [],
                  'salary_curr': [],
                  'href': [],
                  'source': []}
    # установим счетчик страниц на старт
    page = 0
    # основной цикл перебора страниц со списками вакансий
    while True:
        # если страница стартовая, то в параметрах номер страницы не указываем
        # иначе укажем номер страницы чтобы получить следующую
        if page == 0:
            params = {'text': position,
                      'from': 'suggest_post',
                      'area': None}
        else:
            params = {'text': position,
                      'from': 'suggest_post',
                      'area': None,
                      'page': str(page)}
        # сам запрос на получение страницы со списком вакансий
        response = requests.get(url=url, headers=headers, params=params)
        # если такой не существует то прекращаем перелистывать сайт
        if response.status_code != 200:
            break
        # формируем объектную модель документа (далее ОМД)
        # и находим разделы с вакансиями
        soup = bs(response.content, 'html.parser')
        tags = soup.find_all('div', attrs={'class': 'serp-item'})
        # если не найдено ни одного раздела с вакансиями,
        # то прекращаем перелистывать сайт
        if len(tags) == 0:
            break
        # выведем текущее состояние парсинга
        print(f'страница {page + 1}, количество {len(tags)}')
        # цикл поиска значений по каждому элементу из списка разделов с вакансиями
        for tag in tags:
            # поиск тега содержащего ссылку - в данном случае первый попавшийся
            # тег будет содержать нужную ссылку на страницу
            # с подробным описанием вакансии
            a = tag.find('a')
            # записываем наименование и ссылку на вакансию
            parse_info['vacance_name'].append(a.text)
            parse_info['href'].append(a['href'])
            # запрашиваем страницу с подробным описанием вакансии для поиска
            # информации о работодателе и формируем ОМД
            sub_response = requests.get(url=a['href'], headers=headers)
            sub_soup = bs(sub_response.content, 'html.parser')
            # объявляем поиск ссылок на страницу
            # содержащую информацию о работодателе
            sub_a = sub_soup.find('a', attrs={'data-qa': re.compile('vacancy-company')})
            # установим значение тега ссылки на сайт работодателя по умолчанию пустым
            source_company_href = None
            # при наличии тега содержащего ссылку на страницу с информацией
            # о работодателе запрашиваем эту страницу, формируем ее ОМД и
            # проводим поиск тега с ссылкой на сайт работодателя
            if sub_a:
                href = 'https://hh.ru' + str(sub_a['href'])
                sub_sub_response = requests.get(url=href, headers=headers)
                sub_sub_soup = bs(sub_sub_response.content, 'html.parser')
                source_company_href = sub_sub_soup.find('a', attrs={'data-qa': re.compile('company-site')})
            # в случае успеха записываем найденную ссылку
            # в структуру данных как источник иначе записываем пустое значение
            if source_company_href:
                parse_info['source'].append(source_company_href['href'])
            else:
                parse_info['source'].append(source_company_href)
            # объявляем поиск тегов содержащих информацию о заработной плате
            salary_info = tag.find('span', attrs={'data-qa': re.compile('compensation')})
            # в случае успеха обрабатываем данные и записываем их в структуру
            # иначе указываем пустые значения
            if salary_info:
                salary_data = re.sub(r'\b\u202f\b', '', salary_info.text, flags=re.IGNORECASE)
                pos = -1
                for char in reversed(salary_data):
                    if char.isdigit():
                        break
                    pos -= 1
                salary_interval = salary_data[:pos + 1].split(' – ')
                parse_info['salary_curr'].append(salary_data[pos + 1:])
                # в случае наличия только одной границы интервала заработной платы
                # указываем в структуре одну границу пустой,
                # а другую с имеющимся значением
                if len(salary_interval) == 1:
                    if salary_interval[0][:2] == 'от':
                        parse_info['salary_min'].append(int(salary_interval[0][3:]))
                        parse_info['salary_max'].append(None)
                    else:
                        parse_info['salary_min'].append(None)
                        parse_info['salary_max'].append(int(salary_interval[0][3:]))
                else:
                    parse_info['salary_min'].append(int(salary_interval[0]))
                    parse_info['salary_max'].append(int(salary_interval[1]))
            else:
                parse_info['salary_min'].append(None)
                parse_info['salary_max'].append(None)
                parse_info['salary_curr'].append(None)
        # увеличение значения счетчика страниц сайта на 1: перелистываем сайт
        page += 1
    return parse_info


def sj_parse(position):
    # объявляем заголовки, адрес для запроса основной
    # страницы сайта и структуру данных
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
                AppleWebKit/537.36 (KHTML, like Gecko) \
                Chrome/110.0.0.0 Safari/537.36'}
    url = 'https://www.superjob.ru/vacancy/search'
    parse_info = {'vacance_name': [],
                  'salary_min': [],
                  'salary_max': [],
                  'salary_curr': [],
                  'href': [],
                  'source': []}
    # установим счетчик страниц на старт
    page = 1
    # основной цикл перебора страниц со списками вакансий
    while True:
        # если страница стартовая, то в параметрах номер страницы не указываем
        # иначе укажем номер страницы чтобы получить следующую
        if page == 1:
            params = {'noGeo': '1',
                      'keywords': position}
        else:
            params = {'noGeo': '1',
                      'keywords': position,
                      'page': str(page)}
        # сам запрос на получение страницы со списком вакансий
        response = requests.get(url=url, headers=headers, params=params)
        # если такой не существует то прекращаем перелистывать сайт
        if response.status_code != 200:
            break
        # формируем объектную модель документа (далее ОМД)
        # и находим разделы с вакансиями
        soup = bs(response.content, 'html.parser')
        tags = soup.find_all('div', attrs={'class': 'f-test-search-result-item'})
        # если не найдено ни одного раздела с вакансиями,
        # то прекращаем перелистывать сайт
        if len(tags) == 0:
            break
        # выведем текущее состояние парсинга
        print(f'страница {page}, количество {len(tags)}')
        # цикл поиска значений по каждому элементу из списка разделов с вакансиями
        for tag in tags:
            check_for_adv = tag.find('button', attrs={'class': re.compile('button-more_vert')})
            if check_for_adv:
                # поиск тега содержащего ссылку - в данном случае первый попавшийся
                # тег будет содержать нужную ссылку на страницу
                # с подробным описанием вакансии
                a = tag.find('a')
                # записываем наименование и ссылку на вакансию
                parse_info['vacance_name'].append(a.text)
                parse_info['href'].append('https://www.superjob.ru' + a['href'])
                # запрашиваем страницу с подробным описанием вакансии для поиска
                # информации о работодателе и формируем ОМД
                sub_response = requests.get(url='https://www.superjob.ru' + a['href'], headers=headers)
                sub_soup = bs(sub_response.content, 'html.parser')
                # объявляем поиск раздела с ссылкой на страницу
                # содержащую информацию о работодателе
                sub_div = sub_soup.find('div', attrs={'class': re.compile('vacancy')})
                # установим значение тега ссылки на сайт работодателя по умолчанию пустым
                source_company_href = None
                # если раздел найден пробуем найти тег содержащий ссылку
                if sub_div:
                    sub_a = sub_div.find('a', attrs={'href': re.compile('clients')})
                    # если тег найден переходим по ссылке на страницу с информацией
                    # о работодателе формируем ОМД страницы и ищем заголовок
                    # указывающий на данные сатйа работодателя
                    if sub_a:
                        href = 'https://www.superjob.ru' + sub_a['href']
                        sub_sub_response = requests.get(url=href, headers=headers)
                        sub_sub_soup = bs(sub_sub_response.content, 'html.parser')
                        sub_sub_h = sub_sub_soup.find('h2', string='Сайт и соцсети')
                        # если искомый заголовок найден, то переходим к
                        # родителльскому разделу и далее переходим на следующий
                        # тег в котором уже содержится сама ссылка на сайт компании
                        if sub_sub_h:
                            sub_sub_a = sub_sub_h.parent.next_sibling.find('a')
                            # если тег найден меняем пустое значение на информацию
                            # о ссылке сайта работодателя
                            if sub_sub_a:
                                source_company_href = sub_sub_a['href']
                # записыаем значение переменно с информацией о сайте работодателя
                # в структуру (если данных о сайте не имеется то запишется пустое
                # значение)
                parse_info['source'].append(source_company_href)
            # объявляем поиск тегов содержащих информацию о заработной плате
            salary_info = tag.find('div', attrs={'class': re.compile('salary')})
            # в случае успеха обрабатываем данные и записываем их в структуру
            # иначе указываем пустые значения
            if salary_info:
                salary_data = re.sub(r'\xa0', '', salary_info.text, flags=re.IGNORECASE)
                pos = -1
                for char in reversed(salary_data):
                    if char.isdigit():
                        break
                    pos -= 1
                salary_interval = salary_data[: pos + 1].split('—')
                salary_curr = salary_data[pos + 1:salary_data.find('/')]
                # если длина строки меньше 5 символов запишем название валюты
                if len(salary_curr) < 5:
                    parse_info['salary_curr'].append(salary_curr)
                else:
                    parse_info['salary_curr'].append(None)
                # в случае наличия только одной границы интервала заработной платы
                # указываем в структуре одну границу пустой,
                # а другую с имеющимся значением
                if len(salary_interval) == 1:
                    if salary_interval[0][:2] == 'от':
                        parse_info['salary_min'].append(int(salary_interval[0][2:]))
                        parse_info['salary_max'].append(None)
                    elif salary_interval[0][:2] == 'до':
                        parse_info['salary_min'].append(None)
                        parse_info['salary_max'].append(int(salary_interval[0][2:]))
                    else:
                        parse_info['salary_min'].append(None)
                        parse_info['salary_max'].append(None)
                else:
                    parse_info['salary_min'].append(int(salary_interval[0]))
                    parse_info['salary_max'].append(int(salary_interval[1]))
        # увеличение значения счетчика страниц сайта на 1: перелистываем сайт
        page += 1
    return parse_info


choice = int(input('1 - parse hh.ru\n2 - parse superjob.ru\n'))  # запрос параметра для дальнейшей работы программы
if choice == 1:
    mode = int(input('1 - parse predefined position - Data scientist\n2 - parse custom position\n'))
    if mode == 1:
        df = pd.DataFrame(hh_parse('Data scientist'))
        df.to_csv('hh_ds.csv')  # записываем результат в csv файл
        print('result file is in current dyrectory')
    elif mode == 2:
        df = pd.DataFrame(hh_parse(input('input position name: ')))
        df.to_csv('hh_custom.csv')  # записываем результат в csv файл
        print('result file is in current dyrectory')
    else:
        print('wrong input\n buy!')
elif choice == 2:
    mode = int(input('1 - parse predefined position - Программист АСУ ТП\n2 - parse custom position\n'))
    if mode == 1:
        df = pd.DataFrame(sj_parse('Программист АСУ ТП'))
        df.to_csv('sj_pr.csv')  # записываем результат в csv файл
        print('result file is in current dyrectory')
    elif mode == 2:
        df = pd.DataFrame(sj_parse(input('input position name: ')))
        df.to_csv('sj_custom.csv')  # записываем результат в csv файл
        print('result file is in current dyrectory')
    else:
        print('wrong input\n buy!')
else:
    print('wrong input\n buy!')  # сообщение о неверном вводе параметра программы
