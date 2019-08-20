import json
import os.path
import os
import wimbledon

CONFIG_DIR = os.path.expanduser('~/.wimbledon')

HARVEST_CREDENTIALS_PATH = CONFIG_DIR + '/.harvest_credentials'
SQL_CONFIG_PATH = CONFIG_DIR + '/.sql_config'
WIMBLEDON_CONFIG_PATH = CONFIG_DIR + '/.wimbledon_config'
GITHUB_CREDENTIALS_PATH = CONFIG_DIR + '/.github_credentials'

def check_dir(directory):
    """
    Check whether directory exists; if not create it.

    :param directory:
    :return:
    """
    if not os.path.isdir(directory):
        os.makedirs(directory)

    return os.path.isdir(directory)


def get_wimbledon_path():
    """
    Get the directory of the wimbledon code base.

    :return:
    """
    return os.path.dirname(wimbledon.__file__)


def set_harvest_credentials(harvest_account_id,
                            forecast_account_id,
                            access_token):
    """
    Saves Harvest credentials to ~/.wimbledon/.harvest_credentials as a json file containing a harvest account id,
    a forecast account id and an access token.

    Get these from https://id.getharvest.com/developers.

    :param harvest_account_id:
    :param forecast_account_id:
    :param access_token:
    :return:
    """

    credentials = {
        "harvest_account_id": harvest_account_id,
        "forecast_account_id": forecast_account_id,
        "access_token": access_token
    }

    check_dir(CONFIG_DIR)

    with open(HARVEST_CREDENTIALS_PATH, 'w') as f:
        json.dump(credentials, f)


def get_harvest_credentials():
    """
    Load Harvest credentials from ~/.wimbledon/.harvest_credentials, which should be a json file containing the keys
    harvest_account_id, forecast_account_id and access_token, or from HARVEST_ACCOUNT_ID, FORECAST_ACCOUNT_ID and
    HARVEST_ACCESS_TOKEN environment variables.

    :return:
    """
    try:
        # check environment variables
        harvest_credentials = dict()
        harvest_credentials['harvest_account_id'] = os.environ['HARVEST_ACCOUNT_ID']
        harvest_credentials['forecast_account_id'] = os.environ['FORECAST_ACCOUNT_ID']
        harvest_credentials['access_token'] = os.environ['HARVEST_ACCESS_TOKEN']

    except KeyError:
        # check ~/.wimbledon/.harvest_credentials
        try:
            with open(HARVEST_CREDENTIALS_PATH, 'r') as f:
                harvest_credentials = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError('No Harvest credentials found. Please create the file '+ HARVEST_CREDENTIALS_PATH)

        keys = harvest_credentials.keys()

        assert "harvest_account_id" in keys, \
            "harvest_account_id not present in " + HARVEST_CREDENTIALS_PATH

        assert "forecast_account_id" in keys, \
            "forecast_account_id not present in " + HARVEST_CREDENTIALS_PATH

        assert "access_token" in keys, \
            "access_token not present in " + HARVEST_CREDENTIALS_PATH

    assert len(harvest_credentials["harvest_account_id"]) > 0, "harvest_account_id invalid"
    assert len(harvest_credentials["forecast_account_id"]) > 0, "forecast_account_id invalid"
    assert len(harvest_credentials["access_token"]) > 0, "access_token invalid"

    return harvest_credentials


def set_sql_config(drivername, host, database, username='', password=''):
    """
    Saves configuration of a SQL database to ~/.wimbledon/.sql_config

    :param drivername:
    :param host:
    :param database:
    :param password:
    :param username:
    :return:
    """
    sql_config = {
        "drivername": drivername,
        "host": host,
        "database": database,
        "username": username,
        "password": password
    }

    check_dir(CONFIG_DIR)

    with open(SQL_CONFIG_PATH, 'w') as f:
        json.dump(sql_config, f)


def get_sql_config():
    """
    Loads SQL database configuration from ~/.wimbledon/.sql_config which should be a json file with the keys
    drivername, host and database.

    :return:
    """

    try:
        with open(SQL_CONFIG_PATH, 'r') as f:
            sql_config = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError('No SQL configuration file found. Please create the file ' + SQL_CONFIG_PATH)

    keys = sql_config.keys()

    assert "drivername" in keys and len(sql_config["drivername"]) > 0, \
        "drivername not set in " + SQL_CONFIG_PATH

    assert "host" in keys and len(sql_config["host"]) > 0, \
        "host not set in " + SQL_CONFIG_PATH

    assert "database" in keys and len(sql_config["database"]) > 0, \
        "database not set in " + SQL_CONFIG_PATH

    if sql_config["host"] != 'localhost':
        assert "username" in keys and len(sql_config["username"]) > 0, \
            "username not set in " + SQL_CONFIG_PATH

        assert "password" in keys and len(sql_config["password"]) > 0, \
            "password not set in " + SQL_CONFIG_PATH

    return sql_config


def get_github_credentials():

    try:
        # check environment variables
        github_credentials = dict()
        github_credentials['token'] = os.environ['GITHUB_TOKEN']

    except KeyError:
        # check ~/.wimbledon/.github_credentials
        try:
            with open(GITHUB_CREDENTIALS_PATH, 'r') as f:
                github_credentials = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError('No GitHub credentials found. Please create the file '+ GITHUB_CREDENTIALS_PATH)

        keys = github_credentials.keys()

        assert "token" in keys, \
            "token not present in " + GITHUB_CREDENTIALS_PATH

    return github_credentials
