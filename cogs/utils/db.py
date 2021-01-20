import sqlite3

# Notes on SQLite and SQLite3
# ===========================
# 1. We don't need to worry about closing the conection if we have committed all changes - https://stackoverflow.com/questions/9561832/what-if-i-dont-close-the-database-connection-in-python-sqlite
# 2. The `with conn:` context manager automatically commits transactions upon __exit__, or rolls back transaction if error occurs.
#

# SQLite implementation - tuple
# ( 
# 0 guild_id:int, 
# 1 memechannel_id:int or 0, 
# 2 memeresultchannel_id:int or 0, 
# 3 meme_winner_role_id:int, 
# 4 last_scan:string (DateTime iso format)
# 5 serious_channels:string  "channel_id1 channelid2 chanelid3 " etc
# )

conn = sqlite3.connect("gucci.db")
c = conn.cursor()

def set_data(command, args_tuple):
    with conn:
        conn.execute(command, args_tuple)

def get_data(command, args_tuple):
    """Returns the sole tuple if it is the only value in the list, otherwise returns list of tuples."""
    c.execute(command, args_tuple)
    data = c.fetchall()

    if len(data) > 1:
        return data
    else:
        return data[0]
