from datetime import datetime, timedelta

def strToTime(string):
    string = string.replace(" ", "")
    now = datetime.now()
    then = datetime.now()
    if string.isnumeric():
        then += timedelta(days=int(string))
        return then

    if "second" in string:
        arg = string.split("seconds")[0]
        if arg.isnumeric():
            then += timedelta(seconds=int(arg))
            return then
        else:
            return False

    if "minute" in string:
        arg = string.split("minute")[0]
        if arg.isnumeric():
            then += timedelta(minutes=int(arg))
            return then
        else:
            return False

    if "day" in string:
        arg = string.split("day")[0]
        if arg.isnumeric():
            then += timedelta(days=int(arg))
            return then
        else:
            return False

    if "month" in string:
        arg = string.split("month")[0]
        if arg.isnumeric():
            then += timedelta(days=int(arg)*30)
            return then
        else:
            return False

    if "year" in string:
        arg = string.split("year")[0]
        if arg.isnumeric():
            then += timedelta(days=int(arg)*365)
            return then
        else:
            return False

    if "s" in string:
        arg = string.split("s")[0]
        if arg.isnumeric():
            then += timedelta(seconds=int(arg))
            return then
        else:
            return False

    if "m" in string:
        arg = string.split("min")[0]
        if arg.isnumeric():
            then += timedelta(minutes=int(arg))
            return then
        else:
            return False

    if "d" in string:
        arg = string.split("d")[0]
        if arg.isnumeric():
            then += timedelta(days=int(arg))
            return then
        else:
            return False

    if "y" in string:
        arg = string.split("y")[0]
        if arg.isnumeric():
            then += timedelta(days=int(arg)*365)
            return then
        else:
            return False