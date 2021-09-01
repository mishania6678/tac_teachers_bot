import pymysql

from aiogram import types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from typing import Union

# import threading
import datetime
import time
import json


class Admin:
    def __init__(self):
        self.db = None
        self.nickname = ''
        self.name, self.subjects, self.classes, self.schedule, self.lessons = '', [], [], '', []

    @staticmethod
    def teacher_registered(nickname) -> bool:
        with open('teachers_vars.json') as f:
            teachers = json.load(f).keys()
        return nickname in teachers

    def switch_user(self, nickname) -> None:
        self.nickname = nickname

        teacher_info = self.__getter()
        self.subjects = teacher_info[0][1].split(',') if teacher_info else self.subjects
        self.classes = teacher_info[0][2].split(',') if teacher_info else self.classes
        self.schedule = teacher_info[0][3].split(',') if teacher_info else self.schedule
        self.lessons = teacher_info[0][4].split('; ') if teacher_info else self.lessons

    def reinitialize_teacher_vars(self, teacher_vars: dict, except_var=None) -> dict:
        all_vars = [
            'name_expected', 'selecting_expected', 'schedule_expected',
            'edit_classes', 'edit_schedule', 'add_lesson', 'edit_lesson', 'delete_lesson',
            'new_classes_kb', 'show_lessons_on_date'
        ]

        for var in all_vars:
            teacher_vars[self.nickname][var] = False

        if except_var is not None:
            teacher_vars[self.nickname][except_var] = True

        return teacher_vars

    @staticmethod
    def update_teacher_vars(teachers_vars: dict) -> None:
        with open('teachers_vars.json', 'w') as f:
            json.dump(teachers_vars, f)

    def remove_ended_lessons(self) -> None:
        def lesson_ended():
            lesson_date = lesson_datetime.split(':')[0].strip()
            month = int(lesson_date.split('.')[1].strip())
            day = int(lesson_date.split('.')[0].strip())

            lesson_time = lesson_datetime.split(':')[1].strip()
            hour = int(lesson_time.split('.')[0].strip()) + 1
            minutes = int(lesson_time.split('.')[1].strip())

            return curr_datetime > datetime.datetime(2021, month, day, hour, minutes)

        while True:
            db = pymysql.connect(
                host='us-cdbr-east-04.cleardb.com',
                user='b1c96c8af48cba',
                password='c13f73de',
                database='heroku_805235abf2a3a56'
            )

            curr_date = datetime.datetime.now().date()
            curr_time = datetime.datetime.now().time()
            curr_datetime = datetime.datetime(curr_date.year, curr_date.month, curr_date.day, curr_time.hour,
                                              curr_time.minute, curr_time.second, curr_time.microsecond)

            with db.cursor() as cursor:
                cursor.execute('SELECT * FROM `T&C_teachers`')
                rows = cursor.fetchall()
                for row in rows:
                    for lesson_datetime in row[4][:-1].split(';'):
                        lesson_datetime = lesson_datetime.strip()
                        try:
                            if not row[4]:
                                raise SyntaxError

                            if lesson_ended():
                                self.lessons.remove(lesson_datetime)
                                cursor.execute(f'UPDATE `T&C_teachers` SET lessons = '
                                               f'REPLACE(lessons, "{lesson_datetime};", "") WHERE name = "{row[0]}"')
                                db.commit()

                        except (IndexError, ValueError):
                            cursor.execute(
                                f'UPDATE `T&C_teachers` SET lessons = REPLACE(lessons, "{lesson_datetime};", "") '
                                f'WHERE name = "{row[0]}"')
                            db.commit()

                        except SyntaxError:
                            pass

            db.close()

            time.sleep(60)

    @staticmethod
    def check_schedule(schedule: str) -> None:
        try:
            days = schedule.replace(' ', '').split(';')
            date_ranges = [day.split(':')[0] for day in days]
            time_ranges = [day.split(':')[1] for day in days]

            for date_range in date_ranges:
                for date_rang in date_range.split(','):
                    for date in date_rang.split('-'):
                        datetime.datetime(2021, int(date[date.index('.') + 1:]), int(date[:date.index('.')]))

            for time_range in time_ranges:
                for time_rang in time_range.split(','):
                    for time in time_rang.split('-'):
                        datetime.datetime(2021, 1, 1, int(time[:time.index('.')]), int(time[time.index('.') + 1:]))

        except:
            raise IndexError

    @staticmethod
    def create_kb(*args, kb_type='reply', row_width=2, resize_keyboard=True, tick_places=None) -> \
            Union[types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup]:

        if tick_places is None:
            tick_places = []

        kb = InlineKeyboardMarkup(row_width=row_width) if kb_type == 'inline' \
            else ReplyKeyboardMarkup(resize_keyboard=resize_keyboard, row_width=row_width)

        for i in range(0, len(args) - 1, row_width):
            if kb_type == 'inline':
                kb.add(*[InlineKeyboardButton(
                    text=args[i + j][0] if args[i + j][0] not in tick_places else f'{args[i + j][0]}✅',
                    callback_data=args[i + j][1]) for j in range(row_width)])
            else:
                kb.add(*[KeyboardButton(text=args[i + j]) for j in range(row_width)])

        if len(args) % 2 != 0 and row_width % 2 == 0:
            if kb_type == 'inline':
                kb.add(InlineKeyboardButton(text=args[-1][0] if args[-1][0] not in tick_places else f'{args[-1][0]}✅',
                                            callback_data=args[-1][1]))
            else:
                kb.add(KeyboardButton(text=args[-1]))

        return kb

    def add_teacher(self, name, subjects, classes, schedule, lessons='') -> None:
        self.__connect_database()

        with self.db.cursor() as cursor:
            cursor.execute('INSERT INTO `T&C_teachers` (name, subjects, classes, schedule, lessons) '
                           f'VALUES ("{name.lower()}", "{subjects}", "{classes}", '
                           f'"{schedule.lower()}", "{lessons.lower()}")')
            self.db.commit()

        self.__close_database()

    def delete_teacher(self, nickname):
        self.__connect_database()

        with self.db.cursor() as cursor:
            cursor.execute(f'DELETE FROM `T&C_teachers` WHERE name LIKE "%{nickname}"')
            self.db.commit()

        self.__close_database()

    def edit_classes(self, new_classes) -> None:
        self.__connect_database()

        with self.db.cursor() as cursor:
            cursor.execute(f'UPDATE `T&C_teachers` SET classes = "{new_classes}"'
                           f'WHERE name LIKE "%{self.nickname}"')
            self.db.commit()

        self.__close_database()

    def edit_schedule(self, new_schedule) -> None:
        self.__connect_database()

        with self.db.cursor() as cursor:
            cursor.execute(f'UPDATE `T&C_teachers` SET schedule = "{new_schedule}" '
                           f'WHERE name LIKE "%{self.nickname}"')
            self.db.commit()

        self.__close_database()

    def add_lesson(self, lesson_time) -> None:
        self.__connect_database()

        with self.db.cursor() as cursor:
            cursor.execute(f'UPDATE `T&C_teachers` SET lessons = CONCAT(lessons, "{lesson_time};") '
                           f'WHERE name LIKE "%{self.nickname}"')
            self.db.commit()

        self.__close_database()

    def edit_lesson(self, old_lesson_time, new_lesson_time) -> bool:
        self.__connect_database()

        with self.db.cursor() as cursor:
            cursor.execute(f'SELECT * FROM `T&C_teachers` '
                           f'WHERE name LIKE "%{self.nickname}" AND lessons LIKE "%{old_lesson_time.lower()}%"')
            state = cursor.fetchall() != ()

        with self.db.cursor() as cursor:
            cursor.execute(f'UPDATE `T&C_teachers` SET lessons = REPLACE(lessons, "{old_lesson_time.lower()};", '
                           f'"{new_lesson_time};") WHERE name LIKE "%{self.nickname}"')
            self.db.commit()

        self.__close_database()

        return state

    def delete_lesson(self, lesson_time) -> bool:
        self.__connect_database()

        with self.db.cursor() as cursor:
            cursor.execute(f'SELECT * FROM `T&C_teachers` WHERE name LIKE "%{self.nickname}" '
                           f'AND lessons LIKE "%{lesson_time.lower()}%"')
            state = cursor.fetchall() != ()

        with self.db.cursor() as cursor:
            cursor.execute(f'UPDATE `T&C_teachers` SET lessons = REPLACE(lessons, "{lesson_time.lower()}\n", "") '
                           f'WHERE name LIKE "%{self.nickname}"')
            self.db.commit()

        self.__close_database()

        return state

    def show_lessons(self, date='today') -> str:
        self.__connect_database()

        if date == 'today':
            date = f'{datetime.datetime.today().day}.{datetime.datetime.today().month}'

        lessons_on_date = ''
        for lesson in self.lessons:
            if date == lesson.split(':')[0].strip():
                lessons_on_date += f'{lesson.split(":")[1].strip()}\n'

        self.__close_database()

        return lessons_on_date if lessons_on_date else 'Не заплановано ніяких уроків'

    def __getter(self) -> tuple:
        self.__connect_database()

        with self.db.cursor() as cursor:
            cursor.execute(f'SELECT * FROM `T&C_teachers` WHERE name LIKE "%{self.nickname}" ')
            found_obj = cursor.fetchall()

        self.__close_database()

        return found_obj

    def __connect_database(self) -> None:
        self.db = pymysql.connect(
            host='us-cdbr-east-04.cleardb.com',
            user='b1c96c8af48cba',
            password='c13f73de',
            database='heroku_805235abf2a3a56'
        )

    def __close_database(self) -> None:
        self.db.close()
