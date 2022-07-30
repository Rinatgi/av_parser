import datetime
import time
import urllib.request
import psycopg2
from psycopg2.extras import RealDictCursor
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from seleniumwire import webdriver
from setting import PATH_IMAGE_CATALOG, DB_NAME, USER, PASSWORD, DEFAULT_IMAGE_PATH
import sys


class SubProcess:
    def __init__(self):
        self.connection = psycopg2.connect(dbname=DB_NAME, user=USER, password=PASSWORD)
        self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)
        self.categories_name = sys.argv[1].split(',')
        self.date_today = datetime.date.today()
        self.browser = webdriver.Chrome()
        self.transfer_data_select_category()

    def transfer_data_select_category(self):

        self.cursor.execute("SELECT * FROM select_category")
        categories_data = self.cursor.fetchall()
        for category_name in self.categories_name[1:]:
            for category_data in categories_data:
                if category_data['name_select_category'] == category_name:
                    category_url = category_data['link_select_category']
                    category_id = category_data['id_select_category']
                    if category_data['marker_category'] == 'directory':
                        self.parser_product(category_url, directory_id=category_id)
                    else:
                        self.parser_product(category_url, subdirectory_id=category_id)
                else:
                    continue

    def parser_product(self, url, directory_id=None, subdirectory_id=None):
        self.browser.get(url)
        count = 0
        if count < 10:
            product_write_list = []
            products = self.browser.find_elements(By.CSS_SELECTOR, 'div[data-marker="item"]')
            for product in products:
                name_product = product.find_element(By.CSS_SELECTOR, 'a[itemprop="url"]')
                id_product_site = product.get_attribute('data-item-id')
                name = name_product.get_attribute('title')
                price_product = product.find_element(By.CSS_SELECTOR, 'span[data-marker="item-price"]')
                price = price_product.find_element(
                    By.CSS_SELECTOR, 'meta[itemprop="price"]').get_attribute('content')
                currency = price_product.find_element(
                    By.CSS_SELECTOR, 'meta[itemprop="priceCurrency"]').get_attribute('content')
                request_product = self.cursor.execute(
                    "SELECT product_id, name_product FROM products WHERE id_site=%s LIMIT 1", (id_product_site,))

                if not request_product:
                    link = name_product.get_attribute('href')
                    time.sleep(5)
                    name_product.click()
                    self.go_to_product_page()
                    self.browser.implicitly_wait(10)
                    comment = self.parser_product_page()
                    image_path = self.save_image_product(self.browser)
                    self.browser.close()
                    self.return_main_page()
                    product_price = {'price': price,
                                     'currency': currency,
                                     'date': self.date_today}
                    product_data = {"name": name,
                                    "id_site": id_product_site,
                                    "link": link,
                                    "image": image_path,
                                    "comment": comment,
                                    "directory_id": directory_id,
                                    "subdirectory_id": subdirectory_id,
                                    "price": product_price
                                    }
                    product_write_list.append(product_data)
                else:
                    product_price = self.cursor.execute(
                        "SELECT price, fk_product_id FROM price_products WHERE fk_product_id=%s",
                        (request_product['product_id'],)
                    )
                    price_list = [price['price'] for price in product_price]
                    if price not in price_list:
                        self.save_data_price(price, currency, request_product['product_id'])
            self.save_data_product(product_write_list)
            try:
                next_page = WebDriverWait(self.browser, 10).until(
                    expected_conditions.element_to_be_clickable(
                        (By.CSS_SELECTOR, 'span[data-marker="pagination-button/next"]'))
                )

            except TimeoutException:
                count = 11
            else:
                next_page.click()
                count += 1
        self.browser.close()
        self.close_data_base()

    def close_data_base(self):
        self.cursor.close()
        self.connection.close()

    def save_image_product(self, driver):
        try:
            image = WebDriverWait(driver, 15).until(
                expected_conditions.presence_of_element_located((By.CSS_SELECTOR, 'img[class^="css"]'))
            )
            image_link = image.get_attribute('src')
            image = urllib.request.urlopen(image_link)
            time_now = str(time.time())
            image_path = PATH_IMAGE_CATALOG + time_now + '.jpg'
            with open(image_path, 'wb') as handler:
                handler.write(image.read())
            return image_path
        except TimeoutException:
            return DEFAULT_IMAGE_PATH

    def save_data_price(self, price, currency, product_id):
        try:
            price = int(price)
        except ValueError:
            price = 0

        dict_price = {
            'price': price,
            'currency': currency,
            'date': self.date_today,
            'product_id': product_id
        }
        self.cursor.execute(
            """
                INSERT INTO price_products(price, currency, date_price, fk_product_id)
                VALUES(%(price)s, %(currency)s, %(date)s, %(product_id)s)
            """, dict_price)
        self.connection.commit()

    def save_data_product(self, write_products_list):
        for product_data in write_products_list:
            self.cursor.execute(
                """
                    INSERT INTO products(
                    name_product, link_product, image_path, description, id_site , fk_directory_id, fk_subdirectory_id)
                    VALUES(%(name)s, %(link)s, %(image)s, %(comment)s, %(id_site)s, %(directory_id)s, %(subdirectory_id)s) 
                    RETURNING product_id
                """, product_data
            )

            self.connection.commit()
            product_id = self.cursor.fetchone()
            product_price = product_data['price']
            price, currency = product_price['price'], product_price['currency']
            self.save_data_price(price, currency, product_id['product_id'])

    def go_to_product_page(self):
        self.browser.switch_to.window(self.browser.window_handles[1])

    def return_main_page(self):
        self.browser.switch_to.window(self.browser.window_handles[0])

    def parser_product_page(self):
        comment = self.browser.find_element(By.CSS_SELECTOR, 'div[itemprop="description"]').text
        return comment


process = SubProcess()
