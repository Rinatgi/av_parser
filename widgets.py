import subprocess
import sys
import webbrowser
from timeit import default_timer as timer
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.recycleview import RecycleView
from kivy.uix.treeview import TreeView, TreeViewLabel
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen, ScreenManager
from db_category import CategoryManager
from db_products import ProductManager


class ProductScreen(Screen):
    def __init__(self, catalog_manager, parser):
        super().__init__()
        self.name = 'avito'
        self.parser = parser
        self.node = {'name': 'Каталог'}
        self.catalog_manager = catalog_manager
        self.category_manager = CategoryManager()
        self.select_category_name_list = self.category_manager.get_select_category_name_list()
        self.product_manager = ProductManager()
        if not self.catalog_manager.get_catalog_list():
            self.parser.get_menu_list()
        else:
            catalog_list = self.catalog_manager.get_catalog_list()
            self.node['children'] = catalog_list
            self.__create_widgets()
            self.__place_widgets()

    def __create_widgets(self):
        self.top_layout = GridLayout(cols=4, spacing=10,
                                     col_force_default=False,
                                     row_force_default=True,
                                     col_default_width=300,
                                     row_default_height=500
                                     )

        self.button_layout = BoxLayout(orientation='horizontal')
        self.info_top_layout = GridLayout(rows=3)
        self.info_layout = GridLayout(rows=6,
                                      minimum_height=20,
                                      row_force_default=True,
                                      row_default_height=100
                                      )
        self.price_layout = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.button_parsing_products = Button(text='Спарсить товары',
                                              font_size=12,
                                              on_release=self.start_parsing,
                                              size_hint_y=None,
                                              height=40
                                              )
        self.button_delete_category = Button(text='Удалить категорию',
                                             font_size=12,
                                             on_release=self.delete_node,
                                             size_hint_y=None,
                                             height=40
                                             )
        self.back_main_menu = Button(text='Назад на главное меню',
                                     font_size=12,
                                     on_release=self.add_node,
                                     size_hint_y=None,
                                     height=40
                                     )
        self.button_parsing_process = Button(text='Статус процесса',
                                             font_size=12,
                                             on_release=self.add_node,
                                             size_hint_y=None,
                                             height=40
                                             )
        self.category_view = CatalogView(text='Авито каталог')
        self.category_view.select_handler = self.add_select_category
        self.select_category_view = ProductView(text='Выбранные категории')
        self.select_category_view.select_handler = self.show_product_list
        self.products_view = ProductView(text='Список товаров')
        self.products_view.select_handler = self.show_info_product
        self.scroll_main_catalog = ScrollView(size_hint=(1, 0.5),
                                              size=(self.top_layout.width, self.top_layout.height),
                                              scroll_type=['bars', 'content'])
        self.scroll_select_category = ScrollView(size_hint=(1, 0.8),
                                                 size=(self.top_layout.width, self.top_layout.height),
                                                 scroll_type=['bars', 'content']
                                                 )
        self.scroll_product = ScrollView(size_hint=(1, 1),
                                         size=(self.top_layout.width, self.top_layout.height),
                                         scroll_type=['bars', 'content']
                                         )

        self.price_root = RecycleView(size_hint=(1, 1),
                                      size=(self.info_top_layout.width,
                                            self.info_top_layout.height))
        self.select_category_view.bind(minimum_height=self.select_category_view.setter('height'))
        self.products_view.bind(minimum_height=self.products_view.setter('height'))
        self.category_view.bind(minimum_height=self.category_view.setter('height'))
        self.price_layout.bind(minimum_height=self.price_layout.setter('height'))
        self.label_info = Label(text='Информация о товаре',
                                size_hint_x=0.5,
                                size_hint_y=0.06,
                                width=100,
                                font_size=14)
        self.label_name_price = Label(text='Цена',
                                      font_size=12,
                                      size_hint_x=0.5,
                                      size_hint_y=0.1,
                                      height=50)
        self.product_link = Label(markup=True,
                                  font_size=12,
                                  text='[ref=some]Ссылка на товар[/ref]',
                                  size_hint_x=0.5,
                                  size_hint_y=0.1,
                                  height=50,
                                  on_ref_press=self.open_link_product
                                  )
        self.label_comment = Label(text='Описание товара',
                                   )
        self.product_comment = Label(font_size=12,
                                     size_hint_x=0.5,
                                     size_hint_y=0.1,
                                     height=50)
        self.image_product = Image()

    def add_node(self):
        pass

    def __place_widgets(self):
        self.add_widget(self.top_layout)
        self.add_widget(self.button_layout)
        self.top_layout.add_widget(self.scroll_main_catalog)
        self.top_layout.add_widget(self.scroll_select_category)
        self.top_layout.add_widget(self.scroll_product)
        self.top_layout.add_widget(self.info_top_layout)
        self.scroll_main_catalog.add_widget(self.category_view)
        self.scroll_select_category.add_widget(self.select_category_view)
        self.scroll_product.add_widget(self.products_view)
        self.info_top_layout.add_widget(self.info_layout)
        self.info_layout.add_widget(self.label_info)
        self.info_layout.add_widget(self.image_product)
        self.info_layout.add_widget(self.label_comment)
        self.info_layout.add_widget(self.product_comment)
        self.info_layout.add_widget(self.product_link)
        self.info_layout.add_widget(self.label_name_price)
        self.info_layout.add_widget(self.price_root)
        self.price_root.add_widget(self.price_layout)
        self.button_layout.add_widget(self.back_main_menu)
        self.button_layout.add_widget(self.button_parsing_products)
        self.button_layout.add_widget(self.button_parsing_process)
        self.button_layout.add_widget(self.button_delete_category)
        self.populate_tree_view(self.category_view, None, self.node)
        self.create_simple_tree(self.select_category_view, self.select_category_name_list)

    def create_simple_tree(self, tree_view, nodes):
        for node in nodes:
            tree_view.add_node(TreeViewLabel(text=node))

    def measure_time(func):
        def wrapper(*args, **kwargs):
            start = timer()
            func(*args, **kwargs)
            stop = timer()
            print(f"Function {func.__name__} took {stop - start} for execution")

        return wrapper

     #@measure_time
    def populate_tree_view(self, tree_view, parent, node):
        """
            создаем наш каталог товаров
        """
        if parent is None:
            tree_node = tree_view.add_node(TreeViewLabel(text=node['name'],
                                                         is_open=False))
        else:

            tree_node = tree_view.add_node(TreeViewLabel(text=node['name'],
                                                         is_open=False), parent)

        for child_node in node['children']:
            self.populate_tree_view(tree_view, tree_node, child_node)

    def add_select_category(self):
        """
            добавляем директорию в список поиска товаров
        """
        node = self.category_view.selected_node
        try:
            self.select_category_view.add_node(TreeViewLabel(text=node.text))

        except AttributeError:
            """
                отслеживаем неправильное нажатие при выборе категории для поиска
            """
            pass

        self.category_view.remove_node(node)
        self.category_manager.check_select_categories(node.text)

    def delete_node(self, obj):
        """
            удаляем директорию в списке поиска товаров
        """
        node = self.select_category_view.selected_node
        self.select_category_view.remove_node(node)
        self.refresh_product_node()
        self.category_manager.delete_select_category(node.text)

    def refresh_product_node(self):
        """
            очищаем дерево товаров при смене категории
        """
        for node in [i for i in self.products_view.iterate_all_nodes()]:
            self.products_view.remove_node(node)

    def start_parsing(self, obj):
        """
            запускаем парсинг товаров
        """
        select_categories_name_list = [name.text for name in self.select_category_view.iterate_all_nodes()]
        str_name_category = ",".join(select_categories_name_list)
        process = subprocess.Popen([sys.executable, 'parser_product.py', str_name_category],
                                   universal_newlines=True,
                                   text=True,
                                   bufsize=1
                                   )

        self.disable_button_search(process)
        # event = Clock.schedule_interval(self.print_log_process, 10)

    def disable_button_search(self, process):
        if process.poll() is None:
            self.button_parsing_products.disabled = True

    def show_product_list(self):
        self.refresh_product_node()
        category_name = self.select_category_view.selected_node.text
        category_id, marker = self.category_manager.get_select_category_id(category_name)
        products_list = self.product_manager.get_products_name_list(category_id, marker)
        for product in products_list:
            self.products_view.add_node(TreeViewLabel(text=product))

    def show_info_product(self):
        product_name = self.products_view.selected_node.text
        product_data = self.product_manager.get_product_info(product_name)
        self.image_product.source = product_data['image_path']

    def open_link_product(self, obj, a):
        webbrowser.open(self.product_link)


class CatalogView(TreeView):
    def __init__(self, text):
        super().__init__()
        self.root_options = dict(text=text)
        self.hide_root = False
        self.indent_level = 4
        self.size_hint_y = None

    def on_touch_down(self, touch):
        super().on_touch_down(touch)
        if touch.is_double_tap and self.collide_point(*touch.pos):
            self.select_handler()

    def select_handler(self):
        pass


class ProductView(CatalogView):
    def on_touch_down(self, touch):
        super().on_touch_down(touch)
        if self.collide_point(*touch.pos):
            self.select_handler()


class MainScreen(ScreenManager):

    def __init__(self, catalog_manager, parser):
        super().__init__()
        self.parser = parser
        self.catalog_manager = catalog_manager
        self.products_screen = ProductScreen(self.catalog_manager, self.parser)
        self.__place_screen()

    def __place_screen(self):
        self.add_widget(self.products_screen)
