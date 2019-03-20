def disconnect_all_signals(*args):
    if len(args) > 1:
        for slot in args:
            disconnect_all_signals(slot)
    else:
        try:
            args[0].disconnect()
        except TypeError:
            pass
