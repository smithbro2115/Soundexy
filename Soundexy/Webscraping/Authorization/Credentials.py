import configparser
from Soundexy.Functionality.useful_utils import get_app_data_folder
from Soundexy.GUI.API.CustomPyQtWidgets import LoginDialog
from cryptography.fernet import Fernet


downloader_config_path = f"{get_app_data_folder('obj')}/downloader_auth.ini"


def delete_saved_credentials(site_name):
    config = configparser.ConfigParser()
    config.read(downloader_config_path)
    config.remove_section(site_name)
    with open(downloader_config_path, 'w+') as config_file:
        config.write(config_file)


def get_saved_credentials(site_name):
    config = configparser.ConfigParser()
    config.read(downloader_config_path)
    return config[site_name]['user'], decrypt(config[site_name]['password'])


def save_credentials(user, password, site):
    config = configparser.ConfigParser()
    config[site] = {}
    config[site]['User'] = user
    config[site]['Password'] = encrypt(password)
    with open(downloader_config_path, 'w+') as config_file:
        config.write(config_file)


def get_credentials(website):
    try:
        credentials = get_saved_credentials(website), True
    except KeyError:
        dialog = LoginDialog(website)
        outcome = dialog.exec_()
        credentials = (dialog.ui.userLineEdit.text(), dialog.ui.passwordLineEdit.text()), bool(outcome)
        if dialog.ui.rememberCheckBox.checkState():
            save_credentials(dialog.ui.userLineEdit.text(), dialog.ui.passwordLineEdit.text(), website)
    return credentials


def encrypt(secure_data):
    byte_text = secure_data.encode()
    secret = b'RMi8CkGD8ER3uJvEWCF6hIivU3hrV2TtiTY3vnIJiLg='
    fernet = Fernet(secret)
    return fernet.encrypt(byte_text).decode()


def decrypt(encrypted_data):
    byte_text = encrypted_data.encode()
    secret = b'RMi8CkGD8ER3uJvEWCF6hIivU3hrV2TtiTY3vnIJiLg='
    fernet = Fernet(secret)
    return fernet.decrypt(byte_text).decode()
