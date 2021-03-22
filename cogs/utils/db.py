import sqlite3

import aiosqlite

# Notes on SQLite and SQLite3
# ===========================
# 1. We don't need to worry about closing the conection if we have committed all changes - 
#   https://stackoverflow.com/questions/9561832/what-if-i-dont-close-the-database-connection-in-python-sqlite
# 2. The `with conn:` context manager automatically commits 
#   transactions upon __exit__, or rolls back transaction if error occurs.
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

async def db_connect():
    conn = await aiosqlite.connect("gucci.db")
    conn.row_factory = sqlite3.Row
    return conn

async def set_data(command, args_tuple):
    """simply executes an SQL query"""
    conn = await db_connect()
    await conn.execute(command, args_tuple)
    await conn.commit()
    await conn.close()

async def get_all_data(command, args_tuple):
    """Returns a list of tuples (rows)."""
    conn = await db_connect()
    c = await conn.cursor()
    await c.execute(command, args_tuple)
    rows = await c.fetchall()
    await conn.close()
    return rows

async def get_one_data(command, args_tuple):
    """Returns a tuple (row)."""
    conn = await db_connect()
    c = await conn.cursor()
    await c.execute(command, args_tuple)
    row = await c.fetchone()
    await conn.commit()
    await conn.close()
    return row
