import datetime
import unittest

from playhouse.test_utils import test_database
from peewee import *
from unittest.mock import Mock

import work_log


TEST_DB = SqliteDatabase(':memory:')
TEST_DB.connect()
TEST_DB.create_tables([work_log.Entry], safe=True)

ENTRIES = [
    {
        'name': 'Max Planck',
        'project': 'Physics',
        'task_name': 'Quantum mechanics',
        'time_spent': 10000,
        'notes': 'Nobel Prize in Physics in 1918',
        'date': datetime.date(1919, 11, 13)
    },
    {
        'name': 'Niels Bohr',
        'project': 'Physics',
        'task_name': 'Quantum mechanics and atomic structure',
        'time_spent': 20000,
        'notes': 'Nobel Prize in Physics in 1922.',
        'date': datetime.date(1922, 12, 10)
    },
    {
        'name': 'Arieh Warshel',
        'project': 'Chemistry',
        'task_name': 'Theoretical chemistry',
        'time_spent': 50000,
        'notes': 'Nobel Prize in Chemistry in 2013.',
        'date': datetime.date(2013, 12, 8)
    },
    {
        'name': 'Max Kruse',
        'project': 'Football',
        'task_name': 'Forward',
        'time_spent': 6600,
        'notes': '',
        'date': datetime.date(2013, 12, 8)
    },
]


class AddTests(unittest.TestCase):
    def test_get_key_name(self):
        # with unittest.mock.patch('builtins.input', return_value="Tatiana"):
        #     self.assertEqual(work_log.get_key_name(key="User"), "Tatiana")
        with unittest.mock.patch('builtins.input',
                                 side_effect=["", "Tatiana"]):
            self.assertEqual(work_log.get_key_name(key="User"), "Tatiana")

    def test_convert_time_spent_to_min(self):
        self.assertEqual(
            work_log.convert_time_spent_to_min(('0.1', 'w')),
            1008
        )
        self.assertEqual(
            work_log.convert_time_spent_to_min(('0.5', 'd')),
            720
        )
        self.assertEqual(
            work_log.convert_time_spent_to_min(('2', 'h')),
            120
        )
        self.assertEqual(
            work_log.convert_time_spent_to_min(('0.5', 'm')),
            0.5
        )

    def test_validate_time(self):
        self.assertEqual(
            work_log.validate_time('0.5 d'),
            [('0.5', 'd')]
        )
        self.assertIsNone(work_log.validate_time('0.5 k'))

    def test_get_time_spent(self):
        with unittest.mock.patch('builtins.input',
                                 side_effect=["123", "0 d", "10 m"]):
            self.assertEqual(work_log.get_time_spent(), 10)

    def test_get_date(self):
        with unittest.mock.patch('builtins.input',
                                 side_effect=["31.31.2016", "21.06.2016"]):
            self.assertEqual(work_log.get_date(), datetime.date(2016, 6, 21))

    def test_get_entry_data(self):
        with unittest.mock.patch('builtins.input',
                                 side_effect=["Tatiana", "Project", "Task",
                                              "1 d", "22.06.2016"]):
            with unittest.mock.patch('sys.stdin.read', return_value=""):
                entry = work_log.get_entry_data()
                self.assertEqual(entry["name"], "Tatiana")

    def test_save_delete_edit_entry(self):
        with test_database(TEST_DB, (work_log.Entry,)):
            entry = work_log.Entry.create(**ENTRIES[0])
            with unittest.mock.patch('builtins.input', return_value="s"):
                work_log.save_delete_edit_entry(entry)
                self.assertEqual(work_log.Entry.select().count(), 1)
            with unittest.mock.patch('builtins.input',
                                     side_effect=["d", "y", " "]):
                work_log.save_delete_edit_entry(entry)
                self.assertEqual(work_log.Entry.select().count(), 0)

    def test_edit_entry(self):
        with test_database(TEST_DB, (work_log.Entry,)):
            entry = work_log.Entry.create(**ENTRIES[0])
            with unittest.mock.patch('builtins.input',
                                     side_effect=["u", "Tatiana"]):
                work_log.edit_entry(entry=entry)
                self.assertEqual(entry.name, "Tatiana")
            with unittest.mock.patch('builtins.input',
                                     side_effect=["t", "10 m"]):
                work_log.edit_entry(entry=entry)
                self.assertEqual(entry.time_spent, 10)
            with unittest.mock.patch('builtins.input',
                                     side_effect=["o"]):
                with unittest.mock.patch('sys.stdin.read',
                                         return_value="hard work"):
                    work_log.edit_entry(entry=entry)
                    self.assertEqual(entry.notes, "hard work")
            with unittest.mock.patch('builtins.input',
                                     side_effect=["d", "22.06.2016"]):
                work_log.edit_entry(entry=entry)
                self.assertEqual(entry.date, datetime.date(2016, 6, 22))
            with unittest.mock.patch('builtins.input',
                                     side_effect=["p", "Project"]):
                work_log.edit_entry(entry=entry)
                self.assertEqual(entry.project, "Project")
            with unittest.mock.patch('builtins.input',
                                     side_effect=["n", "Task"]):
                work_log.edit_entry(entry=entry)
                self.assertEqual(entry.task_name, "Task")


class SearchTests(unittest.TestCase):
    @staticmethod
    def create_entries():
        for entry in ENTRIES:
            work_log.Entry.create(
                name=entry['name'],
                project=entry['project'],
                task_name=entry['task_name'],
                time_spent=entry['time_spent'],
                notes=entry['notes'],
                date=entry['date']
            )

    def test_search_by_term(self):
        with test_database(TEST_DB, (work_log.Entry,)):
            self.create_entries()
            with unittest.mock.patch('builtins.input', side_effect=["nobel"]):
                self.assertEqual(work_log.search_by_term().count(), 3)

    def test_search_by_time_spent(self):
        with test_database(TEST_DB, (work_log.Entry,)):
            self.create_entries()
            with unittest.mock.patch('builtins.input',
                                     side_effect=["10000 m"]):
                self.assertEqual(work_log.search_by_time_spent().count(), 1)
            with unittest.mock.patch('builtins.input', side_effect=[
                    "1", "1 m - 1 m - 1 m", "1 m"]):
                self.assertEqual(work_log.search_by_time_spent().count(), 0)
            with unittest.mock.patch('builtins.input',
                                     side_effect=["1 m - 10000 m"]):
                self.assertEqual(work_log.search_by_time_spent().count(), 2)

    def test_search_by_project(self):
        with test_database(TEST_DB, (work_log.Entry,)):
            self.create_entries()
            with unittest.mock.patch('builtins.input',
                                     side_effect=["physics"]):
                self.assertEqual(work_log.search_by_project().count(), 2)

    def test_search_by_name(self):
        with test_database(TEST_DB, (work_log.Entry,)):
            self.create_entries()
            with unittest.mock.patch('builtins.input',
                                     side_effect=["Max Kruse"]):
                self.assertEqual(work_log.search_by_name().count(), 1)
            with unittest.mock.patch('builtins.input',
                                     side_effect=["Max"]):
                self.assertEqual(work_log.search_by_name().count(), 2)

    def test_list_of_dates(self):
        with test_database(TEST_DB, (work_log.Entry,)):
            self.create_entries()
            self.assertEqual(
                len(work_log.list_of_dates(
                        entries=work_log.Entry.select())), 3)

    def test_search_by_date(self):
        with test_database(TEST_DB, (work_log.Entry,)):
            self.create_entries()
            with unittest.mock.patch('builtins.input',
                                     side_effect=["08.12.2013"]):
                self.assertEqual(work_log.search_by_date().count(), 2)
            with unittest.mock.patch('builtins.input',
                                     side_effect=["01.01.1918 - 01.01.1923"]):
                self.assertEqual(work_log.search_by_date().count(), 2)

    def test_find_entries(self):
        with test_database(TEST_DB, (work_log.Entry,)):
            self.create_entries()
            with unittest.mock.patch('builtins.input',
                                     side_effect=["t", "prize"]):
                self.assertEqual(work_log.find_entries().count(), 3)
            with unittest.mock.patch('builtins.input',
                                     side_effect=["s", "10000 m"]):
                self.assertEqual(work_log.find_entries().count(), 1)
            with unittest.mock.patch('builtins.input',
                                     side_effect=["p", "Physics"]):
                self.assertEqual(work_log.find_entries().count(), 2)
            with unittest.mock.patch('builtins.input',
                                     side_effect=["d", "08.12.2013"]):
                self.assertEqual(work_log.find_entries().count(), 2)
            with unittest.mock.patch('builtins.input',
                                     side_effect=["e", "Max"]):
                self.assertEqual(work_log.find_entries().count(), 2)

if __name__ == '__main__':
    unittest.main()
