from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from  kivy.uix.label import Label
from kivy.uix.recyclegridlayout import RecycleGridLayout
from kivy.properties import ObjectProperty, StringProperty, NumericProperty
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.storage.jsonstore import JsonStore
from kivy.uix.recycleview import RecycleView
from datetime import  datetime
from kivy.metrics import dp

# Установим размер окна для удобства разработки
Window.size = (360, 640)

# Загружаем KV-файл с интерфейсом
Builder.load_file("kv/screens.kv")


class StandardItem(RecycleDataViewBehavior, GridLayout):
    exercise = StringProperty("")
    gold = StringProperty("")
    silver = StringProperty("")
    bronze = StringProperty("")
    unit = StringProperty("")
    index = NumericProperty(0)  # Добавляем свойство index

    def refresh_view_attrs(self, rv, index, data):
        self.index = index  # Устанавливаем индекс при обновлении
        return super().refresh_view_attrs(rv, index, data)


class StandardsRecycleView(RecycleView):
    def __init__(self, **kwargs):
        super(StandardsRecycleView, self).__init__(**kwargs)
        self.viewclass = 'StandardItem'
        self.layout_manager = RecycleGridLayout()
        self.layout_manager.default_size = (None, dp(60))
        self.layout_manager.default_size_hint = (1, None)
        self.layout_manager.cols = 1
        self.layout_manager.spacing = dp(5)
        self.layout_manager.bind(minimum_height=self.layout_manager.setter('height'))
        self.add_widget(self.layout_manager)

class RegistrationScreen(Screen):
    name_input = ObjectProperty()
    age_input = ObjectProperty()
    gender_spinner = ObjectProperty()

    def on_pre_enter(self):
        """Загружаем сохраненные данные при открытии экрана"""
        store = JsonStore('user_data.json')
        if store.exists('user'):
            user_data = store.get('user')
            self.name_input.text = user_data['name']
            self.age_input.text = str(user_data['age'])
            self.gender_spinner.text = user_data['gender'].capitalize()

    @staticmethod
    def get_user_stage(age: int) -> int:
        if 6 <= age <= 7:
            return 1
        elif 8 <= age <= 9:
            return 2
        elif 10 <= age <= 11:
            return 3
        elif 12 <= age <= 13:
            return 4
        elif 14 <= age <= 15:
            return 5
        elif 16 <= age <= 17:
            return 6
        elif 18 <= age <= 19:
            return 7
        elif 20 <= age <= 24:
            return 8
        elif 25 <= age <= 29:
            return 9
        elif 30 <= age <= 34:
            return 10
        elif 35 <= age <= 39:
            return 11
        elif 40 <= age <= 44:
            return 12
        elif 45 <= age <= 49:
            return 13
        elif 50 <= age <= 54:
            return 14
        elif 55 <= age <= 59:
            return 15
        elif 60 <= age <= 64:
            return 16
        elif 65 <= age <= 69:
            return 17
        elif age >= 70:
            return 18

    def register_user(self):
        name = self.name_input.text.strip()
        age = int(self.age_input.text)
        stage = self.get_user_stage(age)
        gender = self.gender_spinner.text.lower()  # Приводим к нижнему регистру

        user_data = {
            'name': name,
            'age': age,
            'gender': gender,  # Уже в нижнем регистре
            'stage': stage
        }

        store = JsonStore('user_data.json')
        store.put('user', **user_data)

        self.manager.current = 'main'
        main_screen = self.manager.get_screen('main')
        main_screen.load_standards(user_data['stage'], user_data['gender'])


class MainScreen(Screen):
    stage_info = StringProperty("")
    gender = StringProperty("")

    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)

    def on_pre_enter(self):
        """Проверяем данные пользователя при открытии"""
        store = JsonStore('user_data.json')
        if not store.exists('user'):
            self.manager.current = 'registration'
        else:
            user_data = store.get('user')
            self.load_standards(user_data['stage'], user_data['gender'])

    def logout(self):
        store = JsonStore('user_data.json')
        store.delete('user')

        # Очистка всех записей (осторожно!)
        from db import clear_all_entries
        clear_all_entries()

        self.manager.current = 'registration'


    def load_standards(self, stage: int, gender: str):
        from modules.standards import get_standards_for_stage, get_stage_info
        standards = get_standards_for_stage(stage, gender)
        stage_data = get_stage_info(stage)
        self.stage_info = f"Ступень {stage_data['number']} ({stage_data['age_range']})"
        self.gender = gender
        self.ids.rv.data = [  # Используйте ids.rv, а не self.rv
            {
                'exercise': item['exercise'],
                'gold': str(item['gold']),  # Преобразуйте в строку!
                'silver': str(item['silver']),
                'bronze': str(item['bronze']),
                'unit': item['unit']
            }
            for item in standards
        ]

# class TrackerScreen(Screen):
#     def on_enter(self):
#         """Обновляем данные трекера при открытии экрана"""
#         from modules.tracker import get_progress_data
#         progress = get_progress_data()
#         self.ids.progress_container.clear_widgets()
#         for exercise, data in progress.items():
#             self.ids.progress_container.add_widget(
#                 ProgressItem(
#                     exercise=exercise,
#                     current=data['current'],
#                     best=data['best'],
#                     norm=data['norm']
#                 )
#             )


class NotebookEntry(BoxLayout):
    """Элемент записи в блокноте"""
    exercise = StringProperty("")
    result = StringProperty("")
    notes = StringProperty("")
    date = StringProperty("")
    entry_id = NumericProperty(0)

    def __init__(self, **kwargs):
        # Преобразуем результат в строку перед созданием виджета
        if 'result' in kwargs:
            kwargs['result'] = str(kwargs['result'])
        super().__init__(**kwargs)


    def delete_entry(self):
        """Удаление текущей записи"""
        app = App.get_running_app()
        notebook_screen = app.root.get_screen('notebook')
        notebook_screen.delete_entry_by_id(self.entry_id)


class NotebookScreen(Screen):
    exercises_spinner = ObjectProperty(None)
    result_input = ObjectProperty(None)
    notes_input = ObjectProperty(None)

    def on_enter(self):
        """Загрузка данных при открытии экрана"""
        self.load_exercises()
        self.load_entries()

    def delete_entry_by_id(self, entry_id):
        """Удаление записи по ID"""
        from db import delete_entry
        delete_entry(entry_id)
        self.load_entries()  # Перезагружаем список

    def load_entries(self):
        """Загрузка и отображение всех записей"""
        from db import get_all_entries
        entries = get_all_entries()

        self.ids.entries_container.clear_widgets()

        grouped_entries = {}
        for entry in entries:
            date_only = entry['date'].split()[0]
            if date_only not in grouped_entries:
                grouped_entries[date_only] = []
            grouped_entries[date_only].append(entry)

        for date, entries_list in sorted(grouped_entries.items(), reverse=True):
            # Заголовок с датой
            date_label = Label(
                text=date,
                size_hint_y=None,
                height=dp(40),
                font_size='18sp',
                bold=True,
                color=(0.2, 0.2, 0.2, 1)
            )
            self.ids.entries_container.add_widget(date_label)

            for entry in entries_list:
                entry_widget = NotebookEntry(
                    exercise=str(entry['exercise']),
                    result=str(entry['result']),
                    notes=str(entry['notes']) if entry['notes'] else "",
                    date=str(entry['date']),
                    entry_id=entry['id']  # Передаем ID как именованный аргумент
                )
                self.ids.entries_container.add_widget(entry_widget)

    def load_exercises(self):
        """Загрузка упражнений для текущего пользователя"""
        try:
            store = JsonStore('user_data.json')
            if store.exists('user'):
                user_data = store.get('user')
                from modules.standards import get_standards_for_stage
                standards = get_standards_for_stage(user_data['stage'], user_data['gender'])

                exercises = list({item['exercise'] for item in standards})
                exercises.sort()

                if self.exercises_spinner:
                    self.exercises_spinner.values = exercises
                    if exercises:
                        self.exercises_spinner.text = exercises[0]
        except Exception as e:
            print(f"Ошибка загрузки упражнений: {e}")

    def save_entry(self):
        """Сохранение новой записи"""
        try:
            exercise = self.exercises_spinner.text
            result = self.result_input.text.strip()
            notes = self.notes_input.text.strip()
            date = datetime.now().strftime("%Y-%m-%d %H:%M")

            if exercise and result:
                from db import save_entry
                save_entry(exercise, result, notes, date)
                self.clear_inputs()
                self.load_entries()
        except Exception as e:
            print(f"Ошибка сохранения записи: {e}")

    def clear_inputs(self):
        """Очистка полей ввода"""
        self.ids.result_input.text = ""
        self.ids.notes_input.text = ""


class CalculatorScreen(Screen):
    badge_result = StringProperty("")
    badge_details = StringProperty("")

    def on_pre_enter(self):
        """Вычисляем знак ГТО при открытии экрана"""
        from modules.calc import calculate_badge
        store = JsonStore('user_data.json')

        if store.exists('user'):
            user_data = store.get('user')
            result = calculate_badge(user_data)

            if result['can_get_badge']:
                self.badge_result = f"Вы можете получить: {result['badge'].capitalize()} знак ГТО"
                details = []

                # Добавляем информацию об обязательных нормативах
                details.append("\nОбязательные нормативы:")
                for item in result['completed_required']:
                    details.append(f"{item['exercise']}: {item['result']} {item['unit']} ({item['badge']})")

                # Добавляем информацию о нормативах по выбору
                details.append("\nНормативы по выбору:")
                for item in result['completed_optional']:
                    details.append(f"{item['exercise']}: {item['result']} {item['unit']} ({item['badge']})")

                self.badge_details = "\n".join(details)
            else:
                self.badge_result = "Вы пока не можете получить знак ГТО"

                details = []
                if result['missing_required']:
                    details.append(f"\nНе выполнены обязательные категории: {', '.join(result['missing_required'])}")

                if result['missing_optional'] > 0:
                    required = 2 if result['badge'] == 'gold' else 1
                    details.append(f"\nНе хватает {result['missing_optional']} из {required} нормативов по выбору")

                self.badge_details = "\n".join(details) if details else "Выполните нормативы для получения знака"
        else:
            self.badge_result = "Сначала зарегистрируйтесь"
            self.badge_details = ""


class GTOApp(App):
    def build(self):
        from db import init_db
        init_db()

        sm = ScreenManager()
        sm.add_widget(RegistrationScreen(name="registration"))
        sm.add_widget(MainScreen(name="main"))
        sm.add_widget(NotebookScreen(name='notebook'))
        sm.add_widget(CalculatorScreen(name='calc'))


        store = JsonStore('user_data.json')
        if store.exists('user'):
            sm.current = 'main'
        else:
            sm.current = 'registration'

        return sm


if __name__ == "__main__":
    GTOApp().run()