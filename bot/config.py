from sqlobject import *
import json

class ActionColours(SQLObject):
    class sqlmeta:
        table = "action_colours"

    name = StringCol()
    colour = IntCol()


class MediaOnlyChannels(SQLObject):
    class sqlmeta:
        table = "media_only_channels"

    channel_id = BigIntCol()


class DialogflowChannels(SQLObject):
    class sqlmeta:
        table = "dialogflow_channels"

    channel_id = BigIntCol()


class DialogflowExceptionRoles(SQLObject):
    class sqlmeta:
        table = "dialogflow_exception_roles"

    role_id = BigIntCol()


class Dialogflow(SQLObject):
    data = JSONCol()


class Commands(SQLObject):
    name = StringCol()
    content = StringCol()
    attachment = StringCol(default=None)


class Crashes(SQLObject):
    name = StringCol()
    crash = StringCol()
    response = StringCol()


class ReservedCommands(SQLObject):
    class sqlmeta:
        table = "reserved_commands"

    name = StringCol()


class Misc(SQLObject):
    class sqlmeta:
        table = "miscellaneous"

    filter_channel = BigIntCol(default=None)
    mod_channel = BigIntCol(default=None)
    githook_channel = BigIntCol(default=None)
    prefix = StringCol(default=None)
    dialogflow_state = BoolCol(default=None)
    dialogflow_debug_state = BoolCol(default=None)


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
                    Dialogflow(data=i)
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
