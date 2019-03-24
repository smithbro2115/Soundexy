def get_formatted_duration_from_milliseconds(milliseconds):
    duration = milliseconds / 1000
    minutes = duration // 60
    seconds = duration % 60
    return '%02d:%02d' % (minutes, seconds)


def get_yes_no_from_bool(value: bool) -> str:
    if value:
        return 'Yes'
    return 'No'
