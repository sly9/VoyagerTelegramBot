import sqlite3
from os.path import exists
import os
from astropy.io import fits

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
        if not exists(database_filename):
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
        except Exception as e:
            print(e)
        return con

    def scan_sequence_folder(self) -> None:
        """
        Scan the sequence_folder_path for setting up initial data
        :return:
        """
        records = []
        id = 1
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

                    object = headers['OBJECT']
                    filter = headers['FILTER']
                    exposure = headers['EXPOSURE']
                    datetime = headers['DATE-OBS']
                    print(len(path) * '---', file)
                    print(len(path) * '    ', object, filter, exposure, datetime)
                    records.append((object, filter, int(exposure), datetime, full_path))
                    id = id + 1
                except Exception as exception:
                    pass
        cur = self.connection.cursor()
        print(records)
        cur.executemany('REPLACE INTO SEQUENCES (target_name, filter, exposure, date, filepath) VALUES(?,?,?,?,?);', records)
        self.connection.commit()


if __name__ == '__main__':
    s = SequenceDatabaseManager(sequence_folder_path='Y:\\GoogleDrive\\Images\\Sequences\\vdb141_Pane1')
    s.scan_sequence_folder()
