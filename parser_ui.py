from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.select import Select
import psycopg2
from setting import DB_NAME, USER, PASSWORD, URL


class Parser:

    def __init__(self):
        self.connection = psycopg2.connect(dbname=DB_NAME, user=USER, password=PASSWORD)
        self.cursor = self.connection.cursor()

    def get_menu_list(self):
        """
            получем каталог наших товаров для базы данных
        """
        browser = webdriver.Chrome()
        url = URL
        browser.implicitly_wait(20)
        browser.get(url)
        browser.refresh()
        menu = browser.find_element(By.CSS_SELECTOR, "select[name='category_id']")
        select_object = Select(menu)
        """ получаем все элементы меню поиска сайта """
        all_available_options = select_object.options
        category_list = [option.text for option in all_available_options]
        """переходим на страницу каждой категории для получения дополнительных категорий товаров """
        for parent_category in category_list[1:]:
            if parent_category.isupper():
                select_object.select_by_visible_text(parent_category.capitalize())
                parent = browser.find_element(By.LINK_TEXT, parent_category.capitalize())
                link_parent_category = parent.get_attribute('href')
                self.cursor.execute(
                    """
                        INSERT INTO main_catalog(name_catalog, link_catalog) VALUES(%s, %s) RETURNING catalog_id;           
                    """, (parent_category, link_parent_category)
                                    )
                parent_id = self.cursor.fetchone()[0]
                self.connection.commit()
                # после обновления страницы ищем заново наш список
                menu = browser.find_element(By.CSS_SELECTOR, "select[name='category_id']")
                select_object = Select(menu)
                # ищем id для поиска
                id_parent_category = menu.find_element(By.CSS_SELECTOR, 'option[selected]').get_attribute('value')
                main_marker = browser.find_element(
                    By.CSS_SELECTOR,
                    "a[data-category-id='{0}']".format(id_parent_category)).get_attribute('data-marker')
                marker_category = main_marker[:-7] + 'subs'
                submenu_category = browser.find_element(
                    By.CSS_SELECTOR, 'ul[data-marker="{0}"]'.format(marker_category))
                categories_menu = submenu_category.find_elements(By.CSS_SELECTOR,
                                                                 'li[class^="rubricator-list-item-item"]'
                                                                 )
                for category_menu in categories_menu:
                    category = category_menu.find_element(By.CSS_SELECTOR, 'a[class^="rubricator-list-item-link"]')
                    name_category = category.get_attribute('title')
                    if name_category in category_list:
                        link_category = category.get_attribute('href')
                        id_category = category.get_attribute('data-category-id')
                        category_marker = category.get_attribute('data-marker')
                        directory_marker = category_marker[:-4] + 'subs'
                        dict_category = {'name_category': name_category,
                                         'link_category': link_category,
                                         'parent_id': parent_id
                                         }
                        self.cursor.execute(
                            """ 
                                INSERT INTO main_catalog(name_catalog, link_catalog, parent_id)
                                VALUES(%(name_category)s, %(link_category)s, %(parent_id)s) RETURNING catalog_id;    
                            """, dict_category
                        )
                        catalog_id = self.cursor.fetchone()[0]
                        self.connection.commit()
                        submenu_directories = category_menu.find_element(
                            By.CSS_SELECTOR, 'ul[data-marker="{0}"]'.format(directory_marker))
                        directories = submenu_directories.find_elements(
                            By.CSS_SELECTOR, "a[data-category-id='{0}']".format(id_category))
                        if directories:
                            for directory in directories:
                                name_directory = directory.get_attribute('title')
                                self.cursor.execute("SELECT name_subdirectory FROM subdirectories")
                                subdirectories_name_list = [name[0] for name in self.cursor.fetchall()]
                                if name_directory not in subdirectories_name_list:
                                    link_directory = directory.get_attribute('href')
                                    marker_directory = directory.get_attribute('data-marker')
                                    marker_subdirectory = marker_directory[:-4] + 'subs'
                                    dict_directory = {'name_directory': name_directory,
                                                      'link_directory': link_directory,
                                                      'catalog_id': catalog_id
                                                      }
                                    self.cursor.execute(
                                        """ 
                                            INSERT INTO directories(name_directory, link_directory, fk_catalog_id)
                                            VALUES(%(name_directory)s, %(link_directory)s, %(catalog_id)s) 
                                            RETURNING directory_id;    
                                        """, dict_directory
                                    )
                                    self.connection.commit()
                                    directory_id = self.cursor.fetchone()[0]
                                    try:
                                        submenu = browser.find_element(
                                            By.CSS_SELECTOR, 'ul[data-marker="{0}"]'.format(marker_subdirectory)
                                        )
                                        subdirectories = submenu.find_elements(
                                            By.CSS_SELECTOR, "a[data-category-id='{0}']".format(id_category)
                                        )
                                        for subdirectory in subdirectories:
                                            name_subdirectory = subdirectory.get_attribute('title')
                                            link_subdirectories = subdirectory.get_attribute('href')
                                            dict_subdirectory = {
                                                "name": name_subdirectory,
                                                "link": link_subdirectories,
                                                "directory_id": directory_id
                                            }
                                            self.cursor.execute(
                                                """ 
                                                    INSERT INTO subdirectories(name_subdirectory, link_subdirectory, 
                                                    fk_directory_id)
                                                    VALUES(%(name)s, %(link)s, %(directory_id)s)     
                                                """, dict_subdirectory
                                            )
                                            self.connection.commit()
                                    except NoSuchElementException:
                                        continue
                        else:
                            try:
                                new_directories = browser.find_elements(By.CSS_SELECTOR,
                                                                        "a[data-category-id='{0}']".format(id_category))
                            except NoSuchElementException:
                                continue

                            for new_directory in new_directories:
                                name_directory = new_directory.get_attribute('title')
                                link_directory = new_directory.get_attribute('href')
                                # проверяем, чтобы главная категория не попала в таблицу категорий
                                self.cursor.execute("SELECT name_catalog FROM main_catalog WHERE name_catalog=%s",
                                                    (name_directory,))
                                row_catalog = self.cursor.fetchone()
                                if row_catalog is None:
                                    # проверяем на совпадение в таблице категорий уже имеющейся в базе записи.
                                    self.cursor.execute(
                                        "SELECT name_directory FROM directories WHERE name_directory=%s",
                                        (name_directory,)
                                    )
                                    row_directory = self.cursor.fetchone()
                                    # проверяем ,чтобы подкатегория не попала в таблицу категорий
                                    if row_directory is None:
                                        dict_directory = {'name_directory': name_directory,
                                                          'link_directory': link_directory,
                                                          'catalog_id': catalog_id
                                                          }
                                        self.cursor.execute(
                                            """ 
                                                INSERT INTO directories(name_directory, link_directory, fk_catalog_id)
                                                VALUES(%(name_directory)s, %(link_directory)s, %(catalog_id)s) 
                                                RETURNING directory_id;    
                                            """, dict_directory
                                        )
                                        self.connection.commit()

    def close_data_base(self):
        self.cursor.close()
        self.connection.close()
