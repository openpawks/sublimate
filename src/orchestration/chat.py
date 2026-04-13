import copy


class Chat:
    def __init__(self):
        # so at least with deepseek, it looks like
        # they cache automatically, so we don't have to worry about that
        # for now.
        self.messages = []

    @staticmethod
    def from_messages(messages: list, *args, **kwargs):
        new_chat = Chat(*args, **kwargs)
        new_chat.messages = messages
        return new_chat

    def get_messages(self):
        return copy.deepcopy(self.messages)

    def add_message(self, message):
        return self.messages.append(message)
