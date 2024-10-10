from __future__ import annotations

import json
import os
import pathlib
from numbers import Number
from typing import Optional, Any

import nextcord
from sqlobject import SQLObject, IntCol, BoolCol, JSONCol, BigIntCol, StringCol, FloatCol, sqlhub
from sqlobject.dberrors import DuplicateEntryError


class PermissionRoles(SQLObject):
    class sqlmeta:
        table = "role_perms"

    role_id = BigIntCol()
    perm_lvl = IntCol()
    role_name = StringCol()

    @staticmethod
    def fetch_ge_lvl(perm_lvl: int) -> list[PermissionRoles]:
        query = PermissionRoles.select(PermissionRoles.q.perm_lvl >= perm_lvl).orderBy("-perm_lvl")
        return list(query)

    @staticmethod
    def fetch_by_role(role_id: int) -> list[PermissionRoles]:
        query = PermissionRoles.selectBy(role_id=role_id)
        return list(query)


class RankRoles(SQLObject):
    class sqlmeta:
        table = "rank_roles"

    rank = IntCol()
    role_id = BigIntCol()

    @staticmethod
    def fetch_by_rank(rank: int) -> Optional[int]:
        query = RankRoles.select(RankRoles.q.rank <= rank).orderBy("-rank").getOne(None)
        return getattr(query, "role_id", None)

    @staticmethod
    def fetch_by_role(role_id: int) -> Optional[int]:
        query = RankRoles.selectBy(role_id=role_id).getOne(None)
        return getattr(query, "rank", None)


class XpRoles(SQLObject):
    class sqlmeta:
        table = "xp_roles"

    multiplier = FloatCol()
    role_id = BigIntCol()

    @staticmethod
    def fetch(role_id: int) -> Optional[XpRoles]:
        return XpRoles.selectBy(role_id=role_id).getOne(None)


class Users(SQLObject):
    user_id = BigIntCol()
    message_count = IntCol(default=0)
    xp_count = FloatCol(default=0)
    xp_multiplier = FloatCol(default=1)
    role_xp_multiplier = FloatCol(default=1)
    rank = IntCol(default=0)
    rank_role_id = BigIntCol(default=None)
    accepts_dms = BoolCol(default=True)

    def as_dict(self) -> dict[str, Any]:
        return dict(
            user_id=self.user_id,
            message_count=self.message_count,
            xp_count=self.xp_count,
            rank_role_id=self.rank_role_id,
            rank=self.rank,
            accepts_dms=self.accepts_dms,
        )

    @staticmethod
    def fetch(user_id: int) -> Users:
        return Users.selectBy(user_id=user_id).getOne(None)

    @staticmethod
    def create_if_missing(user: nextcord.User) -> Users:
        return Users.selectBy(user_id=user.id).getOne(False) or Users(user_id=user.id)


class ActionColours(SQLObject):
    class sqlmeta:
        table = "action_colours"

    name = StringCol()
    colour = IntCol()

    @staticmethod
    def fetch(name: str) -> Optional[int]:
        query = ActionColours.selectBy(name=name.lower()).getOne(None)
        return getattr(query, "colour", None)


class MediaOnlyChannels(SQLObject):
    class sqlmeta:
        table = "media_only_channels"

    channel_id = BigIntCol()

    @staticmethod
    def check(channel_id: int) -> bool:
        return bool(MediaOnlyChannels.selectBy(channel_id=channel_id).getOne(False))


class DialogflowChannels(SQLObject):
    class sqlmeta:
        table = "dialogflow_channels"

    channel_id = BigIntCol()

    @staticmethod
    def check(channel_id: int) -> bool:
        return bool(DialogflowChannels.selectBy(channel_id=channel_id).getOne(False))


class DialogflowExceptionRoles(SQLObject):
    class sqlmeta:
        table = "dialogflow_exception_roles"

    role_id = BigIntCol()

    @staticmethod
    def check(role_id: int) -> bool:
        return bool(DialogflowExceptionRoles.selectBy(role_id=role_id).getOne(False))

    @staticmethod
    def fetch_all() -> list[int]:
        query = DialogflowExceptionRoles.select()
        return [role.role_id for role in query.lazyIter()]


class Dialogflow(SQLObject):
    intent_id = StringCol()
    data = StringCol()
    response = StringCol()
    has_followup = BoolCol()

    def as_dict(self) -> dict[str, Any]:
        return dict(
            intent_id=self.intent_id,
            data=json.loads(str(self.data)) if self.data else None,
            response=self.response,
            has_followup=self.has_followup,
        )

    @staticmethod
    def fetch(intent_id: str, data: dict) -> Optional[Dialogflow]:
        return Dialogflow.selectBy(intent_id=intent_id, data=data).getOne(None)


type CommandsOrCrashesDict = dict[str, str | StringCol]


class Commands(SQLObject):
    name = StringCol()
    content = StringCol()
    attachment = StringCol(default=None)

    def as_dict(self) -> CommandsOrCrashesDict:
        return dict(name=self.name, content=self.content, attachment=self.attachment)

    @staticmethod
    def fetch(name: str) -> Optional[CommandsOrCrashesDict]:
        query: Optional[Commands]
        if query := Commands.selectBy(name=name.lower()).getOne(None):
            return query.as_dict()
        return None

    @classmethod
    def fetch_by(cls, col: str, val: str) -> Optional[CommandsOrCrashesDict]:
        # used by the search command to get a specific value if possible
        col, val = col.lower(), val.lower()
        if not isinstance(getattr(cls, col, None), property):
            raise KeyError("This is not a valid column!")

        query: Optional[Commands] = cls.selectBy(**{col: val}).getOne(None)
        if query is None:
            return None
        return query.as_dict()

    @staticmethod
    def fetch_all() -> list[CommandsOrCrashesDict]:
        query = Commands.selectBy()
        return [cmd.as_dict() for cmd in query.lazyIter()]


class Crashes(SQLObject):
    name = StringCol()
    crash = StringCol()
    response = StringCol()

    def as_dict(self) -> CommandsOrCrashesDict:
        return dict(name=self.name, response=self.response, crash=self.crash)

    @staticmethod
    def fetch(name: str) -> Optional[CommandsOrCrashesDict]:
        query: Optional[Crashes]
        if (query := Crashes.selectBy(name=name.lower()).getOne(None)) is not None:
            return query.as_dict()
        return None

    @classmethod
    def fetch_by(cls, col: str, val: str) -> Optional[CommandsOrCrashesDict]:
        col, val = col.lower(), val.lower()
        if not isinstance(getattr(cls, col), property):
            raise KeyError("This is not a valid column!")

        query: Optional[Crashes] = cls.selectBy(**{col: val}).getOne(None)
        if query is None:
            return None
        return query.as_dict()

    @staticmethod
    def fetch_all() -> list[CommandsOrCrashesDict]:
        query = Crashes.selectBy()
        return [crash.as_dict() for crash in query.lazyIter()]


class ReservedCommands(SQLObject):
    class sqlmeta:
        table = "reserved_commands"

    name = StringCol()

    @staticmethod
    def check(name: str) -> bool:
        query = ReservedCommands.selectBy(name=name.lower()).getOne(False)
        return bool(query)


type JSONValue = Number | bool | str | list | dict


class Misc(SQLObject):
    class sqlmeta:
        table = "miscellaneous"

    key = StringCol()
    value = JSONCol()

    @staticmethod
    def fetch(key: str) -> Optional[JSONValue]:
        query = Misc.selectBy(key=key).getOne(None)
        return getattr(query, "value", None)

    @staticmethod
    def change(key: str, value: JSONValue):
        query = Misc.selectBy(key=key).getOne(None)
        if query is not None:
            query.value = value

    @staticmethod
    def create_or_change(key: str, value: JSONValue):
        query: Optional[Misc] = Misc.selectBy(key=key).getOne(None)
        if query is None:
            Misc(key=key, value=value)
        else:
            query.value = value


def migrate():
    current_migration_rev = Misc.fetch("migration_rev")
    if current_migration_rev is None:
        current_migration_rev = 0

    migrations_dir = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))
    migrations_filenames = list(migrations_dir.glob("migrations/*-*.up.sql"))
    valid_migrations = [
        migration for migration in migrations_filenames if _migration_rev(migration) > current_migration_rev
    ]

    for migration in valid_migrations:
        sqlhub.processConnection.query(migration.read_text())

    try:
        Misc.create_or_change("migration_rev", _migration_rev(migrations_filenames[0]))
    except DuplicateEntryError as e:
        print(f"UNABLE TO RUN MIGRATION DUE TO {e}")


def _migration_rev(filepath: pathlib.Path) -> int:
    return int(filepath.name.split("-")[0])
