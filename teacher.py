import pymysql


class Teacher:
    def __init__(self, nickname):
        self.db = pymysql.connect(
            host='us-cdbr-east-04.cleardb.com',
            user='b1c96c8af48cba',
            password='c13f73de',
            database='heroku_805235abf2a3a56'
        )

        self.nickname = nickname

    def add_teacher(self, name, subjects, classes, schedule, lessons='') -> None:
        with self.db.cursor() as cursor:
            cursor.execute('INSERT INTO `T&C_teachers` (name, subjects, classes, schedule, lessons) '
                           f'VALUES ("{name.lower()}", "{subjects}", "{classes}", '
                           f'"{schedule.lower()}", "{lessons.lower()}")')
            self.db.commit()

    def __delete_teacher(self):
        with self.db.cursor() as cursor:
            cursor.execute(f'DELETE FROM `T&C_teachers` WHERE name LIKE "%{self.nickname}"')
            self.db.commit()

    def edit_classes(self, new_classes) -> None:
        with self.db.cursor() as cursor:
            cursor.execute(f'UPDATE `T&C_teachers` SET classes = "{new_classes}"'
                           f'WHERE name LIKE "%{self.nickname}"')
            self.db.commit()

    def edit_schedule(self, new_schedule) -> None:
        with self.db.cursor() as cursor:
            cursor.execute(f'UPDATE `T&C_teachers` SET schedule = "{new_schedule.lower()}" '
                           f'WHERE name LIKE "%{self.nickname}"')
            self.db.commit()

    def add_lesson(self, lesson_time) -> None:
        with self.db.cursor() as cursor:
            cursor.execute(f'UPDATE `T&C_teachers` SET lessons = CONCAT(lessons, "{lesson_time};") '
                           f'WHERE name LIKE "%{self.nickname}"')
            self.db.commit()

    def edit_lesson(self, old_lesson_time, new_lesson_time) -> bool:
        with self.db.cursor() as cursor:
            cursor.execute(f'SELECT * FROM `T&C_teachers` '
                           f'WHERE name LIKE "%{self.nickname}" AND lessons LIKE "%{old_lesson_time.lower()}%"')
            state = cursor.fetchall() != ()

        with self.db.cursor() as cursor:
            cursor.execute(f'UPDATE `T&C_teachers` SET lessons = REPLACE(lessons, "{old_lesson_time.lower()};", '
                           f'"{new_lesson_time};") WHERE name LIKE "%{self.nickname}"')
            self.db.commit()

        return state

    def delete_lesson(self, lesson_time) -> bool:
        with self.db.cursor() as cursor:
            cursor.execute(f'SELECT * FROM `T&C_teachers` WHERE name LIKE "%{self.nickname}" '
                           f'AND lessons LIKE "%{lesson_time.lower()}%"')
            state = cursor.fetchall() != ()

        with self.db.cursor() as cursor:
            cursor.execute(f'UPDATE `T&C_teachers` SET lessons = REPLACE(lessons, "{lesson_time.lower()}\n", "") '
                           f'WHERE name LIKE "%{self.nickname}"')
            self.db.commit()

        return state

    def __del__(self):
        self.db.close()
