# использовался драйвер chrome версии 110

# импортируем библиотеки
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common import exceptions
from selenium.webdriver.common.action_chains import ActionChains
from pymongo import MongoClient
from datetime import date

# подключаемся к базе данных
client = MongoClient('mongodb://localhost:27017/')
db = client.avito

# инициализируем веб драйвер и отправляем запрос к сайту
service = Service('chromedriver.exe')
driver = webdriver.Chrome(service=service)
driver.maximize_window()
driver.get('https://www.avito.ru/')

# специальный счетчик для установки количества прокруток страницы в самый низ
# так как контент динамический то при прокрутке вниз он автоматически будет подгружаться
# начальное значение установим равным нулю
# в цикле укажем условие например на три итерации
i = 0
while i < 3:
    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
    i += 1
# после объявляем поиск нужного нам контента с объявлениями по всей странице
announces = driver.find_elements(By.XPATH, "//div[contains(@data-marker, 'block-item')]")
# этот объект предназначен для низкоуровневого контроля над действиями на странице
# в нашем случае мы сдвигаем указатель мыши в центр каждого тега с объявленем
# реакция страницы в таком случае будет динамическая загрузка всех изображений связанных с объявлением
action = ActionChains(driver)
# пробежимся по всем найденным объявлениям
for announce in announces:
    # для каждого отдельного объявления задаем запись в виде словаря
    # в начале цикла она пока пустая
    record = {}
    # сдвигаем указатель мыши на текущее объявление
    action.move_to_element(announce).perform()
    # пробуем найти изображения по текущему объявлению
    # в случае отстутствия изображений укажем их отсутствие в виде текста "no data"
    # в случае успеха сформируем список ссылок на изображения и запишем его в нашу
    # структуру данных record
    try:
        images = announce.find_elements(By.TAG_NAME, 'img')
        images_urls = []
        for image in images:
            images_urls.append(image.get_attribute('src'))
        record['images'] = images_urls
        # сохраним информацию об объявлении
        record['name'] = announce.text.split('\n')[1]
        record['price_info'] = announce.text.split('\n')[2]
        record['location'] = announce.text.split('\n')[3]
        record['date'] = announce.text.split('\n')[4].replace('Сегодня', str(date.today()))
    except exceptions.NoSuchElementException:
        record['images'] = ['no data']
    # записываем запись в базу данных
    db.announces.insert_one(record)
