#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging as log

import telegram as tm
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler
import human
import fsm


log.basicConfig(format='%(asctime)s - %(message)s', level=log.DEBUG)


def handle_update(bot, update):
    user = human.by_id(update.message.from_user.id)

    trigger = fsm.TelegramTrigger()
    trigger.bot = bot
    trigger.user = user
    trigger.update = update

    user.state_machine.fire(trigger)


def create_bot():
    updater = Updater(token=os.environ['TELEGRAM_TOKEN'])
    updater.dispatcher.add_handler(CommandHandler('start', handle_update))
    updater.dispatcher.add_handler(MessageHandler(Filters.text|Filters.contact,handle_update))
    unknown_handler = MessageHandler(Filters.command, handle_update)
    updater.dispatcher.add_handler(unknown_handler)

    return updater


def start_polling_bot():
    bot = create_bot()
    bot.start_polling()

    return bot


def start_webhook_bot():
    bot = create_bot()
    webhook_port = int(os.environ['WEBHOOK_PORT'])

    bot.start_webhook(listen='0.0.0.0', port=webhook_port)
    return bot


if __name__ == '__main__':
    start_polling_bot()
