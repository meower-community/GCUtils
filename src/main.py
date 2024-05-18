from typing import Literal, Tuple, Union
from MeowerBot import Bot, cbids # type: ignore # noqa
from MeowerBot.context import Post
from MeowerBot.data.generic import UUID
from MeowerBot.ext.help import Help
from os import environ as env
from dotenv import load_dotenv
import asyncio
import logging

from httpx import get

from database import Database

load_dotenv(override=True)

logging.basicConfig(level=logging.DEBUG)

bot = Bot(prefix="@gc ")


@bot.command(name="join", args=1)
async def join(ctx, gc_id: str):
    """
    Join a group chat.

    Args:
        gc_id (str): The ID of the group chat.

    Returns:
        None
    """

    gc = await bot.get_chat(gc_id).fetch()

    if not gc:
        Database.delete_groupchat(gc_id)

        return await ctx.send_msg("Cannot add you to that GC")

    groupchat = Database.get_groupchat(gc_id)
    if groupchat is None:
        return await ctx.send_msg("That Group Chat does not exist, or is private")

    if not groupchat["settings"]["public"]:
        return await ctx.send_msg("That Group Chat does not exist, or is private")

    if ctx.message.user.username in groupchat["bans"]:
        return await ctx.send_msg("You are banned from that Group Chat")


    _gc = await bot.api.chats.add_user(UUID(gc_id), ctx.message.user.username)
    if _gc[1] != 200:
        await ctx.send_msg("Hold on... Creating a new group chat to fit you")
        _gc = await Database.move_gcs(bot, gc_id)
        if _gc is None:
            return await ctx.send_msg("Could not create a new group chat")

        await bot.api.chats.add_user(UUID(_gc["_id"]), ctx.message.user.username)
        gc_id = _gc["_id"] + " (moved) "
        push()

    await ctx.send_msg(f"Successfully added you to {gc.nickname} ({gc_id})")



type arguments = Union[Literal["--public"], Literal["--shown_nickname"], str, bool]


def _update(args: Tuple[arguments, ...]):
    setting = None
    ret = {}
    for i in args:
        if i == "--public":
            ret["public"] = True
        elif i == "--shown_nickname":
            setting = "shown_nickname"
        else:
            ret[setting] = i

    return ret


@bot.command(name="setup")
async def setup(ctx, *args: arguments):
    """Sets up a group chat for the moderation and joining system

    Options:
        --public: Make the GC public
        --shown_nickname <nickname> The nickname that should be shown in the group chat
    """
    gc = await ctx.message.chat.fetch()
    if ctx.message.user.username != gc.owner:
        return await ctx.send_msg("You must be the gc owner to setup this bot!")


    await Database.create_groupchat(bot, gc.data.to_dict(), **_update(args))

    await ctx.send_msg("Setup Successfully")


@bot.command(name="ban", args=1)
async def ban(ctx, user):
    gc = Database.get_groupchat(ctx.message.chat.id)
    if gc is None:
        return await ctx.send_msg("You need to register your group chat first!")

    if ctx.message.user.username != gc["owner"]:
        return await ctx.send_msg("You must be the gc owner to use this command!")

    gc["bans"].append(user)
    await ctx.send_msg("User Banned!")


@bot.command(name="unban", args=1)
async def unban(ctx, user):
    gc = Database.get_groupchat(ctx.message.chat.id)
    if gc is None:
        return await ctx.send_msg("You need to register your group chat first!")

    if ctx.message.user.username != gc["owner"]:
        return await ctx.send_msg("You must be the gc owner to use this command!")

    gc["bans"].remove(user)
    await ctx.send_msg("User Unbanned!")


async def edit(ctx, *args: arguments):
    gc = await ctx.message.chat.fetch()
    if ctx.message.user.username != gc.owner:
        return await ctx.send_msg("You must be the gc owner to use this command!")

    # get the groupchat
    db_gc = Database.get_groupchat(ctx.message.chat.id)
    if db_gc is None:
        return await ctx.send_msg("You need to register your group chat first!")


    await Database.update_groupchat(bot, gc.data.to_dict(), **{
        **db_gc["settings"],
        **_update(args)}
    )

    await ctx.send_msg("Setting Changed!")

bot.command("edit")(edit)
bot.command("update")(edit)


@bot.event
async def login(token):
    print("ready!")

@bot.listen(cbids.message)
async def on_message(msg: Post):
    if msg.user.username == bot.username:
        return
    if msg.data.startswith("@gc"):
        return

    gc = Database.get_groupchat(msg.chat.id)
    if gc is None:
        return

    coros = []
    for gc_id in gc["bridges"]:
        coros.append(bot.api.send_post(gc_id, f"{msg.user.username}: {msg.data}"))
    await asyncio.gather(*coros)

def push():
    get("http://localhost:2400/rerender")

async def push_changes():
    while True:
        await asyncio.sleep(60)
        push()

async def main():
    t = asyncio.create_task(push_changes()) # type: ignore # noqa

    bot.register_cog(Help(bot))
    await bot.start(env["username"], env["password"])

if __name__ == "__main__":
    asyncio.run(main())
