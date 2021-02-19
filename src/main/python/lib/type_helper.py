def is_int(str_: str) -> bool:
    """Return if string is an integer"""
    try:
        int(str_)
        return True
    except (ValueError, TypeError):
        return False


def is_bool(str_: str) -> bool:
    """Return if string is a boolean"""
    try:
        str2bool(str_)
        return True
    except (ValueError, TypeError):
        return False


def str2bool(str_: str) -> bool:
    """Converts string to boolean"""
    if not isinstance(str_, str):
        raise TypeError("Type {} is not a string".format(type(str_)))

    if str_.lower().startswith("t"):
        return True
    elif str_.lower().startswith("f"):
        return False
    else:
        raise ValueError("Cannot convert {} to boolean".format(str_))
