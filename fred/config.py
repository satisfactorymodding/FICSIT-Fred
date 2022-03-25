from sqlobject import *
import json


class PermissionRoles(SQLObject):
    class sqlmeta:
        table = "role_perms"

    role_id = BigIntCol()
    perm_lvl = IntCol()
    role_name = StringCol()

    @staticmethod
    def fetch_by_lvl(perm_lvl):
        query = PermissionRoles.select(PermissionRoles.q.perm_lvl >= perm_lvl).orderBy("-perm_lvl")
        return list(query)

    @staticmethod
    def fetch_by_role(role_id):
        query = PermissionRoles.selectBy(role_id=role_id)
        return list(query)


class RankRoles(SQLObject):
    class sqlmeta:
        table = "rank_roles"

    rank = IntCol()
    role_id = BigIntCol()

    @staticmethod
    def fetch_by_rank(rank):
        query = RankRoles.select(RankRoles.q.rank <= rank).orderBy("-rank")
        results = list(query)
        return results[0].role_id if results else None

    @staticmethod
    def fetch_by_role(role_id):
        query = RankRoles.selectBy(role_id=role_id)
        results = list(query)
        return results[0].rank if results else None


class XpRoles(SQLObject):
    class sqlmeta:
        table = "xp_roles"

    multiplier = FloatCol()
    role_id = BigIntCol()

    @staticmethod
    def fetch(role_id):
        query = XpRoles.selectBy(role_id=role_id)
        results = list(query)
        return results[0] if results else None


class Users(SQLObject):
    user_id = BigIntCol()
    full_name = StringCol()
    message_count = IntCol(default=0)
    xp_count = FloatCol(default=0)
    xp_multiplier = FloatCol(default=1)
    role_xp_multiplier = FloatCol(default=1)
    rank = IntCol(default=0)
    rank_role_id = BigIntCol(default=None)
    accepts_dms = BoolCol(default=True)

    def as_dict(self):
        return dict(
            user_id=self.user_id,
            message_count=self.message_count,
            xp_count=self.xp_count,
            rank_role_id=self.rank_role_id,
            rank=self.rank,
            full_name=self.full_name,
            accepts_dms=self.accepts_dms,
        )

    @staticmethod
    def fetch(user_id):
        query = Users.selectBy(user_id=user_id)
        results = list(query)
        return results[0] if results else None

    @staticmethod
    def create_if_missing(user):
        query = Users.selectBy(user_id=user.id)
        results = list(query)
        if results:
            return results[0]
        else:
            return Users(user_id=user.id, full_name=user.name + "#" + user.discriminator)


class ActionColours(SQLObject):
    class sqlmeta:
        table = "action_colours"

    name = StringCol()
    colour = IntCol()

    @staticmethod
    def fetch(name):
        query = ActionColours.selectBy(name=name.lower())
        results = list(query)
        return results[0].colour if results else None


class MediaOnlyChannels(SQLObject):
    class sqlmeta:
        table = "media_only_channels"

    channel_id = BigIntCol()

    @staticmethod
    def fetch(channel_id):
        query = MediaOnlyChannels.selectBy(channel_id=channel_id)
        results = list(query)
        return results[0].channel_id if results else None


class DialogflowChannels(SQLObject):
    class sqlmeta:
        table = "dialogflow_channels"

    channel_id = BigIntCol()

    @staticmethod
    def fetch(channel_id):
        query = DialogflowChannels.selectBy(channel_id=channel_id)
        results = list(query)
        return results[0].channel_id if results else None


class DialogflowExceptionRoles(SQLObject):
    class sqlmeta:
        table = "dialogflow_exception_roles"

    role_id = BigIntCol()

    @staticmethod
    def fetch(role_id):
        query = DialogflowExceptionRoles.selectBy(role_id=role_id)
        results = list(query)
        return results[0].role_id if results else None

    @staticmethod
    def fetch_all():
        query = DialogflowExceptionRoles.select()
        results = list(query)
        return [role.role_id for role in results]


class Dialogflow(SQLObject):
    intent_id = StringCol()
    data = StringCol()
    response = StringCol()
    has_followup = BoolCol()

    def as_dict(self):
        return dict(
            intent_id=self.intent_id,
            data=json.loads(str(self.data)) if self.data else None,
            response=self.response,
            has_followup=self.has_followup,
        )

    @staticmethod
    def fetch(intent_id, data):
        query = Dialogflow.selectBy(intent_id=intent_id, data=data)
        results = list(query)
        return results[0].as_dict() if results else None


class Commands(SQLObject):
    name = StringCol()
    content = StringCol()
    attachment = StringCol(default=None)

    def as_dict(self) -> dict:
        return dict(name=self.name, content=self.content, attachment=self.attachment)

    @staticmethod
    def fetch(name) -> dict | None:
        query = Commands.selectBy(name=name.lower())
        results = list(query)
        return results[0].as_dict() if results else None


class Crashes(SQLObject):
    name = StringCol()
    crash = StringCol()
    response = StringCol()

    def as_dict(self) -> dict:
        return dict(name=self.name, response=self.response, crash=self.crash)

    @staticmethod
    def fetch(name) -> dict | None:
        query = Crashes.selectBy(name=name.lower())
        results = list(query)
        return results[0].as_dict() if results else None

    @staticmethod
    def fetch_all() -> list[dict]:
        query = Crashes.selectBy()
        results = list(query)
        return [crash.as_dict() for crash in results]


class ReservedCommands(SQLObject):
    class sqlmeta:
        table = "reserved_commands"

    name = StringCol()

    @staticmethod
    def fetch(name):
        query = ReservedCommands.selectBy(name=name.lower())
        results = list(query)
        return bool(results)


class Misc(SQLObject):
    class sqlmeta:
        table = "miscellaneous"

    key = StringCol()
    value = JSONCol()

    @staticmethod
    def fetch(key):
        query = Misc.selectBy(key=key)
        results = list(query)
        return results[0].value if results else None

    @staticmethod
    def change(key, value):
        query = Misc.selectBy(key=key)
        results = list(query)
        if results:
            results[0].value = value
