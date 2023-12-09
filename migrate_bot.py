
import asyncio
from MeowerBot import Bot, cbids
import logging

logging.basicConfig(level=logging.DEBUG)

bot1 = Bot()
bot2 = Bot()


BOT1 = ["GCInvite", ""]
BOT2 = ["gc", ""]


@bot2.listen(cbids.login)
async def login(token): # type: ignore # noqa
    chats = (await bot1.api.client.get("/chats/?autoget")).json()

    for chat in chats["autoget"]:
        await bot1.api.chats.add_user(chat["_id"], bot2.username)


@bot1.listen(cbids.login)
async def login(token): # type: ignore # noqa
    asyncio.create_task(bot2.start(*BOT2))


bot1.run(*BOT1)
