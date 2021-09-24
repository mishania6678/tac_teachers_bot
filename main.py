from aiogram import Bot, Dispatcher, types, executor
from aiogram.utils.exceptions import MessageNotModified

from admin import Admin

import threading

bot = Bot('1941908944:AAH-74UPpJW4ZcxUwx67lZdDTi_5Sib_S3o')
dp = Dispatcher(bot)

admin = Admin()

CURRENT_USER = None


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    global CURRENT_USER

    if not admin.is_teacher(f'@{message.from_user.username}'):
        await bot.send_message(message.chat.id, text='⚠ Цим ботом можуть користуватися лише викладачі онлайн-школи T&C')

    elif admin.teacher_registered(f'@{message.from_user.username}'):
        if CURRENT_USER != f'@{message.from_user.username}' and CURRENT_USER != '@tac_teachers_bot':
            CURRENT_USER = f'@{message.from_user.username}'
            admin.switch_user(CURRENT_USER)

    else:
        admin.__init__()

        if CURRENT_USER != f'@{message.from_user.username}' and CURRENT_USER != '@tac_teachers_bot':
            CURRENT_USER = f'@{message.from_user.username}'
            admin.switch_user(CURRENT_USER)

        admin.memory = {
            "name_expected": True, "selecting_expected": False, "schedule_expected": False, "new_classes_kb": False,
            "edit_classes": False, "edit_schedule": False, "add_lesson": False, "edit_lesson": False,
            "delete_lesson": False, "show_lessons_on_date": False
        }

        admin.update_teacher_vars()

        threading.Thread(target=admin.remove_ended_lessons).start()

        await bot.send_message(message.chat.id, text='🔡 Введіть ваше ім\'я та нікнейм у телеграмі\n'
                                                     'Приклад: Коля, @nizhnitschek')


@dp.message_handler(content_types=['text'])
async def text_handler(message: types.Message):
    global CURRENT_USER

    if CURRENT_USER != f'@{message.from_user.username}' and f'@{message.from_user.username}' != '@tac_teachers_bot':
        CURRENT_USER = f'@{message.from_user.username}'
        admin.switch_user(CURRENT_USER)

    try:
        if not (admin.memory['name_expected'] or admin.memory['selecting_expected']
                or admin.memory['schedule_expected']):
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
                admin.reset_teacher_vars(except_var='new_classes_kb')

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
                admin.reset_teacher_vars(except_var='edit_schedule')
                await bot.send_message(message.chat.id, text=f'🔡 Відправте відредагований розклад\n'
                                                             f'`{admin.schedule}`', parse_mode='Markdown')

            elif message.text == 'Подивитися уроки на сьогодні 👁':
                await bot.send_message(message.chat.id, text=admin.show_lessons())

            elif message.text == 'Подивитися уроки на дату 🗓':
                admin.reset_teacher_vars(except_var='show_lessons_on_date')
                await bot.send_message(message.chat.id, text='🔡 Введіть дату')

            elif message.text == 'Додати урок ➕':
                admin.reset_teacher_vars(except_var='add_lesson')
                await bot.send_message(message.chat.id, text='🔡 Введіть дату та час уроку\nПриклад: 08.06: 10.00')

            elif message.text == 'Видалити урок ➖':
                admin.reset_teacher_vars(except_var='delete_lesson')
                await bot.send_message(message.chat.id, text='🔡 Введіть дату та час уроку\nПриклад: 08.06: 10.00')

            elif message.text == 'Змінити урок ✏':
                admin.reset_teacher_vars(except_var='edit_lesson')
                await bot.send_message(message.chat.id, text='🔡 Введіть дату та час уроку, який треба змінити, '
                                                             'на той, на який треба змінити'
                                                             '\nПриклад: 08.06: 10.00 -> 08.06: 16.00')

            elif admin.memory['edit_schedule']:
                admin.check_schedule(message.text.strip())

                admin.schedule = message.text.strip()

                admin.edit_teacher_data('schedule', ''.join(admin.schedule))
                await bot.send_message(message.chat.id, text='Розклад змінено 😆')

                admin.memory['edit_schedule'] = False

            elif admin.memory['add_lesson']:
                admin.check_schedule(message.text.strip())

                admin.lessons.append(message.text.strip())
                admin.add_lesson(message.text.strip())
                await bot.send_message(message.chat.id, text='Урок додано 😆')
                admin.memory['add_lesson'] = False

            elif admin.memory['edit_lesson']:
                admin.check_schedule(message.text.split('->')[0].strip())
                admin.check_schedule(message.text.split('->')[1].strip())

                admin.lessons[admin.lessons.index(message.text.split('->')[0].strip())] = admin.lessons[
                    admin.lessons.index(message.text.split('->')[1].strip())]
                state = admin.edit_lesson(
                    message.text.split('->')[0].strip(),
                    message.text.split('->')[1].strip()
                )

                await bot.send_message(message.chat.id,
                                       text='Урок змінено 😆' if state else '😅 Введеної дати немає в базі')
                admin.memory['edit_lesson'] = False

            elif admin.memory['delete_lesson']:
                admin.check_schedule(message.text.strip())

                admin.lessons.remove(message.text.strip())
                state = admin.delete_lesson(message.text.strip())
                await bot.send_message(message.chat.id,
                                       text='Урок видалено 😆' if state else '😅 Такого уроку немає в базі')
                admin.memory['delete_lesson'] = False

            elif admin.memory['show_lessons_on_date']:
                await bot.send_message(message.chat.id, text=admin.show_lessons(date=message.text.strip()))

            else:
                await bot.send_message(message.chat.id, text='😅 Команда не вибрана')

        else:
            if admin.memory['name_expected']:
                if len(message.text.split()) != 2 or '@' not in message.text or ', ' not in message.text \
                        or message.text.index('@') < message.text.index(','):
                    await bot.send_message(message.chat.id,
                                           text='❗Неправильний формат вводу імені. Спробуйте ще раз')
                    raise SyntaxError

                admin.name = message.text.strip()
                admin.add_teacher_data('name', admin.name)

                subjs_kb = admin.create_kb(
                    ('Математика', 'subject Математика'), ('Укр.мова', 'subject Укр.мова'),
                    ('Англ.мова', 'subject Англ.мова'), ('Далі ➡️', 'subject Далі ➡️'),
                    kb_type='inline'
                )

                await bot.send_message(message.chat.id, text='🔀 Виберіть предмети, на яких ви спеціалізуєтесь:',
                                       reply_markup=subjs_kb)

                admin.reset_teacher_vars(except_var='selecting_expected')

            elif admin.memory['schedule_expected']:
                admin.check_schedule(message.text.strip())

                admin.schedule = message.text.strip()
                admin.add_teacher_data('schedule', admin.schedule)

                funcs_kb = admin.create_kb(
                    'Мій розклад 📅', 'Уроки 📚',
                    'Змінити класи 🏫', 'Налаштування ⚙'
                )

                await bot.send_message(message.chat.id, text='Вітаю! Вас успішно додано у базу вчителів T&C! 😉',
                                       reply_markup=funcs_kb)

                admin.memory['schedule_expected'] = False

        admin.update_teacher_vars()

    except (IndexError, ValueError):
        await bot.send_message(message.chat.id, text='❗Неправильний формат вхідних даних. Спробуйте ще раз')

    except SyntaxError:
        pass


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('subject'))
async def subjects_keyboard_callback_data_handler(call: types.CallbackQuery):
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

        admin.edit_teacher_data('subjects', ', '.join(admin.subjects))


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('class'))
async def classes_keyboard_callback_data_handler(call: types.CallbackQuery):
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
            await bot.send_message(call.message.chat.id,
                                   text='🔡Введіть бажаний графік занять, як показано на прикладі:\n'
                                        '❗️Дотримуйтесь зазначеного синтаксису, '
                                        'адже навіть якщо десь буде зайва кома, '
                                        'бот не зможе зчитати повідомлення.\n'
                                        'Дата(день та місяць) або період дат: години роботи.\n '
                                        'Приклад:\n'
                                        '08.09-10.09: 10.00-19.00;\n'
                                        '11.09: 12.00-16.00;\n'
                                        '12.06: 13.00-21.00;\n'
                                        '13.06, 14.06: 08.00-19.00\n')

            admin.reset_teacher_vars(except_var='schedule_expected')
            admin.edit_teacher_data('classes', ','.join(sorted(admin.classes)))

    elif call.data == 'class Підтвердити ✅️':
        admin.edit_teacher_data('classes', ','.join(sorted(admin.classes)))
        await bot.send_message(call.message.chat.id, text='Класи змінено 😆')

    else:
        curr_class = call.data.split()[1]
        if curr_class not in admin.classes:
            admin.classes.append(curr_class)
        else:
            admin.classes.remove(curr_class)

        if not admin.memory['new_classes_kb']:
            classes_kb = admin.create_kb(
                ('1', 'class 1'), ('2', 'class 2'), ('3', 'class 3'), ('4', 'class 4'), ('5', 'class 5'),
                ('6', 'class 6'), ('7', 'class 7'), ('8', 'class 8'), ('9', 'class 9'), ('10', 'class 10'),
                ('11', 'class 11'), ('Назад ⬅️', 'class Назад ⬅️'), ('Продовжити ➡️', 'class Продовжити ➡️'),
                kb_type='inline', tick_places=admin.classes
            )

        else:
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

        admin.edit_teacher_data('classes', ','.join(sorted(admin.classes)))

    admin.update_teacher_vars()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
