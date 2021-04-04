from sqlobject import *
import json


class ActionColours(SQLObject):
    class sqlmeta:
        table = "action_colours"

    name = StringCol()
    colour = IntCol()


def get_action_colour(name):
    query = ActionColours.selectBy(name=name.lower())
    results = list(query)
    if len(results) > 0:
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
        if len(results) > 0:
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
        if len(results) > 0:
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
        if len(results) > 0:
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
    data = JSONCol()
    response = StringCol()
    has_followup = BoolCol()

    def as_dict(self):
        return dict(intent_id=self.intent_id, data=self.data, response=self.response, has_followup=self.has_followup)

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
        if len(results) > 0:
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
        if len(results) > 0:
            return dict(results[0])
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
        if len(results) > 0:
            return True
        else:
            return False


class Misc(SQLObject):
    class sqlmeta:
        table = "miscellaneous"

    filter_channel = BigIntCol(default=None)

    @staticmethod
    def get_filter_channel():
        return list(Misc.select(sqlbuilder.ISNOTNULL(Misc.q.filter_channel)))[0].filter_channel

    @staticmethod
    def set_filter_channel(channel_id: int):
        list(Misc.select(sqlbuilder.ISNOTNULL(Misc.q.filter_channel)))[0].filter_channel = channel_id

    mod_channel = BigIntCol(default=None)

    @staticmethod
    def get_mod_channel():
        return list(Misc.select(sqlbuilder.ISNOTNULL(Misc.q.mod_channel)))[0].mod_channel

    @staticmethod
    def set_mod_channel(channel_id: int):
        list(Misc.select(sqlbuilder.ISNOTNULL(Misc.q.mod_channel)))[0].mod_channel = channel_id

    githook_channel = BigIntCol(default=None)

    @staticmethod
    def get_githook_channel():
        return list(Misc.select(sqlbuilder.ISNOTNULL(Misc.q.githook_channel)))[0].githook_channel

    @staticmethod
    def set_githook_channel(channel_id: int):
        list(Misc.select(sqlbuilder.ISNOTNULL(Misc.q.githook_channel)))[0].githook_channel = channel_id

    prefix = StringCol(default=None)

    @staticmethod
    def get_prefix():
        return list(Misc.select(sqlbuilder.ISNOTNULL(Misc.q.prefix)))[0].prefix

    @staticmethod
    def set_prefix(prefix: str):
        list(Misc.select(sqlbuilder.ISNOTNULL(Misc.q.prefix)))[0].prefix = prefix

    dialogflow_state = BoolCol(default=None)

    @staticmethod
    def get_dialogflow_state(state: bool):
        list(Misc.select(sqlbuilder.ISNOTNULL(Misc.q.dialogflow_state)))[0].dialogflow_state = state

    dialogflow_debug_state = BoolCol(default=None)

    @staticmethod
    def get_dialogflow_debug_state(state: bool):
        list(Misc.select(sqlbuilder.ISNOTNULL(Misc.q.dialogflow_debug_state)))[0].dialogflow_debug_state = state


def create_missing_tables():
    tables = {
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
                    Dialogflow(intent_id=i["id"], data=i["data"], response=i["response"], has_followup=i["has_followup"])
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
