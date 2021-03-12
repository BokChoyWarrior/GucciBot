import time
import discord
import asyncio
from discord.ext import commands
import datetime as dt
from cogs.utils import db
from calendar import month_name

birthdays = {}

def beautify_date(iso_date):
    return str(iso_date[8:]) + " " + str(month_name[int(iso_date[5:7])])

def get_birthday(user_id):
    birthday = db.get_data("SELECT bday_date FROM users WHERE id = ?", (user_id,))
    print(birthday)
    if not birthday or len(birthday[0]) == 0:
        return False
    else:
        return birthday[0]

def extract_birthday(user_given_date):
    # Here we try to split up the given data into a correct format to be parsed into dt.date()
    # Allowing separate delimiters in-case people r stoopid
    delimiters = [".", ",", "/", "-", "_"]
    chosen_delimiter = "."
    for d in delimiters:
        if user_given_date.find(d) != -1:
            chosen_delimiter = d
            break

    data = list(filter(None, user_given_date.split(chosen_delimiter)))                   #  55.11.1999 ---> ["55", "11", "1999"]

    if len(data) != 2 or not isinstance(data, list):
        raise ValueError("Non-valid date given")

    try:
        data = [int(i) for i in data]
    except ValueError as e:
        raise ValueError("Date contained invalid numbers") from e

    ## convert into datetime object
    try:
        given_birthday = dt.date(2020, data[1], data[0])
        iso_birthday = given_birthday.isoformat()   # --> "YYYY-MM-DD"     This is nice because we can use this as a dictionary key
    except ValueError as e:
        raise ValueError("Date not within allowed parameters.") from e
    
    return iso_birthday

def set_birthday(user_id, iso_birthday):
    db.set_data("INSERT OR REPLACE INTO users VALUES (?, ?)", (user_id, iso_birthday))

def is_birthday_shown(user_id, guild_id):
    shown = db.get_data("SELECT EXISTS(SELECT 1 FROM user_bday_shown_guilds WHERE user_id=? AND guild_id=?)", (user_id, guild_id))
    shown = shown[0] ## first item in tuple returned, since a tuple of either (1,) or (0,) is returned from EXISTS()

    if shown:
        return True
    else:
        return False

def birthday_toggle_visibility(user_id, guild_id):
    visible = is_birthday_shown(user_id, guild_id)

    if visible:
        db.set_data("DELETE FROM user_bday_shown_guilds WHERE user_id=? AND guild_id=?", (user_id, guild_id))
        return False
    else:
        db.set_data("INSERT INTO user_bday_shown_guilds VALUES (?, ?)", (user_id, guild_id))
        return True


class Birthday(commands.Cog):


    def __init__(self, bot):
        self.bot = bot
        self.name = "Birthday"
        self.bg_task = self.bot.loop.create_task(self.birthday_bg_task())

    @commands.Cog.listener()
    async def on_ready(self):
        pass

    async def birthday_bg_task(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            self.current_scan = dt.datetime.utcnow().day
            # for guild_id_tuple in self.guild_ids:
            #     guild_id = guild_id_tuple[0]
            #     last_scan = dt.datetime.fromisoformat(db.get_data("SELECT last_scan FROM guild_info WHERE guild_id=?", guild_id_tuple)[0])
            #     if dt.timedelta(2) < self.current_scan - last_scan < dt.timedelta(7):
            #         await self.remove_meme_roles(guild_id)
            #     if self.current_scan - last_scan > dt.timedelta(7):
            #         print("Scanning... ", self.current_scan - last_scan)
            #         await self.get_meme_contest_results(guild_id_tuple)
            #         last_scan += dt.timedelta(7)
            #         db.set_data("UPDATE guild_info SET last_scan=? WHERE guild_id=?", (dt.datetime.isoformat(last_scan), ) + guild_id_tuple)


            await asyncio.sleep(60)

    @commands.group(name="birthday", aliases=["bd", "bday"])    # !birthday set
    async def birthday(self, ctx):
        if ctx.invoked_subcommand:
            pass
        else:
            try:
                visible_msg = "not "
                if is_birthday_shown(ctx.author.id, ctx.guild.id):
                    visible_msg = ""

                msg = ""
                birthday = get_birthday(ctx.author.id)
                if not birthday:
                    msg = "You have not stored your birthday yet - type `!birthday help` to see how to add it!"
                else:
                    msg = "Your current birthday is **" + beautify_date(birthday)  + "** and is " + visible_msg + "visible in this guild."
                
                await ctx.send(msg)

            except Exception as e:
                print(repr(e))


    @birthday.group(name="set")
    async def user_set(self, ctx, date):
        errormsg = ""
        try:
            # "YYYY-MM-DD" == isoformat
            iso_birthday = extract_birthday(date)
            set_birthday(ctx.author.id, iso_birthday)

            await ctx.send("Your birthday has been updated to " + beautify_date(iso_birthday) + ".")

        except Exception as e:
            await ctx.send("\nPlease input a valid date as follows: `dd.mm`. For example: `25.12` for 25th of December. You do *not* need to enter the specific year.")
            print(e)


    @birthday.group(name="delete", aliases=["del", "remove"])
    async def user_delete(self, ctx):
        msg = ""
        try:
            if get_birthday(ctx.author.id):
                msg = "Your birthday was successfully **removed**. Feel free to add it when you're ready!"
            else:
                msg = "I didn't know your birthday anyway, but we made sure to keep the place extra clean in case you'd like to add it one day!"

            db.set_data("INSERT OR REPLACE INTO users VALUES (:id, :bday_date)", {"id": ctx.author.id, "bday_date": ""})
        except Exception:
            msg = "There was an error processing your request. Please try again later."
        finally:
            await ctx.send(msg)


    @commands.guild_only()
    @birthday.group(name="show", aliases=["hide"])
    async def user_toggle_visibility(self, ctx):

        try:
            shown = birthday_toggle_visibility(ctx.author.id, ctx.guild.id)
            print("Shown: " + str(shown))
        except Exception as e:
            print(e)

        msg = ""
        if shown:
            msg = "Your birthday is now **visible** in this guild."
        else:
            msg = "Your birthday is now **hidden** in this guild."

        await ctx.send(msg)


def setup(bot):
    bot.add_cog(Birthday(bot))
