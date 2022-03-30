import config


def d_print(*args, **kwargs):
    if config.DEBUG:
        print(*args, **kwargs)
