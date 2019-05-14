import csv


def _get_csv(element, dict):
    e = dict.get(element, [])
    if e:
        return list(csv.reader([e]))[0]
    return e


def _get_int(element, dict):
    e = dict.get(element, None)
    if e:
        return int(e)
    return e


def parse_args(args):
    return {
        "limit": _get_int("limit", args),
        "offset": _get_int("offset", args),
        "sort": _get_csv("sort", args),
        "where": _get_csv("where", args),
        "embed": _get_csv("embed", args),
    }
