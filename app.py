from widget_ui import MainApp
from catalog_manager import CatalogManager
from parser_ui import Parser


class Application:
    def __init__(self):
        self.catalog_manager = CatalogManager()
        self.parser = Parser()
        self.main_window = MainApp(catalog_manager=self.catalog_manager, parser=self.parser)

    def start(self):
        """
        """
        self.main_window.run()