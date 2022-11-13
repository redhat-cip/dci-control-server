import csv
from datetime import datetime


def _get_csv(element, dict):
    e = dict.get(element, [])
    if e:
        e = e.strip().replace("\n", "").replace("\t", "")
        return list(csv.reader([e]))[0]
    return e


def _get_int(element, dict):
    e = dict.get(element, None)
    if e:
        return int(e)
    return e


def _get_datetime(element, dict):
    e = dict.get(element, None)
    if e:
        try:
            return datetime.strptime(e, "%Y-%m-%dT%H:%M:%S.%f")
        except ValueError:
            pass

        try:
            timestamp_in_ms = int(e)
            timestamp_in_second = timestamp_in_ms / 1000
            return datetime.fromtimestamp(timestamp_in_second)
        except ValueError:
            pass


def parse_args(args):
    _res = {
        "limit": _get_int("limit", args),
        "offset": _get_int("offset", args),
        "sort": _get_csv("sort", args),
        "where": _get_csv("where", args),
        "embed": _get_csv("embed", args),
        "created_after": _get_datetime("created_after", args),
        "updated_after": _get_datetime("updated_after", args),
    }

    return {k: _res[k] for k in _res if _res[k] is not None}
