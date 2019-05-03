from Soundexy.Functionality.useful_utils import get_app_data_folder, pickle_obj, load_pickle_obj, check_if_file_exists


def make_playlist(name):
    base_path = get_app_data_folder('playlists')
    path = f"{base_path}/{name}"
    if not check_if_file_exists(path):
        pickle_obj(path, {})
    else:
        raise FileExistsError("That playlist name is already taken")


def save_playlist(name, playlist):
    base_path = get_app_data_folder('playlists')
    path = f"{base_path}/{name}"
    pickle_obj(path, playlist)


def load_playlist(name):
    base_path = get_app_data_folder('playlists')
    path = f"{base_path}/{name}"
    return load_pickle_obj(path)


def add_to_playlist(name, result_id, index_name, index_path):
    existing_playlist = load_playlist(name)
    existing_playlist[result_id] = [index_name, index_path]
    save_playlist(name, existing_playlist)


def remove_from_playlist(name, result_id):
    existing_playlist = load_playlist(name)
    existing_playlist.pop(result_id)
    save_playlist(name, existing_playlist)
