from croniter import croniter
from datetime import datetime

import asyncio


class Heartbeat:
    """
    Heartbeat runs a callback function every X seconds, according to cron
    syntax "* * * * *"
    """

    def __init__(self, cron, callback):
        self.cron = cron
        self.callback = callback
        self.current = None

    def get_next(self):
        return croniter(self.cron, datetime.now())

    def wait_until_datetime(self, target_datetime):
        now = datetime.now()
        delta = (target_datetime - now).total_seconds()
        if delta > 0:
            return asyncio.sleep(delta)
        return asyncio.sleep(0)

    async def daemon(self):
        while True:
            await self.wait_until_datetime(self.get_next())
            await self.abeat()

    def beat(self):
        # NOTE: callback is invoked without task context.
        # we should probably also save task data incase program stops suddenly
        return self.callback()

    def start(self):
        if self.current:
            raise RuntimeError("Heartbeat already running")
        self.current = asyncio.create_task(self.daemon())
        return self.current

    def stop(self):
        if self.current:
            # stop asyncio create_task object.
            return self.current.cancel()
        return None  # no heartbeat to kill
