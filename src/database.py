from typing import NoReturn, Optional, TypedDict, List, cast
from pymongo import MongoClient

from dotenv import load_dotenv
from os import environ as env
load_dotenv(override=True)


class Settings(TypedDict):
    public: bool
    shown_nickname: str


class GCData(TypedDict):
    _id: str
    created: int
    deleted: bool
    last_active: int
    members: List[str]
    nickname: Optional[str]
    owner: Optional[str]
    type: int


class GroupChat(TypedDict):
    _id: str
    data: GCData
    bans: list
    settings: Settings



class Database:
    db = MongoClient(host=env["database_host"], port=int(env["database_port"])).gcutils

    def __new__(cls) -> NoReturn:
        raise Exception("Database is a singleton")

    def __init__(self):
        raise Exception("Database is a singleton")

    @classmethod
    def get_groupchat(self, id) -> Optional[GroupChat]:  # type: ignore
        return self.db.groupchats.find_one({"_id": id})

    @classmethod
    async def create_groupchat(self, bot, gc, public=False, shown_nickname=None) -> GroupChat:  # type: ignore
        if gc is None:
            gc = (await bot.get_chat(id).fetch()).data.to_dict()  # type: ignore[unknownPylancereportGeneralTypeIssues]

        groupchat = GroupChat(
            _id=gc["_id"],
            data=gc,
            bans=[],
            settings={
              "public": public,
              "shown_nickname": shown_nickname if shown_nickname is not None else gc["nickname"]
            }
        )

        resp = self.db.groupchats.insert_one({**groupchat})
        if resp is None:
            raise Exception("Failed to create groupchat")

        return groupchat

    @classmethod
    async def update_groupchat(self, bot, gc, public=False, shown_nickname=None) -> GroupChat:  # type: ignore
        if gc is None:
            gc = (await bot.get_chat(id).fetch()).data.to_dict()  # type: ignore[unknownPylancereportGeneralTypeIssues]

        resp = self.db.groupchats.update_one({"_id": gc["_id"]}, {"$set": {
            "data": gc,
            "settings": {
              "public": public,
              "shown_nickname": shown_nickname if shown_nickname is not None else gc["nickname"]
            }
        }})

        if resp is None:
            raise Exception("Failed to update groupchat")

        return gc

    @classmethod
    def delete_groupchat(self, id):  # type: ignore
        return self.db.groupchats.delete_one({"_id": id}).deleted_count == 1

    @classmethod
    def get_all_groupchats(self) -> List[GroupChat]:  # type: ignore
        return cast(List[GroupChat], self.db.groupchats.find({}))
