# -*- coding: utf-8 -*-


import logging as log
import re

import telegram as tm
from pidgey import convert_num_sys
import texts as tx


# -- base types -----------------------------------------------------------


class State(object):

    def on_trigger(self, trigger):
        pass

    def _on_trigger(self, trigger):
        log.debug('== ' + str(self))
        return self.on_trigger(trigger)

    def on_enter(self, trigger):
        pass

    def _on_enter(self, trigger):
        log.debug('-> ' + str(self))
        return self.on_enter(trigger)

    def on_exit(self, trigger):
        pass

    def _on_exit(self, trigger):
        log.debug('<- ' + str(self))
        return self.on_exit(trigger)


class Filter(object):

    def __init__(self):
        pass

    def on_process(self, current_state, trigger):
        pass

    def _on_process(self, current_state, trigger):
        log.debug(':: ' + type(self).__name__)
        return self.on_process(current_state, trigger)


class StateMachine(object):

    def __init__(self, user):
        self.state = BootStrapState()
        self.user = user
        self.filters = [StartFilter(),
                        FeedbackFilter(),
                        PoliteFilter()]

    def fire(self, trigger):
        trigger.user = self.user

        for f in self.filters:
            filtered_state = f._on_process(self.state, trigger)
            if filtered_state:
                self.to_state(filtered_state, trigger)
                return

        new_state = self.state._on_trigger(trigger)
        self.to_state(new_state, trigger)

    def to_state(self, new_state, trigger):
        if not new_state:
            return self.state

        if new_state == self.state:
            reenter_state = self.state._on_enter(trigger)
            self.to_state(reenter_state, trigger)
            return

        exit_state = self.state._on_exit(trigger)
        if exit_state:
            self.to_state(exit_state, trigger)
            return

        self.state = new_state

        enter_state = self.state._on_enter(trigger)
        if enter_state:
            self.to_state(enter_state, trigger)
            return


class TelegramTrigger(object):

    def __init__(self):
        self.user = None
        self.bot = None
        self.update = None

    def get_chat_id(self):
        return self.update.message.chat_id if self.update else None

    def get_txt(self):
        return self.update.message.text if self.update else None

    def get_name(self):
        user = self.update.message.from_user
        return user.first_name if user.first_name else user.username

    def send_msg(self, txt):
        self.bot.sendMessage(chat_id=self.chat_id,
                             text=txt,
                             disable_web_page_preview=True,
                             parse_mode=tm.ParseMode.MARKDOWN)

    def send_keys(self, txt, keyboard):
        reply_markup = tm.ReplyKeyboardMarkup(keyboard=keyboard,
                                              resize_keyboard=True,
                                              one_time_keyboard=True)

        self.bot.sendMessage(chat_id=self.chat_id,
                             text=txt,
                             disable_web_page_preview=True,
                             parse_mode=tm.ParseMode.MARKDOWN,
                             reply_markup=reply_markup)

    def send_photo(self, src):
        self.bot.sendPhoto(chat_id=self.chat_id, photo=src)

    # will call 'get_chat_id' when accessing like obj.chat_id
    chat_id = property(get_chat_id)
    txt = property(get_txt)
    name = property(get_name)


# -- states ---------------------------------------------------------------


class BootStrapState(State):

    def on_trigger(self, trigger):
        return RootState()


class RootState(State):

    def on_enter(self, trigger):
        trigger.send_keys(u'Из какой системы будем переводить?',
                          [[u'2ичной', u'8иричной',
                            u'10ичной', u'16еричной']])

    def on_trigger(self, trigger):
        f_num_sys = None

        msg = (u'двоичной|2|2ичной|bin')

        if tx.equals(trigger.txt, msg):
            f_num_sys = 2

        msg = (u'восьмеричной|8|8ичной|oct')

        if tx.equals(trigger.txt, msg):
            f_num_sys = 8

        msg = (u'десятичной|10|10ичной|dec')

        if tx.equals(trigger.txt, msg):
            f_num_sys = 10

        msg = (u'шестнадцатеричной|16|16ичной|hex')

        if tx.equals(trigger.txt, msg):
            f_num_sys = 16

        if not f_num_sys:
            trigger.send_msg(u'Извини, не понял')
            return self

        if f_num_sys:
            return AskSystemState(f_num_sys)

        return self


class AskSystemState(State):

    def __init__(self, f_num_sys):
        self.f_num_sys = f_num_sys

    def on_enter(self, trigger):
        trigger.send_keys(u'В какую?',
                        [[u'2ичной', u'8иричной',
                            u'10ичной', u'16еричной']])

    def on_trigger(self, trigger):
        t_num_sys = None

        msg = (u'двоичную|2|2ичную|bin')

        if tx.equals(trigger.txt, msg):
            t_num_sys = 2

        msg = (u'восьмеричную|8|8ичную|oct')

        if tx.equals(trigger.txt, msg):
            t_num_sys = 8

        msg = (u'десятичную|10|10ичную|dec')

        if tx.equals(trigger.txt, msg):
            t_num_sys = 10

        msg = (u'шестнадцатеричную|16|16ичную|hex')

        if tx.equals(trigger.txt, msg):
            t_num_sys = 16

        if not t_num_sys:
            trigger.send_msg(u'Извини, не понял')
            return self

        if t_num_sys:
            return AskNumberState(self.f_num_sys, t_num_sys)

        return self


class AskNumberState(State):

    numbers_rgx = re.compile(r'[^0-9]')

    def __init__(self, f_num_sys, t_num_sys):
        self.f_num_sys = f_num_sys
        self.t_num_sys = t_num_sys

    def on_enter(self, trigger):
        trigger.send_msg(u'Введи число')

    def on_trigger(self, trigger):
        try:
            val = int(AskNumberState.numbers_rgx.sub('', trigger.txt))
            return NumberCalculation(val, self.f_num_sys, self.t_num_sys)
        except ValueError:
            return self


class NumberCalculation(State):

    def __init__(self, val, f_num_sys, t_num_sys):
        self.val = val
        self.f_num_sys = f_num_sys
        self.t_num_sys = t_num_sys

    def on_enter(self, trigger):
        if self.f_num_sys and self.t_num_sys:
            try:
                self.val = str(self.val)
                msg = convert_num_sys(self.val, self.f_num_sys, self.t_num_sys)
                trigger.send_msg(u'Результат: ')
                trigger.send_msg(str(msg))
                trigger.send_keys(u'Ещё хочешь? :)',
                                  [[u'Да', u'Хватит']])
            except ValueError:
                trigger.send_msg('Странное число. Попробуй ввести ещё раз')
                return AskNumberState(self.f_num_sys, self.t_num_sys)

            except TypeError:
                trigger.send_msg('Это не число. Меня обманули')
                return AskNumberState(self.f_num_sys, self.t_num_sys)

    def on_trigger(self, trigger):
        if tx.equals(trigger.txt, u'хватит|нет|н|-'):
            return trigger.send_msg('Cya, {}! :3'.format(trigger.name))
        if tx.equals(trigger.txt, u'покажи ещё|покажи еще|ещё|еще|да|+|д'):
            return RootState()


class FeedbackState(State):

    def on_enter(self, trigger):
        trigger.send_msg(u'В целях улучшения качества обслуживания '
                         u'все разговоры записываются ;) Напиши свои мысли')

    def on_trigger(self, trigger):
        log.warn('feedback: ' + str(trigger.update))
        trigger.send_msg(u'Спасибо!')

        return RootState()


# -- filters  -------------------------------------------------------------

class StartFilter(Filter):

    def on_process(self, current_state, trigger):
        if tx.is_command(trigger.txt, '/start|/help'):

            trigger.send_msg(u'Если у тебя что-то пошло не так '
                             u'или ты хочешь поделиться с нами своими '
                             u'мыслями - просто напиши в чате /feedback '
                             u'и опиши, что случилось. '
                             u'Мы обязательно что-нибудь придумаем!')

            return RootState()


class PoliteFilter(Filter):
    def on_process(self, current_state, trigger):
        if tx.equals(trigger.txt, u'привет|здравствуй|хай|hello|hallo|hi'):
            trigger.send_msg(u'Привет, {}! ^^'.format(trigger.name))

            if type(current_state) == BootStrapState:
                return RootState()

            return current_state

        byes = (u'пока|до свидания|бб|66|бай-бай|пока-пока'
                u'|goodbye|спокойной ночи')

        if tx.equals(trigger.txt, byes):
            trigger.send_msg(u'Пока, {}! :3'.format(trigger.name))
            return BootStrapState()


class FeedbackFilter(Filter):

    def on_process(self, current_state, trigger):
        if tx.is_command(trigger.txt, '/feedback'):
            return FeedbackState()
