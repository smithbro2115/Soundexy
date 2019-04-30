import configparser
from CustomPyQtWidgets import LoginDialog


# TODO encrypt credentials before saving them to ini file


def delete_saved_credentials(site_name):
    config = configparser.ConfigParser()
    config.read('downloader_auth.ini')
    config.remove_section(site_name)
    with open('downloader_auth.ini', 'w+') as config_file:
        config.write(config_file)


def get_saved_credentials(site_name):
    config = configparser.ConfigParser()
    config.read('downloader_auth.ini')
    return config[site_name]['user'], config[site_name]['password']


def save_credentials(user, password, site):
    config = configparser.ConfigParser()
    config[site] = {}
    config[site]['User'] = user
    config[site]['Password'] = password
    with open('downloader_auth.ini', 'w+') as config_file:
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
