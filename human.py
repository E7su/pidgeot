# -*- coding: utf-8 -*-

import fsm


# temporary cache impl
users_cache = {}


class User(object):

    def __init__(self, telegram_id):
        self.telegram_id = telegram_id
        self.state_machine = fsm.StateMachine(self)


def by_id(user_id):
    user = users_cache.get(user_id)

    if not user:
        user = User(user_id)
        users_cache[user_id] = user

    return user
