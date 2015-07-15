__author__ = 'pjuluri'
import sqlite3
import config_cdash


def create_db(database_name, table_list):
    """
    :param database_name:
    :return:
    """
    try:
        conn = sqlite3.connect(database_name)
        cur = conn.cursor()
        config_cdash.LOG.info('Opened connection to the database file: {}'.format(database_name))
    except sqlite3.OperationalError:
        config_cdash.LOG.error('Unable to open the database file: {}'.format(database_name))

    for table in table_list:
        try:
            cur.execute(table)
            config_cdash.LOG.info('Creating Table:{} in {}'.format(table, database_name))
        except sqlite3.OperationalError as error:
            config_cdash.LOG.info('Error: {}'.format(error))
    return conn
