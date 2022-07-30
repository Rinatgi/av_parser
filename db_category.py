import psycopg2
from psycopg2.extras import RealDictCursor

from setting import DB_NAME, USER, PASSWORD


class CategoryManager:

    def __init__(self):
        self.connection = psycopg2.connect(dbname=DB_NAME, user=USER, password=PASSWORD)
        self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)

    def check_select_categories(self, category_name):
        self.cursor.execute(
            "SELECT name_select_category FROM select_category WHERE name_select_category=%s LIMIT 1",
            (category_name,)
        )
        category = self.cursor.fetchone()
        if category is None:
            self.search_data_select_category(category_name)

    def search_data_select_category(self, category_name):
        self.cursor.execute(
            "SELECT directory_id, name_directory, link_directory FROM directories WHERE name_directory=%s",
            (category_name,))
        directory = self.cursor.fetchone()
        if directory is None:
            self.cursor.execute(
                """
                    SELECT subdirectory_id, name_subdirectory, link_subdirectory FROM subdirectories 
                    WHERE name_subdirectory=%s
                """, (category_name,))
            subdirectory = self.cursor.fetchone()
            subdirectory_data_list = [subdirectory['subdirectory_id'],
                                      subdirectory['name_subdirectory'],
                                      subdirectory['link_subdirectory']
                                      ]
            self.save_select_category(subdirectory_data_list, marker="subdirectory")

        else:
            directory_data_list = [directory['directory_id'],
                                   directory['name_directory'],
                                   directory['link_directory']
                                   ]
            self.save_select_category(directory_data_list, marker="directory")

    def save_select_category(self, category_data_list, marker=None):
        self.cursor.execute(
            """
               INSERT INTO select_category(id_select_category, name_select_category, link_select_category, marker_category)
               VALUES (%s, %s, %s, %s);
               """, (category_data_list[0], category_data_list[1], category_data_list[2], marker))
        self.connection.commit()

    def delete_select_category(self, name):
        self.cursor.execute("DELETE FROM select_category WHERE name_select_category=%s", (name,))
        self.connection.commit()

    def get_category_info(self, name_category):
        self.cursor.execute("SELECT * FROM directories WHERE name_directory=%s", (name_category,))
        directory_info = self.cursor.fetchone()
        if directory_info is None:
            self.cursor.execute("SELECT * From subdirectories name_subdirectory=%s", (name_category,))
            subdirectory_info = self.cursor.fetchone()
            if subdirectory_info is None:
                return []
            else:
                return subdirectory_info
        else:
            return directory_info

    def get_data_select_categories(self, categories_name):
        data_category_list = []
        for category_name in categories_name:
            self.cursor.execute(
                """
                    SELECT id_select_category, link_select_category FROM select_category 
                    WHERE name_select_category=%s
                """, (category_name,)
            )
            data_category = self.cursor.fetchone()
            data_category_list.append(data_category)

        return data_category_list

    def get_select_category_id(self, category_name):
        self.cursor.execute(
            """
                SELECT id_select_category, marker_category FROM select_category WHERE name_select_category=%s LIMIT 1
            """, (category_name,))
        category_row = self.cursor.fetchone()
        if category_row is not None:
            return category_row['id_select_category'], category_row['marker_category']

    def get_select_category_name_list(self):
        self.cursor.execute(
            "SELECT name_select_category FROM select_category"
        )
        name_list = [name['name_select_category'] for name in self.cursor.fetchall()]
        return name_list
