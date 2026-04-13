import time


class BaseMessage:
    def __init__(self, role, content, userid=0, username=""):
        # NOTE: role is mostly temporary, we should dynamically set roles based on
        # each agent, so that they see every other agent's messages as from a "user"
        # atm, this is _mostly_ temporary, but this is good to differentiate from
        # human and AI messages anyway.
        self.role = role
        self.content = content
        self.userid = userid
        self.username = username
        # TODO: verify that this should be time, or datetime. I think
        # datetime but I'm leaving that task for someone else
        self.created_at = time.time()
