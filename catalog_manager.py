from setting import DB_NAME, USER, PASSWORD
import psycopg2


class CatalogManager:
    def __init__(self):
        self.connection = psycopg2.connect(dbname=DB_NAME, user=USER, password=PASSWORD)
        self.cursor = self.connection.cursor()
        self.tree_catalog = {'name': 'Каталог'}

    def get_catalog_list(self):
        self.cursor.execute(
            """
                SELECT * FROM main_catalog
            """
        )
        main_catalog = self.cursor.fetchall()
        if main_catalog is None:
            return []
        else:
            parent_catalog_list = []
            self.cursor.execute("SELECT * FROM main_catalog WHERE parent_id IS NULL")
            parent_catalogs = self.cursor.fetchall()
            for parent_catalog in parent_catalogs:
                catalog_list = []
                parent_id = parent_catalog[0]
                self.cursor.execute(

                        "SELECT * FROM main_catalog WHERE parent_id = %s", (parent_id,)
                )
                catalogs = self.cursor.fetchall()
                for catalog in catalogs:
                    directory_list = []
                    catalog_id = catalog[0]
                    self.cursor.execute("SELECT * FROM directories WHERE fk_catalog_id = %s", (catalog_id,))
                    directories = self.cursor.fetchall()
                    for directory in directories:
                        subdirectory_list = []
                        id_directory = directory[0]
                        self.cursor.execute("SELECT * FROM subdirectories WHERE fk_directory_id = %s", (id_directory,))
                        subdirectories = self.cursor.fetchall()
                        for subdirectory in subdirectories:
                            subdirectory_dict = {'name': subdirectory[1], 'children': []}
                            subdirectory_list.append(subdirectory_dict)
                        directory_dict = {'name': directory[1], 'children': subdirectory_list}
                        directory_list.append(directory_dict)
                    catalog_dict = {'name': catalog[1], 'children': directory_list}
                    catalog_list.append(catalog_dict)
                parent_catalog_dict = {'name': parent_catalog[1], 'children': catalog_list}
                parent_catalog_list.append(parent_catalog_dict)

        return parent_catalog_list
