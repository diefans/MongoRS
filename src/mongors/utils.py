import simplejson as json
import datetime
import time


def defaults(obj):
    if isinstance(obj, datetime.datetime):
        return time.mktime(obj.timetuple()) + obj.microsecond * 10 ** -6

def dumps(data):
    return json.dumps(data, default=defaults)
