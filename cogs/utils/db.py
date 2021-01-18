import sqlite3

# Notes on SQLite and SQLite3
# ===========================
# 1. We don't need to worry about closing the conection if we have committed all changes - https://stackoverflow.com/questions/9561832/what-if-i-dont-close-the-database-connection-in-python-sqlite
# 2. The `with conn:` context manager automatically commits transactions upon __exit__, or rolls back transaction if error occurs.
#
conn = sqlite3.connect("gucci.db")
c = conn.cursor()

def set_data(command, args_tuple):
    with conn:
        conn.execute(command, args_tuple)

def get_data(command, args_tuple):
    c.execute(command, args_tuple)
    data = c.fetchall()

    if len(data) > 1:
        return data
    else:
        return data[0]
