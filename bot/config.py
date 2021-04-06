from sqlobject import *
import json


class RankRoles(SQLObject):
    class sqlmeta:
        table = "rank_roles"

    rank = IntCol()
    role_id = BigIntCol()

    @staticmethod
    def fetch_by_rank(rank):
        query = RankRoles.select(RankRoles.q.rank <= rank).orderBy("-rank")
        results = list(query)
        if results:
            return results[0].role_id
        else:
            return None

    @staticmethod
    def fetch_by_role(role_id):
        query = RankRoles.selectBy(role_id=role_id)
        results = list(query)
        if results:
            return results[0].rank
        else:
            return None


class Users(SQLObject):
    user_id = BigIntCol()
    full_name = StringCol()
    message_count = IntCol(default=0)
    xp_count = IntCol(default=0)
    rank = IntCol(default=0)
    rank_role_id = BigIntCol(default=None)
    accepts_dms = BoolCol(default=True)

    def as_dict(self):
        return dict(user_id=self.user_id, message_count=self.message_count, xp_count=self.xp_count,
                    rank_role_id=self.rank_role_id, rank=self.rank, full_name=self.full_name,
                    accepts_dms=self.accepts_dms)

    @staticmethod
    def fetch(user_id):
        query = Users.selectBy(user_id=user_id)
        results = list(query)
        if results:
            return results[0]
        else:
            return None

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
        if results:
            return query[0].colour
        else:
            return None


class MediaOnlyChannels(SQLObject):
    class sqlmeta:
        table = "media_only_channels"

    channel_id = BigIntCol()

    @staticmethod
    def fetch(channel_id):
        query = MediaOnlyChannels.selectBy(channel_id=channel_id)
        results = list(query)
        if results:
            return query[0].channel_id
        else:
            return None


class DialogflowChannels(SQLObject):
    class sqlmeta:
        table = "dialogflow_channels"

    channel_id = BigIntCol()

    @staticmethod
    def fetch(channel_id):
        query = DialogflowChannels.selectBy(channel_id=channel_id)
        results = list(query)
        if results:
            return query[0].channel_id
        else:
            return None


class DialogflowExceptionRoles(SQLObject):
    class sqlmeta:
        table = "dialogflow_exception_roles"

    role_id = BigIntCol()

    @staticmethod
    def fetch(role_id):
        query = DialogflowExceptionRoles.selectBy(role_id=role_id)
        results = list(query)
        if results:
            return query[0].role_id
        else:
            return None

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
        return dict(intent_id=self.intent_id, data=json.loads(str(self.data)), response=self.response,
                    has_followup=self.has_followup)

    @staticmethod
    def fetch(intent_id, data):
        query = DialogflowExceptionRoles.selectBy(intent_id=intent_id, data=data)
        results = list(query)
        if results:
            return query[0].as_dict()
        else:
            return None


class Commands(SQLObject):
    name = StringCol()
    content = StringCol()
    attachment = StringCol(default=None)

    def as_dict(self):
        return dict(name=self.name, content=self.content, attachment=self.attachment)

    @staticmethod
    def fetch(name):
        query = Commands.selectBy(name=name.lower())
        results = list(query)
        if results:
            return results[0].as_dict()
        else:
            return None


class Crashes(SQLObject):
    name = StringCol()
    crash = StringCol()
    response = StringCol()

    def as_dict(self):
        return dict(name=self.name, response=self.response, crash=self.crash)

    @staticmethod
    def fetch(name):
        query = Crashes.selectBy(name=name.lower())
        results = list(query)
        if results:
            return results[0].as_dict()
        else:
            return None

    @staticmethod
    def fetch_all():
        query = Crashes.select()
        results = list(query)
        return (crash.as_dict() for crash in results)


class ReservedCommands(SQLObject):
    class sqlmeta:
        table = "reserved_commands"

    name = StringCol()

    @staticmethod
    def fetch(name):
        query = ReservedCommands.selectBy(name=name.lower())
        results = list(query)
        if results:
            return True
        else:
            return False


class Misc(SQLObject):
    class sqlmeta:
        table = "miscellaneous"

    key = StringCol()
    value = JSONCol()

    @staticmethod
    def fetch(key):
        query = Misc.selectBy(key=key)
        results = list(query)
        if results:
            return results[0].value
        else:
            return None

    @staticmethod
    def change(key, value):
        query = Misc.selectBy(key=key)
        results = list(query)
        if results:
            results[0].value = value


def create_missing_tables():
    tables = {
        "users": Users,
        "rank_roles": RankRoles,
        "action_colours": ActionColours,
        "media_only_channels": MediaOnlyChannels,
        "dialogflow_channels": DialogflowChannels,
        "dialogflow_exception_roles": DialogflowExceptionRoles,
        "dialogflow": Dialogflow,
        "commands": Commands,
        "crashes": Crashes,
        "reserved_commands": ReservedCommands,
        "miscellaneous": Misc
    }
    for table in tables.values():
        table.createTable(ifNotExists=True)


def convert_old_config():
    reservedcommands = ["management commands", "special commands", "miscellaneous commands"]

    Misc(key="welcome_message", value="")
    Misc(key="latest_info", value="")
    Misc(key="base_rank_value", value=300)
    Misc(key="rank_value_multiplier", value=1.2)
    Misc(key="xp_gain_value", value=1)
    Misc(key="xp_gain_delay", value=2)
    Misc(key="main_guild_id", value=319164249333039114)
    Misc(key="levelling_state", value=False)

    with open("../config/config.json", "r") as file:
        cfg = json.load(file)
        for k, v in cfg.items():
            if k == "action colours":
                for n, c in v.items():
                    ActionColours(name=n, colour=c)
            elif k == "filter channel":
                Misc(key="filter_channel", value=v)
            elif k == "mod channel":
                Misc(key="mod_channel", value=v)
            elif k == "githook channel":
                Misc(key="githook_channel", value=v)
            elif k == "prefix":
                Misc(key="prefix", value=v)
            elif k == "media only channels":
                for i in v:
                    MediaOnlyChannels(channel_id=i)
            elif k == "dialogflow_channels":
                for i in v:
                    DialogflowChannels(channel_id=i)
            elif k == "dialogflow_exception_roles":
                for i in v:
                    DialogflowExceptionRoles(role_id=i)
            elif k == "dialogflow state":
                Misc(key="dialogflow_state", value=v)
            elif k == "dialogflow debug state":
                Misc(key="dialogflow_debug_state", value=v)
            elif k == "dialogflow":
                for i in v:
                    if not i["response"]:
                        i["response"] = None
                    if not i["data"]:
                        i["data"] = None
                    Dialogflow(intent_id=i["id"], data=json.dumps(i["data"]).replace("'", '"'), response=i["response"],
                               has_followup=i["has_followup"])
            elif k == "commands":
                for i in v:
                    Commands(name=i["command"], content=i["response"])
            elif k == "known crashes":
                for i in v:
                    Crashes(name=i["name"], crash=i["crash"], response=i["response"])
            elif k in reservedcommands:
                for i in v:
                    ReservedCommands(name=i["command"])
            else:
                raise Exception("found non supported config key : {}".format(k))
