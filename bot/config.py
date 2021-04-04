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
    message_count = IntCol()
    xp_count = IntCol()
    rank = IntCol()
    rank_role_id = BigIntCol()
    rankup_notifications = BoolCol(default=True)

    def as_dict(self):
        return dict(user_id=self.user_id, message_count=self.message_count, xp_count=self.xp_count,
                    rank_role_id=self.rank_role_id, rank=self.rank, full_name=self.full_name,
                    rankup_notifications=self.rankup_notifications)

    @staticmethod
    def fetch(user_id):
        query = Users.selectBy(user_id=user_id)
        results = list(query)
        if results:
            return results[0]
        else:
            return None


class ActionColours(SQLObject):
    class sqlmeta:
        table = "action_colours"

    name = StringCol()
    colour = IntCol()


def get_action_colour(name):
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

    welcome_message = StringCol(default=None)
    latest_info = StringCol(default=None)
    filter_channel = BigIntCol(default=None)
    mod_channel = BigIntCol(default=None)
    githook_channel = BigIntCol(default=None)
    prefix = StringCol(default=None)
    dialogflow_state = BoolCol(default=None)
    dialogflow_debug_state = BoolCol(default=None)
    base_rank_value = IntCol(default=None)
    rank_value_multiplier = FloatCol(default=None)
    xp_gain_value = IntCol(default=None)
    xp_gain_delay = IntCol(default=None)
    main_guild_id = BigIntCol(default=None)

    @staticmethod
    def get_main_guild_id():
        return list(Misc.select(sqlbuilder.ISNOTNULL(Misc.q.main_guild_id)))[0].main_guild_id

    @staticmethod
    def set_main_guild_id(main_guild_id):
        list(Misc.select(sqlbuilder.ISNOTNULL(Misc.q.main_guild_id)))[0].main_guild_id = main_guild_id

    @staticmethod
    def get_xp_gain_value():
        return list(Misc.select(sqlbuilder.ISNOTNULL(Misc.q.xp_gain_value)))[0].xp_gain_value

    @staticmethod
    def set_xp_gain_value(xp_gain_value):
        list(Misc.select(sqlbuilder.ISNOTNULL(Misc.q.xp_gain_value)))[0].xp_gain_value = xp_gain_value

    @staticmethod
    def get_xp_gain_delay():
        return list(Misc.select(sqlbuilder.ISNOTNULL(Misc.q.xp_gain_delay)))[0].xp_gain_delay

    @staticmethod
    def set_xp_gain_delay(xp_gain_delay):
        list(Misc.select(sqlbuilder.ISNOTNULL(Misc.q.xp_gain_delay)))[0].xp_gain_delay = xp_gain_delay

    @staticmethod
    def get_base_rank_value():
        return list(Misc.select(sqlbuilder.ISNOTNULL(Misc.q.base_rank_value)))[0].base_rank_value

    @staticmethod
    def set_base_rank_value(base_rank_value):
        list(Misc.select(sqlbuilder.ISNOTNULL(Misc.q.base_rank_value)))[0].base_rank_value = base_rank_value

    @staticmethod
    def get_rank_value_multiplier():
        return list(Misc.select(sqlbuilder.ISNOTNULL(Misc.q.rank_value_multiplier)))[0].rank_value_multiplier

    @staticmethod
    def set_rank_value_multiplier(rank_value_multiplier):
        list(Misc.select(sqlbuilder.ISNOTNULL(Misc.q.rank_value_multiplier)))[0].rank_value_multiplier = rank_value_multiplier

    @staticmethod
    def get_welcome_message():
        return list(Misc.select(sqlbuilder.ISNOTNULL(Misc.q.welcome_message)))[0].welcome_message

    @staticmethod
    def set_welcome_message(welcome_message):
        list(Misc.select(sqlbuilder.ISNOTNULL(Misc.q.welcome_message)))[0].welcome_message = welcome_message

    @staticmethod
    def get_latest_info():
        return list(Misc.select(sqlbuilder.ISNOTNULL(Misc.q.latest_info)))[0].latest_info

    @staticmethod
    def set_latest_info(latest_info):
        list(Misc.select(sqlbuilder.ISNOTNULL(Misc.q.latest_info)))[0].latest_info = latest_info

    @staticmethod
    def get_filter_channel():
        return list(Misc.select(sqlbuilder.ISNOTNULL(Misc.q.filter_channel)))[0].filter_channel

    @staticmethod
    def set_filter_channel(channel_id: int):
        list(Misc.select(sqlbuilder.ISNOTNULL(Misc.q.filter_channel)))[0].filter_channel = channel_id

    @staticmethod
    def get_mod_channel():
        return list(Misc.select(sqlbuilder.ISNOTNULL(Misc.q.mod_channel)))[0].mod_channel

    @staticmethod
    def set_mod_channel(channel_id: int):
        list(Misc.select(sqlbuilder.ISNOTNULL(Misc.q.mod_channel)))[0].mod_channel = channel_id

    @staticmethod
    def get_githook_channel():
        return list(Misc.select(sqlbuilder.ISNOTNULL(Misc.q.githook_channel)))[0].githook_channel

    @staticmethod
    def set_githook_channel(channel_id: int):
        list(Misc.select(sqlbuilder.ISNOTNULL(Misc.q.githook_channel)))[0].githook_channel = channel_id

    @staticmethod
    def get_prefix():
        return list(Misc.select(sqlbuilder.ISNOTNULL(Misc.q.prefix)))[0].prefix

    @staticmethod
    def set_prefix(prefix: str):
        list(Misc.select(sqlbuilder.ISNOTNULL(Misc.q.prefix)))[0].prefix = prefix

    @staticmethod
    def get_dialogflow_state():
        return list(Misc.select(sqlbuilder.ISNOTNULL(Misc.q.dialogflow_state)))[0].dialogflow_state

    @staticmethod
    def set_dialogflow_state(state: bool):
        list(Misc.select(sqlbuilder.ISNOTNULL(Misc.q.dialogflow_state)))[0].dialogflow_state = state

    @staticmethod
    def get_dialogflow_debug_state():
        return list(Misc.select(sqlbuilder.ISNOTNULL(Misc.q.dialogflow_debug_state)))[0].dialogflow_debug_state

    @staticmethod
    def set_dialogflow_debug_state(state: bool):
        list(Misc.select(sqlbuilder.ISNOTNULL(Misc.q.dialogflow_debug_state)))[0].dialogflow_debug_state = state


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

    Misc(welcome_message="")
    Misc(latest_info="")
    Misc(base_rank_value=300)
    Misc(rank_value_multiplier=1.2)
    Misc(xp_gain_value=1)
    Misc(xp_gain_delay=2)
    Misc(main_guild_id=319164249333039114)

    with open("../config/config.json", "r") as file:
        cfg = json.load(file)
        for k, v in cfg.items():
            if k == "action colours":
                for n, c in v.items():
                    ActionColours(name=n, colour=c)
            elif k == "filter channel":
                Misc(filter_channel=v)
            elif k == "mod channel":
                Misc(mod_channel=v)
            elif k == "githook channel":
                Misc(githook_channel=v)
            elif k == "prefix":
                Misc(prefix=v)
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
                Misc(dialogflow_state=v)
            elif k == "dialogflow debug state":
                Misc(dialogflow_debug_state=v)
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
