from aiogram import Bot, Dispatcher, types, executor
from aiogram.utils.exceptions import MessageNotModified

from admin import Admin

from threading import Thread

import json

bot = Bot('1941908944:AAH-74UPpJW4ZcxUwx67lZdDTi_5Sib_S3o')
dp = Dispatcher(bot)

admin = Admin()

current_user = None


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    global current_user

    teachers = ['wargkul', 'nizhnitschek', 'maxbenival']
    if message.from_user.username not in teachers:
        await bot.send_message(message.chat.id, text='⚠ Цим ботом можуть користуватися лише викладачі онлайн-школи T&C')

    if admin.teacher_registered(f'@{message.from_user.username}'):
        print('nu')
        if current_user != f'@{message.from_user.username}' and current_user != '@tac_teachers_bot':
            current_user = f'@{message.from_user.username}'
            admin.switch_user(f'@{message.from_user.username}')

    else:
        with open('teachers_vars.json') as fr:
            curr_teachers_vars = json.load(fr)

        default_vars = {
            f'@{message.from_user.username}': {
                "name_expected": 1, "selecting_expected": 0, "schedule_expected": 0, "new_classes_kb": 0,
                "edit_classes": 0, "edit_schedule": 0, "add_lesson": 0, "edit_lesson": 0, "delete_lesson": 0,
            }
        }

        admin.update_teacher_vars(curr_teachers_vars | default_vars)

        Thread(target=admin.remove_ended_lessons).start()

        await bot.send_message(message.chat.id, text='🔡 Введіть ваше ім\'я та нікнейм у телеграмі\n'
                                                     'Приклад: Коля, @nizhnitschek')


@dp.message_handler(content_types=['text'])
async def text_handler(message: types.Message):
    global current_user

    if current_user != f'@{message.from_user.username}' and f'@{message.from_user.username}' != '@tac_teachers_bot':
        current_user = f'@{message.from_user.username}'
        admin.switch_user(f'@{message.from_user.username}')

    try:
        with open('teachers_vars.json') as f:
            teachers_vars = json.load(f)

            if not (teachers_vars[current_user]['name_expected'] or teachers_vars[current_user]['selecting_expected']
                    or teachers_vars[current_user]['schedule_expected']):
                if message.text == 'Назад ⬅️':
                    funcs_kb = admin.create_kb(
                        'Мій розклад 📅', 'Уроки 📚',
                        'Змінити класи 🏫', 'Налаштування ⚙'
                    )

                    await bot.send_message(message.chat.id, text='.', reply_markup=funcs_kb)

                elif message.text == 'Мій розклад 📅':
                    schedule_kb = admin.create_kb(
                        'Подивитися уроки на сьогодні 👁', 'Подивитися уроки на дату 🗓',
                        'Змінити розклад 📋', 'Назад ⬅️'
                    )

                    await bot.send_message(message.chat.id, text='.', reply_markup=schedule_kb)

                elif message.text == 'Уроки 📚':
                    lessons_kb = admin.create_kb(
                        'Додати урок ➕', 'Видалити урок ➖',
                        'Змінити урок ✏', 'Назад ⬅️'
                    )

                    await bot.send_message(message.chat.id, text='.', reply_markup=lessons_kb)

                elif message.text == 'Змінити класи 🏫':
                    teachers_vars[current_user]['edit_classes'] = teachers_vars[current_user]['edit_schedule'] = False
                    teachers_vars[current_user]['add_lesson'] = teachers_vars[current_user]['delete_lesson'] = False
                    teachers_vars[current_user]['edit_lesson'] = False
                    teachers_vars[current_user]['new_classes_kb'] = True

                    classes_kb = admin.create_kb(
                        ('1', 'class 1'), ('2', 'class 2'), ('3', 'class 3'), ('4', 'class 4'), ('5', 'class 5'),
                        ('6', 'class 6'), ('7', 'class 7'), ('8', 'class 8'), ('9', 'class 9'), ('10', 'class 10'),
                        ('11', 'class 11'), ('Підтвердити ✅️️', 'class Підтвердити ✅️'),
                        kb_type='inline', tick_places=admin.classes
                    )

                    await bot.send_message(message.chat.id, text='🔀 Виберіть класи:', reply_markup=classes_kb)

                elif message.text == 'Налаштування ⚙':
                    pass

                elif message.text == 'Змінити розклад 📋':
                    teachers_vars[current_user]['edit_classes'] = False
                    teachers_vars[current_user]['edit_schedule'] = True
                    teachers_vars[current_user]['add_lesson'] = teachers_vars[current_user]['delete_lesson'] = False
                    teachers_vars[current_user]['edit_lesson'] = False
                    await bot.send_message(message.chat.id, text=f'🔡 Відправте відредагований розклад\n'
                                                                 f'`{admin.schedule}`', parse_mode='Markdown')

                elif message.text == 'Подивитися уроки на сьогодні 👁':
                    pass

                elif message.text == 'Подивитися уроки на дату 🗓':
                    pass

                elif message.text == 'Додати урок ➕':
                    teachers_vars[current_user]['edit_classes'] = teachers_vars[current_user]['edit_schedule'] = False
                    teachers_vars[current_user]['add_lesson'] = True
                    teachers_vars[current_user]['delete_lesson'] = teachers_vars[current_user]['edit_lesson'] = False
                    await bot.send_message(message.chat.id, text='🔡 Введіть дату та час уроку\nПриклад: 08.06: 10.00')

                elif message.text == 'Видалити урок ➖':
                    teachers_vars[current_user]['edit_classes'] = teachers_vars[current_user]['edit_schedule'] = False
                    teachers_vars[current_user]['add_lesson'] = False
                    teachers_vars[current_user]['delete_lesson'] = True
                    teachers_vars[current_user]['edit_lesson'] = False
                    await bot.send_message(message.chat.id, text='🔡 Введіть дату та час уроку\nПриклад: 08.06: 10.00')

                elif message.text == 'Змінити урок ✏':
                    teachers_vars[current_user]['edit_classes'] = teachers_vars[current_user]['edit_schedule'] = False
                    teachers_vars[current_user]['add_lesson'] = teachers_vars[current_user]['delete_lesson'] = False
                    teachers_vars[current_user]['edit_lesson'] = True
                    await bot.send_message(message.chat.id, text='🔡 Введіть дату та час уроку, який треба змінити, '
                                                                 'на той, на який треба змінити'
                                                                 '\nПриклад: 08.06: 10.00 -> 08.06: 16.00')

                elif teachers_vars[current_user]['edit_schedule']:
                    admin.schedule = message.text.strip()
                    admin.check_schedule(admin.schedule)

                    admin.edit_schedule(admin.schedule)
                    await bot.send_message(message.chat.id, text='Розклад змінено 😆')

                    teachers_vars[current_user]['edit_schedule'] = False

                elif teachers_vars[current_user]['add_lesson']:
                    if ':' not in message.text.strip():
                        await bot.send_message(message.chat.id, text='❗Неправильний формат дати уроку. '
                                                                     'Спробуйте ще раз')
                        raise SyntaxError

                    admin.add_lesson(message.text.strip())
                    await bot.send_message(message.chat.id, text='Урок додано 😆')
                    teachers_vars[current_user]['add_lesson'] = False

                elif teachers_vars[current_user]['edit_lesson']:
                    if '->' not in message.text or not not ':' not in message.text.split('->')[0].strip() \
                            or ':' not in message.text.strip('->')[0].strip():
                        await bot.send_message(message.chat.id, text='❗Неправильний формат дати уроку. '
                                                                     'Спробуйте ще раз')
                        raise SyntaxError

                    state = admin.edit_lesson(
                        message.text.split('->')[0].strip(),
                        message.text.split('->')[1].strip()
                    )

                    await bot.send_message(message.chat.id,
                                           text='Урок змінено 😆' if state else '😅 Введеної дати немає в базі')
                    admin.edit_lesson = False

                elif teachers_vars[current_user]['delete_lesson']:
                    if ':' not in message.text.strip():
                        await bot.send_message(message.chat.id,
                                               text='❗Неправильний формат дати уроку. Спробуйте ще раз')
                        raise SyntaxError

                    state = admin.delete_lesson(message.text.strip())
                    await bot.send_message(message.chat.id,
                                           text='Урок видалено 😆' if state else '😅 Такого уроку немає в базі')
                    admin.edit_lesson = False

                else:
                    await bot.send_message(message.chat.id, text='😅 Команда не вибрана')

            else:
                if teachers_vars[current_user]['name_expected']:
                    if len(message.text.split()) != 2 or '@' not in message.text or ', ' not in message.text \
                            or message.text.index('@') < message.text.index(','):
                        await bot.send_message(message.chat.id,
                                               text='❗Неправильний формат вводу імені. Спробуйте ще раз')
                        raise SyntaxError

                    admin.name = message.text.strip()

                    subjs_kb = admin.create_kb(
                        ('Математика', 'subject Математика'), ('Укр.мова', 'subject Укр.мова'),
                        ('Англ.мова', 'subject Англ.мова'), ('Далі ➡️', 'subject Далі ➡️'),
                        kb_type='inline'
                    )

                    await bot.send_message(message.chat.id, text='🔀 Виберіть предмети, на яких ви спеціалізуєтесь:',
                                           reply_markup=subjs_kb)

                    teachers_vars[current_user]['name_expected'] = False
                    teachers_vars[current_user]['selecting_expected'] = True

                elif teachers_vars[current_user]['schedule_expected']:
                    admin.schedule = message.text.strip()
                    admin.check_schedule(admin.schedule)

                    admin.add_teacher(name=admin.name, subjects=', '.join(admin.subjects),
                                      classes=','.join(sorted(admin.classes)), schedule=admin.schedule.strip())

                    funcs_kb = admin.create_kb(
                        'Мій розклад 📅', 'Уроки 📚',
                        'Змінити класи 🏫', 'Налаштування ⚙'
                    )

                    await bot.send_message(message.chat.id, text='Вітаю! Вас успішно додано у базу вчителів T&C! 😉',
                                           reply_markup=funcs_kb)

                    teachers_vars[current_user]['schedule_expected'] = False

        admin.update_teacher_vars(teachers_vars)

    except (IndexError, ValueError):
        await bot.send_message(message.chat.id, text='❗Неправильний формат вхідних даних. Спробуйте ще раз')

    except SyntaxError:
        pass


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('subject'))
async def subjects_keyboard_callback_data_handler(call: types.CallbackQuery):
    global current_user

    if current_user != f'@{call.message.from_user.username}' \
            and f'@{call.message.from_user.username}' != '@tac_teachers_bot':
        current_user = f'@{call.message.from_user.username}'
        admin.switch_user(f'@{call.message.from_user.username}')

    if call.data == 'subject Далі ➡️':
        classes_kb = admin.create_kb(
            ('1', 'class 1'), ('2', 'class 2'), ('3', 'class 3'), ('4', 'class 4'), ('5', 'class 5'), ('6', 'class 6'),
            ('7', 'class 7'), ('8', 'class 8'), ('9', 'class 9'), ('10', 'class 10'), ('11', 'class 11'),
            ('Назад ⬅️', 'class Назад ⬅️'), ('Продовжити ➡️', 'class Продовжити ➡️'),
            kb_type='inline', tick_places=admin.classes
        )

        await bot.edit_message_text(chat_id=call.message.chat.id, text='🔀 Виберіть класи:',
                                    message_id=call.message.message_id, reply_markup=classes_kb)

    else:
        subj = call.data.split()[1]
        if subj not in admin.subjects:
            admin.subjects.append(subj)
        else:
            admin.subjects.remove(subj)

        subjs_kb = admin.create_kb(
            ('Математика', 'subject Математика'), ('Укр.мова', 'subject Укр.мова'),
            ('Англ.мова', 'subject Англ.мова'), ('Далі ➡️', 'subject Далі ➡️'),
            kb_type='inline', tick_places=admin.subjects
        )

        try:
            await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                        text='🔀 Виберіть предмети, на яких ви спеціалізуєтесь:', reply_markup=subjs_kb)
        except MessageNotModified:
            pass


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('class'))
async def classes_keyboard_callback_data_handler(call: types.CallbackQuery):
    global current_user

    if current_user != f'@{call.message.from_user.username}' \
            and f'@{call.message.from_user.username}' != '@tac_teachers_bot':
        current_user = f'@{call.message.from_user.username}'
        admin.switch_user(f'@{call.message.from_user.username}')

    with open('teachers_vars.json') as f:
        teachers_vars = json.load(f)

        if call.data == 'class Назад ⬅️':
            subjs_kb = admin.create_kb(
                ('Математика', 'subject Математика'), ('Укр.мова', 'subject Укр.мова'),
                ('Англ.мова', 'subject Англ.мова'), ('Далі ➡️', 'subject Далі ➡️'),
                kb_type='inline', tick_places=admin.subjects
            )

            await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                        text='🔀 Виберіть предмети, на яких ви спеціалізуєтесь:', reply_markup=subjs_kb)

        elif call.data == 'class Продовжити ➡️':
            if not admin.subjects or not admin.classes:
                await bot.send_message(call.message.chat.id, text='❗Не вибрані предмети або класи')
            else:
                await bot.send_message(call.message.chat.id, text='Чудово! 😀 Тепер створіть свій розклад!')
                await bot.send_message(call.message.chat.id, text='🔡 Напишіть бажаний графік занять '
                                                                  'Кожен день/діапазон днів через ; '
                                                                  'Можна через ; та з нового рядочка, як у прикладі\n'
                                                                  'Перейти на новий рядочок Shift+Enter\n'
                                                                  'Приклад:\n'
                                                                  '08.06-10.06: 10.00-19.00;\n11.06: 12.00-16.00;\n'
                                                                  '12.06: 13.00-21.00;\n13.06, 14.06: 8.00-19.00')
                teachers_vars[current_user]['selecting_expected'] = False
                teachers_vars[current_user]['schedule_expected'] = True

        elif call.data == 'class Підтвердити ✅️':
            admin.edit_classes(','.join(sorted(admin.classes)))
            await bot.send_message(call.message.chat.id, text='Класи змінено 😆')

        else:
            curr_class = call.data.split()[1]
            if curr_class not in admin.classes:
                admin.classes.append(curr_class)
            else:
                admin.classes.remove(curr_class)

            if not teachers_vars[current_user]['new_classes_kb']:
                classes_kb = admin.create_kb(
                    ('1', 'class 1'), ('2', 'class 2'), ('3', 'class 3'), ('4', 'class 4'), ('5', 'class 5'),
                    ('6', 'class 6'), ('7', 'class 7'), ('8', 'class 8'), ('9', 'class 9'), ('10', 'class 10'),
                    ('11', 'class 11'), ('Назад ⬅️', 'class Назад ⬅️'), ('Продовжити ➡️', 'class Продовжити ➡️'),
                    kb_type='inline', tick_places=admin.classes
                )

            else:
                print(admin.classes)
                classes_kb = admin.create_kb(
                    ('1', 'class 1'), ('2', 'class 2'), ('3', 'class 3'), ('4', 'class 4'), ('5', 'class 5'),
                    ('6', 'class 6'), ('7', 'class 7'), ('8', 'class 8'), ('9', 'class 9'), ('10', 'class 10'),
                    ('11', 'class 11'), ('Підтвердити ✅️️', 'class Підтвердити ✅️'),
                    kb_type='inline', tick_places=admin.classes
                )

            try:
                await bot.edit_message_text(chat_id=call.message.chat.id, text='🔀 Виберіть класи:',
                                            message_id=call.message.message_id, reply_markup=classes_kb)
            except MessageNotModified:
                pass

    admin.update_teacher_vars(teachers_vars)

executor.start_polling(dp, skip_updates=True)
