from src.orchestration.message import BaseMessage


class BaseChat:
    def __init__(self):
        # so at least with deepseek, it looks like
        # they cache automatically, so we don't have to worry about that
        # for now.
        #
        # TODO: user ids or usernames for messaging
        # to track which user/assistant sent a message
        self.messages = []

    @staticmethod
    def from_messages(messages: list, *args, **kwargs):
        new_chat = BaseChat(*args, **kwargs)
        new_chat.messages = messages
        return new_chat

    def get_messages(self):
        return [
            {
                # TODO: dynamically set role
                "role": x.role,
                "content": x.content,
            }
            for x in self.messages
        ]  # copy.deepcopy(self.messages)

    def was_created_at(self):
        return self.messages[0].created_at

    def was_last_updated_at(self):
        return self.messages[-1].created_at

    def add_message(self, *args, **kwargs):
        return self.messages.append(BaseMessage(*args, **kwargs))
