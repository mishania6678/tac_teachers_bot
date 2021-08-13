import pymysql

from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.exceptions import MessageNotModified

from teacher import Teacher

from typing import Union

from threading import Thread
from datetime import datetime
from time import sleep

bot = Bot('1941908944:AAH-74UPpJW4ZcxUwx67lZdDTi_5Sib_S3o')
dp = Dispatcher(bot)

start_pressed = True
name_expected, selecting_expected, schedule_expected, = False, False, False
edit_classes, edit_schedule, add_lesson, delete_lesson, edit_lesson = False, False, False, False, False

name, subjects, classes, schedule = '', [], [], ''

new_classes_kb = False


def remove_ended_lessons():
    def lesson_ended():
        date = lesson_time.split(':')[0].strip()
        month = int(date.split('.')[1].strip())
        day = int(date.split('.')[0].strip())

        time = lesson_time.split(':')[1].strip()
        hour = int(time.split('.')[0].strip())
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
                        cursor.execute(f'UPDATE `T&C_teachers` SET lessons = REPLACE(lessons, "{lesson_time};", "") '
                                       f'WHERE name = "{row[0]}"')
                        db.commit()

                    except SyntaxError:
                        pass

        db.close()

        sleep(60)


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


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    global start_pressed, name_expected

    teachers = ['wargkul', 'nizhnitschek', 'maxbenival']
    if message.from_user.username not in teachers:
        await bot.send_message(message.chat.id, text='Цим ботом можуть користуватися лише викладачі онлайн-школи T&C')

    if start_pressed:
        Thread(target=remove_ended_lessons).start()

        await bot.send_message(message.chat.id, text='Введіть ваше ім\'я та нікнейм у телеграмі\n'
                                                     'Приклад: Коля, @nizhnitschek')
        name_expected = True
        start_pressed = False


@dp.message_handler(content_types=['text'])
async def text_handler(message: types.Message):
    global name_expected, selecting_expected, schedule_expected, new_classes_kb, \
        add_lesson, delete_lesson, edit_lesson, edit_classes, edit_schedule, name, subjects, classes, schedule

    try:
        if not (name_expected or selecting_expected or schedule_expected):
            if message.text == 'Змінити класи 🏫':
                edit_classes, edit_schedule, add_lesson, delete_lesson, edit_lesson = False, False, False, False, False

                new_classes_kb = True

                classes_kb = create_kb(
                    ('1', 'class 1'), ('2', 'class 2'), ('3', 'class 3'), ('4', 'class 4'), ('5', 'class 5'),
                    ('6', 'class 6'), ('7', 'class 7'), ('8', 'class 8'), ('9', 'class 9'), ('10', 'class 10'),
                    ('11', 'class 11'), ('Підтвердити ✅️️', 'class Підтвердити ✅️'),
                    kb_type='inline', tick_places=classes
                )

                await bot.send_message(message.chat.id, text='Виберіть класи:', reply_markup=classes_kb)

            elif message.text == 'Змінити розклад 📅':
                edit_classes, edit_schedule, add_lesson, delete_lesson, edit_lesson = False, True, False, False, False
                await bot.send_message(message.chat.id, text=f'Відправте відредагований розклад\n`{schedule}`',
                                       parse_mode='Markdown')

            elif message.text == 'Додати урок ➕':
                edit_classes, edit_schedule, add_lesson, delete_lesson, edit_lesson = False, False, True, False, False
                await bot.send_message(message.chat.id, text='Введіть дату та час уроку\nПриклад: 08.06: 10.00')

            elif message.text == 'Видалити урок ➖':
                edit_classes, edit_schedule, add_lesson, delete_lesson, edit_lesson = False, False, False, True, False
                await bot.send_message(message.chat.id, text='Введіть дату та час уроку\nПриклад: 08.06: 10.00')

            elif message.text == 'Змінити урок ✏':
                edit_classes, edit_schedule, add_lesson, delete_lesson, edit_lesson = False, False, False, False, True
                await bot.send_message(message.chat.id, text='Введіть дату та час уроку, який треба змінити, '
                                                             'на той, на який треба змінити'
                                                             '\nПриклад: 08.06: 10.00 -> 08.06: 16.00')

            elif edit_schedule:
                schedule = message.text.strip()
                teacher = Teacher(name.split(', ')[-1])
                teacher.edit_schedule(schedule.lower())
                await bot.send_message(message.chat.id, text='Розклад змінено')
                edit_schedule = False

            elif add_lesson:
                if ':' not in message.text.strip().lower():
                    await bot.send_message(message.chat.id, text='Неправильний формат дати уроку. Спробуйте ще раз')
                    raise SyntaxError

                teacher = Teacher(name.split(',')[-1].strip())
                teacher.add_lesson(message.text.strip().lower())
                await bot.send_message(message.chat.id, text='Урок додано')
                add_lesson = False

            elif edit_lesson:
                if '->' not in message.text or not not ':' not in message.text.split('->')[0].strip().lower() \
                        or ':' not in message.text.strip('->')[0].strip().lower():
                    await bot.send_message(message.chat.id, text='Неправильний формат дати уроку. Спробуйте ще раз')
                    raise SyntaxError

                teacher = Teacher(name.split(',')[-1].strip())

                state = teacher.edit_lesson(
                    message.text.split('->')[0].strip().lower(),
                    message.text.split('->')[1].strip().lower()
                )

                await bot.send_message(message.chat.id, text='Урок змінено' if state else 'Введеної дати немає в базі')
                edit_lesson = False

            elif delete_lesson:
                if ':' not in message.text.strip().lower():
                    await bot.send_message(message.chat.id, text='Неправильний формат дати уроку. Спробуйте ще раз')
                    raise SyntaxError

                teacher = Teacher(name.split(',')[-1].strip())
                state = teacher.delete_lesson(message.text.strip().lower())
                await bot.send_message(message.chat.id, text='Урок видалено' if state else 'Такого уроку немає в базі')
                edit_lesson = False

            else:
                await bot.send_message(message.chat.id, text='Команда не вибрана')

        else:
            if name_expected:
                if len(message.text.split()) != 2 or '@' not in message.text or ', ' not in message.text \
                        or message.text.index('@') < message.text.index(','):
                    await bot.send_message(message.chat.id, text='Неправильний формат вводу імені. Спробуйте ще раз')
                    raise SyntaxError

                name = message.text.strip()

                subjs_kb = create_kb(
                    ('Математика', 'subject Математика'),
                    ('Укр.мова', 'subject Укр.мова'),
                    ('Англ.мова', 'subject Англ.мова'),
                    ('Далі ➡️', 'subject Далі ➡️'),
                    kb_type='inline'
                )

                await bot.send_message(message.chat.id, text='Виберіть предмети, на яких ви спеціалізуєтесь:',
                                       reply_markup=subjs_kb)

                name_expected, selecting_expected = False, True

            elif schedule_expected:
                schedule = message.text.strip()

                teacher = Teacher(name.split(',')[-1].strip())
                teacher.add_teacher(name=name, subjects=', '.join(subjects), classes=classes, schedule=schedule.strip())

                funcs_kb = create_kb('Змінити розклад 📅', 'Змінити класи 🏫')
                funcs_kb.row(*[btn['text'] for btn in create_kb(
                    'Додати урок ➕', 'Змінити урок ✏', 'Видалити урок ➖', row_width=3)['keyboard'][0]])
                await bot.send_message(message.chat.id, text='Вітаю! Вас успішно додано у базу вчителів T&C!',
                                       reply_markup=funcs_kb)

                schedule_expected = False

    except (IndexError, ValueError):
        await bot.send_message(message.chat.id, text='Неправильний формат вхідних даних. Спробуйте ще раз')

    except SyntaxError:
        pass


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('subject'))
async def subjects_keyboard_callback_data_handler(call: types.CallbackQuery):
    global subjects

    if call.data == 'subject Далі ➡️':
        classes_kb = create_kb(
            ('1', 'class 1'), ('2', 'class 2'), ('3', 'class 3'), ('4', 'class 4'), ('5', 'class 5'), ('6', 'class 6'),
            ('7', 'class 7'), ('8', 'class 8'), ('9', 'class 9'), ('10', 'class 10'), ('11', 'class 11'),
            ('Назад ⬅️', 'class Назад ⬅️'), ('Продовжити ➡️', 'class Продовжити ➡️'),
            kb_type='inline', tick_places=classes
        )

        await bot.edit_message_text(chat_id=call.message.chat.id, text='Виберіть класи:',
                                    message_id=call.message.message_id, reply_markup=classes_kb)

    else:
        subj = call.data.split()[1]
        if subj not in subjects:
            subjects.append(subj)
        else:
            subjects.remove(subj)

        subjs_kb = create_kb(
            ('Математика', 'subject Математика'),
            ('Укр.мова', 'subject Укр.мова'),
            ('Англ.мова', 'subject Англ.мова'),
            ('Далі ➡️', 'subject Далі ➡️'),
            kb_type='inline', tick_places=subjects
        )

        try:
            await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                        text='Виберіть предмети, на яких ви спеціалізуєтесь:', reply_markup=subjs_kb)
        except MessageNotModified:
            pass


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('class'))
async def classes_keyboard_callback_data_handler(call: types.CallbackQuery):
    global subjects, selecting_expected, schedule_expected

    if call.data == 'class Назад ⬅️':
        subjs_kb = create_kb(
            ('Математика', 'subject Математика'),
            ('Укр.мова', 'subject Укр.мова'),
            ('Англ.мова', 'subject Англ.мова'),
            ('Далі ➡️', 'subject Далі ➡️'),
            kb_type='inline', tick_places=subjects
        )

        await bot.edit_message_text(chat_id=call.message.chat.id, text='Виберіть предмети, на яких ви спеціалізуєтесь:',
                                    message_id=call.message.message_id, reply_markup=subjs_kb)

    elif call.data == 'class Продовжити ➡️':
        if not subjects or not classes:
            await bot.send_message(call.message.chat.id, text='Не вибрані предмети або класи')
        else:
            await bot.send_message(call.message.chat.id, text='Чудово! Тепер створіть свій розклад!')
            await bot.send_message(call.message.chat.id, text='Напишіть бажаний графік занять '
                                                              'Кожен день/діапазон днів через ; '
                                                              'Можна через ; та з нового рядочка, як у прикладі\n'
                                                              'Перейти на новий рядочок Shift+Enter\n'
                                                              'Приклад:\n'
                                                              '08.06-10.06: 10.00-19.00;\n11.06: 12.00-16.00;\n'
                                                              '12.06: 13.00-21.00;\n13.06, 14.06: 8.00-19.00')
            selecting_expected, schedule_expected = False, True

    elif call.data == 'class Підтвердити ✅️':
        teacher = Teacher(name.split(',')[-1].strip())
        teacher.edit_classes(classes)
        await bot.send_message(call.message.chat.id, text='Класи змінено')

    else:
        curr_class = call.data.split()[1]
        if curr_class not in classes:
            classes.append(curr_class)
        else:
            classes.remove(curr_class)

        if not new_classes_kb:
            classes_kb = create_kb(
                ('1', 'class 1'), ('2', 'class 2'), ('3', 'class 3'), ('4', 'class 4'), ('5', 'class 5'),
                ('6', 'class 6'),
                ('7', 'class 7'), ('8', 'class 8'), ('9', 'class 9'), ('10', 'class 10'), ('11', 'class 11'),
                ('Назад ⬅️', 'class Назад ⬅️'), ('Продовжити ➡️', 'class Продовжити ➡️'),
                kb_type='inline', tick_places=classes
            )
        else:
            classes_kb = create_kb(
                ('1', 'class 1'), ('2', 'class 2'), ('3', 'class 3'), ('4', 'class 4'), ('5', 'class 5'),
                ('6', 'class 6'), ('7', 'class 7'), ('8', 'class 8'), ('9', 'class 9'), ('10', 'class 10'),
                ('11', 'class 11'), ('Підтвердити ✅️️', 'class Підтвердити ✅️'),
                kb_type='inline', tick_places=classes
            )

        try:
            await bot.edit_message_text(chat_id=call.message.chat.id, text='Виберіть класи:',
                                        message_id=call.message.message_id, reply_markup=classes_kb)
        except MessageNotModified:
            pass


executor.start_polling(dp, skip_updates=True)
