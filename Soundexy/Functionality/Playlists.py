from Soundexy.Functionality.useful_utils import get_app_data_folder, pickle_obj, load_pickle_obj, check_if_file_exists,\
    get_all_file_paths_from_dir
from Soundexy.Indexing import LocalFileHandler
from os import rename, remove


def make_playlist_index(name):
    base_path = get_app_data_folder('playlists')
    path = f"{base_path}/{name}"
    if not check_if_file_exists(f"{path}.pkl"):
        pickle_obj(path, [])
    else:
        raise FileExistsError("That playlist name is already taken")


def rename_playlist_index(new, old):
    base_path = get_app_data_folder('playlists')
    old_path = f"{base_path}/{old}.pkl"
    new_path = f"{base_path}/{new}.pkl"
    try:
        rename(old_path, new_path)
    except FileExistsError:
        raise FileExistsError('This file name is already in use')


def save_playlist_index(name, playlist):
    base_path = get_app_data_folder('playlists')
    path = f"{base_path}/{name}"
    pickle_obj(path, playlist)


def load_playlist_index(name):
    base_path = get_app_data_folder('playlists')
    path = f"{base_path}/{name}"
    return load_pickle_obj(path)


def add_to_playlist_index(name, result):
    existing_playlist = load_playlist_index(name)
    if result not in existing_playlist:
        existing_playlist.append(result)
    save_playlist_index(name, existing_playlist)


def remove_from_playlist_index(name, result):
    existing_playlist = load_playlist_index(f"{name}.pkl")
    existing_playlist.remove(result)
    save_playlist_index(name, existing_playlist)


def delete_playlist_index(name):
    base_path = get_app_data_folder('playlists')
    path = f"{base_path}/{name}.pkl"
    remove(path)


def add_all_playlist_items(tree):
    playlist_files = get_all_file_paths_from_dir(get_app_data_folder('playlists'))
    for playlist_file in playlist_files:
        if playlist_file.endswith('.pkl'):
            playlist_name = playlist_file[:-4]
            results = LocalFileHandler.IndexFile(playlist_name, 'playlists').index
            playlist_item = tree.add_playlist_to_tree([playlist_name])
            tree.add_all_result_items(results, playlist_item)
        else:
            continue
