import pymysql

from aiogram import types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from datetime import datetime
from time import sleep

from typing import Union


class Admin:
    def __init__(self):
        self.db = None
        self.nickname = ''
        self.name, self.subjects, self.classes, self.schedule, self.lessons = '', [], [], '', []
        self.edit_classes, self.edit_schedule, self.add_lesson, self.delete_lesson, self.edit_lesson = False, False, False, False, False

    def switch_user(self, nickname):
        if self.nickname == nickname or nickname == '@tac_teachers_bot':
            return

        print('vsm')

        self.nickname = nickname

        self.name = self.getter('name') if self.getter('name') != 0 else self.name
        self.subjects = self.getter('subjects', split=True) if self.getter('subjects', split=True) != 0 else self.subjects
        self.classes = self.getter('classes', split=True) if self.getter('classes', split=True) != 0 else self.classes
        self.schedule = self.getter('schedule') if self.getter('schedule') != 0 else self.schedule
        self.lessons = self.getter('lessons', split=True) if self.getter('lessons', split=True) != 0 else self.lessons

        try:
            self.edit_classes, self.edit_schedule, self.add_lesson, self.delete_lesson, self.edit_lesson = self.getter(
                'vars', split=True) if self.getter('vars', split=True) != 0 \
                else self.edit_classes, self.edit_schedule, self.add_lesson, self.delete_lesson, self.edit_lesson
        except ValueError:
            pass

    def update_teacher_vars(self):
        self.__connect_database()

        with self.db.cursor() as cursor:
            cursor.execute(f'UPDATE `T&C_teachers` SET vars = "{self.edit_classes}, {self.edit_schedule}, '
                           f'{self.add_lesson}, {self.delete_lesson}, {self.edit_lesson}" '
                           f'WHERE name LIKE "%{self.nickname}"')

        self.__close_database()

    def getter(self, obj, split=False) -> Union[str, list]:
        self.__connect_database()

        with self.db.cursor() as cursor:
            cursor.execute(f'SELECT {obj} FROM `T&C_teachers` WHERE name LIKE "%{self.nickname}" ')
            found_obj = cursor.fetchall()

        self.__close_database()

        print(found_obj)

        return 0 if not found_obj else found_obj[0] if not split else found_obj.split(',')

    @staticmethod
    def remove_ended_lessons() -> None:
        def lesson_ended():
            date = lesson_time.split(':')[0].strip()
            month = int(date.split('.')[1].strip())
            day = int(date.split('.')[0].strip())

            time = lesson_time.split(':')[1].strip()
            hour = int(time.split('.')[0].strip()) + 1
            minutes = int(time.split('.')[1].strip())

            return curr_datetime > datetime(2021, month, day, hour, minutes)

        while True:
            db = pymysql.connect(
                host='us-cdbr-east-04.cleardb.com',
                user='b1c96c8af48cba',
                password='c13f73de',
                database='heroku_805235abf2a3a56'
            )

            curr_date = datetime.now().date()
            curr_time = datetime.now().time()
            curr_datetime = datetime(curr_date.year, curr_date.month, curr_date.day, curr_time.hour,
                                     curr_time.minute, curr_time.second, curr_time.microsecond)

            with db.cursor() as cursor:
                cursor.execute('SELECT * FROM `T&C_teachers`')
                rows = cursor.fetchall()
                for row in rows:
                    for lesson_time in row[4][:-1].split(';'):
                        lesson_time = lesson_time.strip()
                        try:
                            if not row[4]:
                                raise SyntaxError

                            if lesson_ended():
                                cursor.execute(f'UPDATE `T&C_teachers` SET lessons = '
                                               f'REPLACE(lessons, "{lesson_time};", "") WHERE name = "{row[0]}"')
                                db.commit()

                        except (IndexError, ValueError):
                            cursor.execute(
                                f'UPDATE `T&C_teachers` SET lessons = REPLACE(lessons, "{lesson_time};", "") '
                                f'WHERE name = "{row[0]}"')
                            db.commit()

                        except SyntaxError:
                            pass

            db.close()

            sleep(60)

    @staticmethod
    def check_schedule(schedule: str) -> None:
        try:
            days = schedule.replace(' ', '').split(';')
            date_ranges = [day.split(':')[0] for day in days]
            time_ranges = [day.split(':')[1] for day in days]

            for date_range in date_ranges:
                for date_rang in date_range.split(','):
                    for date in date_rang.split('-'):
                        datetime(2021, int(date[date.index('.') + 1:]), int(date[:date.index('.')]))

            for time_range in time_ranges:
                for time_rang in time_range.split(','):
                    for time in time_rang.split('-'):
                        datetime(2021, 1, 1, int(time[:time.index('.')]), int(time[time.index('.') + 1:]))

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

    def _edit_classes(self, new_classes) -> None:
        self.__connect_database()

        with self.db.cursor() as cursor:
            cursor.execute(f'UPDATE `T&C_teachers` SET classes = "{new_classes}"'
                           f'WHERE name LIKE "%{self.nickname}"')
            self.db.commit()

        self.__close_database()

    def _edit_schedule(self, new_schedule) -> None:
        self.__connect_database()

        with self.db.cursor() as cursor:
            cursor.execute(f'UPDATE `T&C_teachers` SET schedule = "{new_schedule.lower()}" '
                           f'WHERE name LIKE "%{self.nickname}"')
            self.db.commit()

        self.__close_database()

    def _add_lesson(self, lesson_time) -> None:
        self.__connect_database()

        with self.db.cursor() as cursor:
            cursor.execute(f'UPDATE `T&C_teachers` SET lessons = CONCAT(lessons, "{lesson_time};") '
                           f'WHERE name LIKE "%{self.nickname}"')
            self.db.commit()

        self.__close_database()

    def _edit_lesson(self, old_lesson_time, new_lesson_time) -> bool:
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

    def _delete_lesson(self, lesson_time) -> bool:
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

    def __connect_database(self):
        self.db = pymysql.connect(
            host='us-cdbr-east-04.cleardb.com',
            user='b1c96c8af48cba',
            password='c13f73de',
            database='heroku_805235abf2a3a56'
        )

    def __close_database(self):
        self.db.close()

    def __delete_teacher(self, nickname):
        self.__connect_database()

        with self.db.cursor() as cursor:
            cursor.execute(f'DELETE FROM `T&C_teachers` WHERE name LIKE "%{nickname}"')
            self.db.commit()

        self.__close_database()
