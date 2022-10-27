import os
import sqlite3
import time
from os.path import exists
from pathlib import Path
from threading import Thread

from astropy.io import fits
from time import sleep
from console import main_console

create_table_sql = '''CREATE TABLE IF NOT EXISTS SEQUENCES (
  target_name text NOT NULL,
  filter text NOT NULL,
  exposure INTEGER NOT NULL,
  date text NOT NULL,
  filepath text NOT NULL PRIMARY KEY
);'''


class SequenceDatabaseManager:

    def __init__(self, database_filename: str = 'sequence.db', sequence_folder_path: str = None):
        """
        Init method.
        :param database_filename: The filename to find / create sqlite3 database.
        :param sequence_folder_path: The folder containing existing sequences data.
        """
        self.database_filename = database_filename
        self.sequence_folder_path = sequence_folder_path
        self.thread = None
        if not exists(database_filename):
            Path(os.path.dirname(database_filename)).mkdir(parents=True, exist_ok=True)
            self.connection = self.create_database()
            if sequence_folder_path:
                self.scan_sequence_folder()
        else:
            self.connection = sqlite3.connect(database_filename)

    def __del__(self):
        self.connection.close()

    def create_database(self) -> sqlite3.Connection:
        """
        Creates a SQLite3 database from scratch.
        :return: None
        """
        try:
            con = sqlite3.connect(self.database_filename)
            cur = con.cursor()
            cur.execute(create_table_sql)
            con.commit()
        except Exception:
            main_console.print_exception()
        return con

    def scan_sequence_folder(self) -> None:
        """
        Scan the sequence_folder_path for setting up initial data
        :return:
        """
        records = []
        for root, dirs, files in os.walk(self.sequence_folder_path):
            path = root.split(os.sep)
            print((len(path) - 1) * '---', os.path.basename(root))
            for file in files:
                if not file.upper().endswith('.FIT'):
                    continue
                full_path = os.path.join(root, file)
                try:
                    hdul = fits.open(full_path)
                    headers = hdul[0].header
                    object_name = headers['OBJECT']
                    filter_name = headers['FILTER']
                    exposure = headers['EXPOSURE']
                    datetime = headers['DATE-OBS']
                    print(len(path) * '---', file)
                    print(len(path) * '    ', object_name, filter_name, exposure, datetime)
                    records.append((object_name, filter_name, int(exposure), datetime, full_path))
                    id = id + 1
                except Exception as exception:
                    pass
        cur = self.connection.cursor()
        print(records)
        cur.executemany('REPLACE INTO SEQUENCES (target_name, filter, exposure, date, filepath) VALUES(?,?,?,?,?);',
                        records)
        self.connection.commit()

    def add_fit_file_impl(self, fit_filename: str, connection) -> None:
        try:
            sleep(5)
            hdul = fits.open(fit_filename)
            headers = hdul[0].header
            object_name = headers['OBJECT']
            filter_name = headers['FILTER']
            exposure = headers['EXPOSURE']
            datetime = headers['DATE-OBS']
            cur = connection.cursor()
            cur.executemany('REPLACE INTO SEQUENCES (target_name, filter, exposure, date, filepath) VALUES(?,?,?,?,?);',
                            [(object_name, filter_name, int(exposure), datetime, fit_filename)])
            connection.commit()
        except Exception as exp:
            print(exp)
            main_console.print_exception()

    def add_fit_file(self, fit_filename: str) -> None:
        self.thread = Thread(target=self.add_fit_file_impl, args=(fit_filename, self.connection))
        self.thread.start()

    def get_accumulated_exposure(self, object_name: str) -> dict:
        """
        Find accumlated exposure time per filter, using provided object name.
        :param object_name: The name of the target. Usually the name of the sequence.
        :return: A dictionary of filter name to accumulated exposure time in seconds.
        """
        get_accumulated_exposure_sql = f'select filter, sum(exposure) from sequences where target_name="{object_name}" ' \
                                       f'group by target_name, filter; '
        cur = self.connection.cursor()
        cur.execute(get_accumulated_exposure_sql)
        rows = cur.fetchall()
        return dict(rows)


if __name__ == '__main__':
    s = SequenceDatabaseManager(sequence_folder_path='Y:\\GoogleDrive\\Images\\Sequences')
    # s.scan_sequence_folder()
    s.get_accumulated_exposure(object_name='Abell_85')
