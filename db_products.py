from psycopg2.extras import RealDictCursor
from setting import DB_NAME, PASSWORD, USER
import psycopg2


class ProductManager:
    def __init__(self):
        self.connection = psycopg2.connect(dbname=DB_NAME, user=USER, password=PASSWORD)
        self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)

    def get_products_name_list(self, category_id, marker):
        if marker == 'directory':
            self.cursor.execute(
                "SELECT name_product FROM products WHERE fk_directory_id=%s", (category_id,)
            )
            products_name = self.cursor.fetchall()
        else:
            self.cursor.execute(
                "SELECT name_product FROM products WHERE fk_subdirectory_id=%s", (category_id,)
            )
            products_name = self.cursor.fetchall()
        for product_name in products_name:
            yield product_name['name_product']

    def get_product_info(self, product_name):
        self.cursor.execute("SELECT * FROM products WHERE name_product=%s LIMIT 1", (product_name,))
        product_info = self.cursor.fetchone()
        return product_info

    def get_price_product(self, product_id):
        self.cursor.execute("SELECT * FROM price_products WHERE fk_product_id=%s", (product_id,))
        price_list = self.cursor.fetchall()
        return price_list
