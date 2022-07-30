from kivy.app import App
from widgets import MainScreen


class MainApp(App):
    def __init__(self, catalog_manager, parser):
        super().__init__()
        self.catalog_manager = catalog_manager
        self.parser = parser

    def build(self):
        return MainScreen(catalog_manager=self.catalog_manager, parser=self.parser)

