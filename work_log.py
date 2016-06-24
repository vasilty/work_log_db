import datetime
import os
import re
import sys

from collections import OrderedDict
from peewee import *

DATABASE = SqliteDatabase('work_log.db')


class Entry(Model):
    name = CharField(max_length=100)
    task_name = CharField(max_length=255)
    date = DateField()
    project = CharField(max_length=255)
    notes = TextField(default='')
    time_spent = FloatField()

    class Meta:
        database = DATABASE


def initialize():
    """Create the database and the table if they don't exist."""
    DATABASE.connect()
    DATABASE.create_tables([Entry], safe=True)


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


def get_key_name(key, message=None):
    """Gets the name and checks that its length > 0."""
    while True:
        clear()
        if message:
            print(message)
        name = input("{} name:\n".format(key)).strip()
        # Checks that user name is one or more characters long.
        if len(name) > 0:
            break
        else:
            message = '{} name should be at least one character long!'.format(
                key)
    return name


def convert_time_spent_to_min(time):
    """Converts time from w/d/h/m to minutes."""
    time_value = float(time[0])
    time_format = time[1]
    if time_format == 'w':
        time_min = time_value * 7 * 24 * 60
    elif time_format == 'd':
        time_min = time_value * 24 * 60
    elif time_format == 'h':
        time_min = time_value * 60
    else:
        time_min = time_value
    return time_min


def validate_time(time_input):
    """Checks that the input time matches the required format."""
    match = r'(?P<value>^[0-9]+.?[0-9]*)\s*(?P<format>[wdhm])$'
    time = re.findall(match, time_input)
    if time:
        return time
    else:
        return None


def get_time_spent(message=None):
    """Gets time spent."""
    while True:
        clear()
        if message:
            print(message)
        time_input = input('Time spent (in [w]eeks/[d]ays/[h]ours/'
                           '[m]inutes, eg. 1 h):\n')
        time = validate_time(time_input=time_input.lower())
        # If time is in the correct format
        if time is not None:
            # Converts time to minutes.
            time_min = convert_time_spent_to_min(time[0])
            # Check that time is positive.
            if time_min <= 0:
                message = "Time spent must be positive!"
            else:
                return time_min
        else:
            message = "Invalid time format!"


def get_notes():
    """Gets notes, which can be empty, contain multiple lines."""
    clear()
    print('General notes (press ctrl+d when finished): ')
    return sys.stdin.read().strip()


def get_date(message=None):
    """Get a date."""
    while True:
        clear()
        if message:
            print(message)
        date_input = input('Date (dd.mm.yyyy):\n')
        # Checks that the input date is a valid date.
        try:
            date = datetime.datetime.strptime(date_input, '%d.%m.%Y').date()
        except ValueError:
            message = 'Wrong date format!'
        else:
            return date


def print_entry(entry):
    """Prints an entry to a screen."""
    print('User name: {}'.format(entry.name))
    print('Project: {}'.format(entry.project))
    print('Task name: {}'.format(entry.task_name))
    print('Time spent (min): {}'.format(entry.time_spent))
    print('Notes: {}'.format(entry.notes))
    print('Date: {}'.format(entry.date.strftime('%d.%m.%Y')))
    print('_'*30)


def get_entry_data():
    """Get entry data from user."""
    name = get_key_name(key="User")
    project = get_key_name(key="Project")
    task_name = get_key_name(key="Task")
    time_spent = get_time_spent()
    notes = get_notes()
    date = datetime.datetime.now().date()
    return {'name': name, 'project': project, 'task_name': task_name,
            'time_spent': time_spent, 'notes': notes, 'date': date}


def create_entry():
    """Create an entry."""
    entry_data = get_entry_data()
    entry = Entry.create(**entry_data)
    return entry


def add_entry():
    """Add an entry."""
    entry = create_entry()
    save_delete_edit_entry(entry=entry)


def save_delete_edit_entry(entry):
    """Provides options to save, delete or edit entry."""
    while True:
        clear()
        print_entry(entry=entry)
        choice = input('[S]ave, [D]elete or [E]dit entry? ').lower().strip()
        if choice == 's':
            input('Entry saved! Press enter to go to the main menu.')
            break
        elif choice == 'e':
            edit_entry(entry=entry)
        elif choice == 'd':
            choice = input("Are you sure you want to delete this "
                           "entry? [N]/y ").lower().strip()
            if choice == 'y':
                entry.delete_instance()
                input('Entry deleted! Press enter to go to the main menu.')
                break


def edit_entry(entry):
    """Edit an entry."""
    while True:
        clear()
        choice = input(
            "Edit:\n"
            "[U] user name\n"
            "[P] project name\n"
            "[N] task name\n"
            "[T] time spent\n"
            "[O] notes\n"
            "[D] date\n\n"
            "[S] Show again the entry\n"
            "Action: ").lower().strip()
        if choice in list('upntods'):
            break
    if choice == 'u':
        entry.name = get_key_name(key="User")
    elif choice == 't':
        entry.time_spent = get_time_spent()
    elif choice == 'o':
        entry.notes = get_notes()
    elif choice == 'd':
        entry.date = get_date()
    elif choice == 'p':
        entry.project = get_key_name(key="Project")
    elif choice == 'n':
        entry.task_name = get_key_name(key="Task")
    query = Entry.update(
        name=entry.name,
        project=entry.project,
        task_name=entry.task_name,
        time_spent=entry.time_spent,
        notes=entry.notes,
        date=entry.date
    ).where(Entry.id == entry.id)
    query.execute()


def show_results(entries):
    """Shows search results with the ability to navigate through them."""
    if entries:
        index = 0
        while True:
            options = [
                '[N]ext',
                '[P]revious',
                '[E]dit',
                '[D]elete',
                '[M]ain menu'
            ]
            clear()
            entry = entries[index]
            print_entry(entry=entry)
            if index == 0:
                options.remove('[P]revious')
            if index == len(entries) - 1:
                options.remove('[N]ext')
            message = ', '.join(options) + ': '
            navigate = input(message).lower().strip()
            if navigate.upper() in message:
                if navigate == 'p':
                    index -= 1
                elif navigate == 'n':
                    index += 1
                elif navigate == 'e':
                    edit_entry(entry=entry)
                    save_delete_edit_entry(entry=entry)
                    break
                elif navigate == 'd':
                    choice = input("Are you sure you want to delete this "
                                   "entry? [N]/y ").lower().strip()
                    if choice == 'y':
                        entry.delete_instance()
                        input("Entry deleted! Press enter to return to the "
                              "main menu.")
                        break
                    else:
                        clear()
                        print_entry(entry=entry)
                elif navigate == 'm':
                    break
    else:
        clear()
        input('No entries found. Press enter to return to main menu.')


def search_by_term():
    """Searches by a term in the task name and notes."""
    clear()
    string = input('Exact string or regular expression: ')
    match = r'' + string
    entries = Entry.select().where(
        (Entry.notes.regexp(match)) | (Entry.task_name.regexp(match))
    )
    return entries


def search_by_time_spent(message=None):
    """Searches by time spent and time spent range."""
    clear()
    if message:
        print(message)
    time_input = input('Time spent (in [w]eeks/[d]ays/[h]ours/'
                       '[m]inutes, eg. 1 h) or time range (eg. 1 h - 2 h):'
                       ' ').lower().strip()
    match = r'(?P<value>[0-9]+.?[0-9]*)\s*(?P<format>[wdhm])'
    times = re.findall(match, time_input)
    # If time in the correct format was given.
    if times:
        # Converts time to minutes.
        times_min = map(convert_time_spent_to_min, times)
        sorted_times_min = sorted(times_min)
        # If a single time or time range was given.
        if len(times) < 3:
            entries = Entry.select().where(
                (Entry.time_spent >= sorted_times_min[0]) & (
                    Entry.time_spent <= sorted_times_min[-1]))
            return entries
        else:
            return search_by_time_spent(message='Invalid time format!')
    else:
        return search_by_time_spent(message='Invalid time format!')


def search_by_project():
    """Serches by the project name."""
    clear()
    string = input('Project name: ').strip()
    entries = Entry.select().where(Entry.project ** string)
    return entries


def search_by_name():
    """Searches by the employee name."""
    clear()
    string = input('Employee name: ').strip()
    entries = Entry.select().where(Entry.name ** (string+'%'))
    return entries


def list_of_dates(entries):
    """Returns a list of all dates with entries."""
    dates = []
    for entry in entries:
        if entry.date not in dates:
            dates.append(entry.date)
    sorted_dates = sorted(dates)
    return sorted_dates


def print_list_of_dates(dates):
    """Prints a list of dates to the screen."""
    print('Dates with entries:')
    for date in dates:
        print(date.strftime('%d.%m.%Y'))


def search_by_date(message=None):
    """Searches by date."""
    clear()
    dt_date_range = []
    if message:
        print(message)
    all_dates = list_of_dates(entries=Entry.select())
    print_list_of_dates(dates=all_dates)

    date_input = input('Date (dd.mm.yyyy) or date range '
                       '(dd.mm.yyyy - dd.mm.yyyy): ').strip()
    date_range = re.findall(r'[0-9]{2}.[0-9]{2}.[0-9]{4}', date_input)
    if date_range:
        # Check that input data is actually date(s).
        for date in date_range:
            try:
                dt_date = datetime.datetime.strptime(date, '%d.%m.%Y').date()
            except ValueError:
                return search_by_date(message='Wrong date format!')
            else:
                dt_date_range.append(dt_date)
        sorted_date_range = sorted(dt_date_range)
        # If a single date or a date range was given.
        if len(date_range) < 3:
            entries = Entry.select().where(
                (Entry.date >= sorted_date_range[0]) & (
                    Entry.date <= sorted_date_range[-1]))
        else:
            return search_by_date(message='Wrong date format!')
        return entries
    else:
        return search_by_date(message='Wrong date format!')


def find_entries():
    """Provides all possible search options."""
    while True:
        clear()
        choice = input(
            'Search by:\n'
            '[D] date\n'
            '[T] search term\n'
            '[S] time spent\n'
            '[P] project name\n'
            '[E] employee name\n\n'
            '[M] return to the main menu\n'
            'Action: ').lower().strip()
        if choice in list('dtspem'):
            break
    if choice != 'm':
        if choice == 't':
            entries = search_by_term()
        elif choice == 's':
            entries = search_by_time_spent()
        elif choice == 'p':
            entries = search_by_project()
        elif choice == 'd':
            entries = search_by_date()
        elif choice == 'e':
            entries = search_by_name()
        return entries


def lookup_entry():
    """Look up an entry."""
    entries = find_entries()
    show_results(entries=entries)


def menu_loop():
    """Show the menu."""
    while True:
        clear()
        for key, value in menu.items():
            print('[{}] {}'.format(key, value.__doc__))
        print('[Q] Quit the program.')
        choice = input("Action: ").upper().strip()
        if choice in menu:
            menu[choice]()
        if choice == 'Q':
            break

menu = OrderedDict([
    ('A', add_entry),
    ('L', lookup_entry),
])

if __name__ == '__main__':
    initialize()
    menu_loop()
