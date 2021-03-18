import sys
import traceback
import asyncio
import discord
from discord.ext import commands
import datetime as dt

from cogs.utils import db
from constants import ZERO_WIDTH_CHAR, GET_BASE_EMBED, EMBED_COLOUR

from calendar import month_name
from collections import defaultdict

def _2020ify_date(iso_date):
    return "2020" + iso_date[4:]

def _beautify_date(iso_date):
    return str(str(int(iso_date[8:]))) + " " + str(month_name[int(iso_date[5:7])])

async def _set_birthday(user_id, iso_birthday):
    await db.set_data("INSERT OR REPLACE INTO users VALUES (?, ?)", (user_id, iso_birthday,))

async def _get_birthday(user_id):
    birthday = (await db.get_one_data("SELECT bday_date FROM users WHERE id = ?", (user_id,)))[0]
    return birthday






        

async def _set_birthday_channel_id(guild_id, channel_id):
    await db.set_data("UPDATE guild_info SET bday_channel_id=? WHERE guild_id=?", (channel_id, guild_id,))

async def _get_birthday_channel_id(guild_id):
    birthday_channel_id = (await db.get_one_data("SELECT bday_channel_id FROM guild_info WHERE guild_id=?", (guild_id,)))[0]
    return birthday_channel_id

def _extract_birthday(user_given_date):
    # Here we try to split up the given data into a correct format to be parsed into dt.date()
    # Allowing separate delimiters in-case people r stoopid
    delimiters = [".", ",", "/", "-", "_", " "]
    chosen_delimiter = None
    for d in delimiters:
        if user_given_date.find(d) != -1:
            chosen_delimiter = d
            break

    #  "55.11" ---> ["55", "11"]
    data = list(filter(None, user_given_date.split(chosen_delimiter)))

    # check numbers were integers
    try:
        data = [int(i) for i in data]
    except ValueError as e:
        raise ValueError(f"Date: `{user_given_date}` contained non-integers.") from e

    # check that only day and month were given
    if len(data) != 2:
        raise ValueError(f"Date: `{user_given_date}` was too long or too short.")

    ## try to convert into datetime object
    try:
        given_birthday = dt.date(2020, data[1], data[0])
        iso_birthday = given_birthday.isoformat()   # --> "YYYY-MM-DD"     This is nice because we can use this as a dictionary key
    except ValueError as e:
        raise ValueError(f"Could not convert ({data[1]}, {data[0]}) into (month, day).") from e
    
    return iso_birthday


async def _is_birthday_shown(user_id, guild_id):
    shown = await db.get_one_data("SELECT EXISTS(SELECT 1 FROM user_bday_shown_guilds WHERE user_id=? AND guild_id=?)", (user_id, guild_id))
    shown = shown[0] ## first item in tuple returned, since a tuple of either (1,) or (0,) is returned from EXISTS()

    return shown

async def _birthday_toggle_visibility(user_id, guild_id):
    visible = await _is_birthday_shown(user_id, guild_id)

    if visible:
        await db.set_data("DELETE FROM user_bday_shown_guilds WHERE user_id=? AND guild_id=?", (user_id, guild_id))
        return False
    else:
        await db.set_data("INSERT INTO user_bday_shown_guilds VALUES (?, ?)", (user_id, guild_id))
        return True

async def _delete_birthday(user_id):
    try:
        await db.set_data("UPDATE users SET bday_date=null WHERE id=?", (user_id,))
    except Exception as e:
        raise Exception("There was an error removing birthday from users table.") from e
    
    # try:
    #     await db.set_data("DELETE FROM user_bday_shown_guilds WHERE user_id=?", (user_id,))
    # except Exception as e:
    #     raise Exception("There was an error while trying to remove all shown guilds") from e

async def _get_shown_guild_ids(user_id):
    guilds = []
    guilds = await db.get_all_data("SELECT guild_id FROM user_bday_shown_guilds WHERE user_id=?", (user_id,))
    return guilds

## These functions help us keep track of which is the most recent set birthday prompt given to a user

prompt_dicts = {"set_bday": {}, "set_bday_channel": {}}

async def _add_prompt(prompt_dict, key, prompt):
    if key in prompt_dicts[prompt_dict]:
        await _delete_prompt(prompt_dict, key)
    else:
        prompt_dicts[prompt_dict][key] = prompt

async def _delete_prompt(prompt_dict, key):
    try:
        await prompt_dicts[prompt_dict][key].delete()
        del prompt_dicts[prompt_dict][key]
    except Exception as e:
        pass

async def _get_last_birthday_scan():
    last_scan = (await db.get_one_data("SELECT last_bd_scan FROM bot_info", ()))[0]
    return last_scan

class Birthday(commands.Cog):
    """Add your birthday to be announced in servers!"""

    def __init__(self, bot):
        self.bot = bot
        self.name = "Birthday"
        self.bg_task = self.bot.loop.create_task(self.birthday_bg_task())


    async def _get_shown_guild_names(self, user_id): # should return empty list if no names found or no ids given
        guild_id_tuples = await _get_shown_guild_ids(user_id)
        guild_names = []

        for guild_id_tuple in guild_id_tuples:
            try:
                guild_id = guild_id_tuple[0]
                guild_name = self.bot.get_guild(guild_id).name

                if guild_name == None:
                    raise ValueError(f"Guild with id: {guild_id} was not found")

                guild_names.append(guild_name)
            except ValueError as e:
                print(e)
                continue

        return guild_names
            

    @commands.Cog.listener()
    async def on_ready(self):
        pass

    async def birthday_bg_task(self):
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            last_birthday_scan_2020_iso = await _get_last_birthday_scan()
            current_scan = dt.datetime.now(dt.timezone.utc)
            todays_date_2020_iso = _2020ify_date(dt.date.today().isoformat())

            if current_scan.hour > 12 and last_birthday_scan_2020_iso != todays_date_2020_iso:
                
                await db.set_data("UPDATE bot_info SET last_bd_scan=?", (todays_date_2020_iso,))

                
                birthday_list = await db.get_all_data(
                    """
                    SELECT guild_info.bday_channel_id, users.id FROM users, user_bday_shown_guilds, guild_info
                    WHERE users.id = user_bday_shown_guilds.user_id
                        AND guild_info.guild_id = user_bday_shown_guilds.guild_id
                        AND guild_info.bday_channel_id IS NOT NULL
                        AND users.bday_date = ?
                    """,
                    (todays_date_2020_iso,)
                )

                if len(birthday_list) == 0:
                    return

                birthdays_to_congratulate = defaultdict(list)
                for channel_id, user_id in birthday_list:
                    birthdays_to_congratulate[channel_id].append(user_id)


                embed = GET_BASE_EMBED()
                for channel_id, user_ids in birthdays_to_congratulate.items():
                    try:
                        channel = self.bot.get_channel(channel_id)
                        users_string = " ".join([self.bot.get_user(user_id).mention for user_id in user_ids])
                        embed.description = (
                            f"""🥳 **_HAPPY BIRTHDAY TO_** 🎂
                            {users_string}
                            ✨ 🎊 Hopefully your day is as amazing as you are! 🎉 🎆"""
                        )

                        await channel.send(embed=embed)
                    except Exception as e:
                        traceback.print_exception(type(e), e, e.__traceback__, file=sys.stderr)
                        continue

            await asyncio.sleep(60*60)

    @commands.group(name="birthday", aliases=["bd", "bday"])    # !birthday set
    async def birthday(self, ctx):
        """
        Base command. Shows the status of your birthday and whether it is visible in this guild.
        
        
        "!birthday" or "!bd"
        "!bd <subcommand>" eg "!bd guilds"
        """
        if ctx.invoked_subcommand:
            return
        elif ctx.subcommand_passed:
            await ctx.send_help("birthday")
            return

        try:
            embed = GET_BASE_EMBED()

            birthday = await _get_birthday(ctx.author.id)
            if not birthday:
                await ctx.invoke(self.bot.get_command("birthday set"))
            else:
                birthday_msg = ""
                visible_msg = ""
                if isinstance(ctx.channel, discord.DMChannel):
                    birthday_msg = "Your current birthday is 🎉 **" + _beautify_date(birthday)  + "** 🎁"
                elif isinstance(ctx.channel, discord.abc.GuildChannel):
                    visible_msg = "\n**Visible in this guild:** "
                    if await _is_birthday_shown(ctx.author.id, ctx.guild.id):
                        visible_msg += "☑️"
                    else:
                        visible_msg += "❌"

                msg = (
                    birthday_msg +
                    visible_msg
                )
                end_tip = "\n\n_Use command `!birthday guilds` to see in which guilds your birthday will be announced._"

                embed.description = msg
                embed.add_field(name=ZERO_WIDTH_CHAR, value=end_tip, inline=False)
                sent = await ctx.send(embed=embed)
                return sent

        except Exception as e:
            print(repr(e))

    @birthday.group(name="set", aliases=["add"])
    async def user_set(self, ctx, date="", override=None):
        """
        Sets your birthday to a specific date.
        
        "!birthday set 25.12"
        """
        description = ""
        end_tip = "_To show or hide your birthday in a guild, use the command `!bd toggle` in a channel in the guild._"
        end_warning = "\N{WARNING SIGN}** Warning: Setting your birthday is currently __permanent__. Please make sure it is correct!**"
        embed = GET_BASE_EMBED()
        author_id = ctx.author.id
        description = ""
        
        # case: user has a birthday (and is not overriding function)
        if (await _get_birthday(author_id)) and (override != "o" and ctx.author.id != 114458356491485185):
            # Do we want to do anything here?
            # maybe give link to DMs where user can ask for bday
            pre_description = "You already set a birthday!\n\n"
            message = await ctx.invoke(self.bot.get_command("birthday"))
            embed = message.embeds[0]
            embed.description = pre_description + embed.description
            await message.edit(embed=embed)
            return

        # case: user did not enter a date
        elif not date:
            embed.description = "Hi! 👋\n\nTo set your birthday use the command `!birthday set dd.mm`. 📋 For example:\n `!birthday set 25.12` for 25th of December. 🎄 \n\n**You should *not* enter the year.**"
            embed.add_field(name=ZERO_WIDTH_CHAR, value=end_tip, inline=False)
            await ctx.send(embed=embed)
            return

        # case: user entered a date
        else:
            try:
                # "YYYY-MM-DD" == isoformat
                iso_birthday = _extract_birthday(date)

            except Exception as e:
                description =   "👨🏽‍💻 Please input a valid date as follows: `dd.mm`. For example: `!birthday set 8.1` for 8th Januray. ☸️"\
                                "\n\n\n**You should *not* enter the year.**"
                embed.description = description
                embed.add_field(name=ZERO_WIDTH_CHAR, value=end_tip, inline=False)
                await ctx.send(embed=embed)
                print(e)
                return

            else:
                ## beef starts
                embed.description = f"You would like to set your birthday to **{_beautify_date(iso_birthday)}**. Please react with ☑️ if this is correct.\nUse the command again if you would like a different date."
                embed.add_field(name=ZERO_WIDTH_CHAR, value=end_warning, inline=False)
                prompt = await ctx.send(embed=embed, delete_after=30.0)

                def reaction_check(reaction, user):
                    if user.id == author_id and reaction.emoji == "☑️" and prompt.id == reaction.message.id:
                        return True
                    return False

                await _add_prompt("set_bday", author_id, prompt)
                await prompt.add_reaction("☑️")

                try:
                    await self.bot.wait_for("reaction_add", check=reaction_check, timeout=30.0)
                except asyncio.TimeoutError:
                    pass
                else:
                    ## make bday permanent
                    await _set_birthday(ctx.author.id, iso_birthday)
                    not_shown_msg = "\n\nYour birthday is not currently shown in any guilds. To show it here, type `!bd toggle`"

                    embed.description = f"🥳 Congratulations! Your birthday has been updated to **{_beautify_date(iso_birthday)}**. 🎊"
                    if not (await _get_shown_guild_ids(ctx.author.id)):
                        embed.description += not_shown_msg
                    embed.clear_fields()
                    embed.add_field(name=ZERO_WIDTH_CHAR, value="_This message will auto conceal your birthday in 1 minute..._", inline=False)

                    sent = await ctx.send(embed=embed)
                    await _delete_prompt("set_bday", author_id)

                    await asyncio.sleep(60.0)
                    embed.description = "🥳 Congratulations! Your birthday has been updated! 🎊"
                    if not (await _get_shown_guild_ids(ctx.author.id)):
                        embed.description += not_shown_msg

                    embed.clear_fields()
                    await sent.edit(embed=embed)

            finally:
                await _delete_prompt("set_bday", author_id)


    #@commands.is_owner()
    @birthday.group(name="delete", aliases=["del", "remove"])
    async def user_delete(self, ctx):
        """
        Deletes your own birthday from the database. Temp allowed all.
        
        "!birthday delete"
        """
        msg = ""
        embed = GET_BASE_EMBED()
        try:
            if (await _get_birthday(ctx.author.id)):
                await _delete_birthday(ctx.author.id)
                msg = "Your birthday was successfully **removed**. Feel free to add it again when you're ready! 🤞"
            else:
                msg = "I didn't know your birthday, 🤷🏼‍♀️ but we made sure to keep the place extra clean in case you'd like to add it one day!💪🏾"
            
            #add the tip if the user now has no birthday
            end_tip = "_To set your birthday use the command `!birthday set dd.mm`_"
            embed.add_field(name=ZERO_WIDTH_CHAR, value=end_tip, inline=False)

        except Exception as e:
            print(e)
            msg = "⛔️ There was an error processing your request. 🤕 Please try again later."
        finally:
            embed.description = msg
            await ctx.send(embed=embed)

    @birthday.group(name="toggle", aliases=["hide", "show"], usage="`!birthday toggle` to toggle birthday announces in this guild.")
    async def user_toggle_visibility(self, ctx):
        """
        Toggles whether birthday will be announced in this guild.
        
        "!birthday toggle"
        """
        embed = GET_BASE_EMBED()
        msg = ""

        if isinstance(ctx.channel, discord.abc.GuildChannel):
            if not (await _get_birthday(ctx.author.id)):
                await ctx.invoke(self.bot.get_command("birthday set"))
                return
            try:
                shown = await _birthday_toggle_visibility(ctx.author.id, ctx.guild.id)
            except Exception as e:
                print(e)

            msg = ""
            if shown:
                msg = "Your birthday is now **visible** in this guild. ☑️"
            else:
                msg = "Your birthday is now **hidden** in this guild. ❌"

        else:
            msg = "You can only use this command in a guild."

        embed.description = msg
        await ctx.send(embed=embed)


    @birthday.group(name="guilds", aliases=["g"])
    async def user_get_shown_guilds(self, ctx):
        """
        Shows the guilds in which your birthday will be announced.

        "!birthday guilds"
        """
        author_id = ctx.author.id
        ## declare priv message variables so that the second block can access them
        priv_msg_url = None

        priv_msg = None
        priv_embed = GET_BASE_EMBED()
        priv_title = ""
        priv_embed.description = ""
        priv_description = ""

        pub_msg = None
        pub_embed = GET_BASE_EMBED()
        pub_embed.description = ""
        pub_description = ""

        end_tip = "\n\n_To hide or show in a particular guild, type `!birthday toggle` in a text channel there._"

        # 
        guild_names = await self._get_shown_guild_names(author_id)

        user_birthday = await _get_birthday(author_id)
        if user_birthday:
            priv_title = f"Your birthday is: {_beautify_date(user_birthday)}"
        else:
            priv_title = "You have not set a birthday. Use `!bd set` to see how."

        if len(guild_names) > 0: ## check just in case one or more guild_id didnt convert to a name
            priv_description = "**Your birthday will be announced in the following guilds:**\n"
            priv_description += (
                "\n".join(["**"+str(i)+".** "+str(name) for i, name in enumerate(guild_names, start=1)])
            )
        else:
            priv_title = "Your birthday will not be announced in any guilds."

        priv_embed.title = priv_title
        priv_embed.description = priv_description
        priv_embed.add_field(name=ZERO_WIDTH_CHAR, value=end_tip, inline=False)
        priv_msg = await ctx.author.send(embed=priv_embed)
        priv_msg_url = priv_msg.jump_url


        if isinstance(ctx.channel, discord.abc.GuildChannel):
            pub_description = f"""🕵🏽 For privacy reasons, we sent you a DM with the information requested. 🛰
                                \n\n[**Jump to DM** ⤴️]({priv_msg_url})"""

            pub_embed.add_field(name=ZERO_WIDTH_CHAR, value=end_tip, inline=False)
            pub_embed.description = pub_description
            pub_msg = await ctx.send(embed=pub_embed)
            pub_msg_url = pub_msg.jump_url

            priv_embed.description += f"\n\n\n[**Jump back to channel** ↩️]({pub_msg_url})"

            await priv_msg.edit(embed=priv_embed)

    @birthday.group(name="channel", aliases=["c"])
    @commands.has_permissions(manage_channels=True)
    async def user_set_channel(self, ctx, given_channel=None):
        """
        You need the \"Manage Channels\" permissions to use this command.
        Either type part of a channel name e.g "!birthday channel chicken-cottage" for a channel called "🍗-chicken-cottage-place" or paste the channel ID. "!birthday channel 54325254325432"

        "!birthday channel general"
        "!birthday channel 473284813"
        """
        author_id = ctx.author.id
        msg = None
        embed = GET_BASE_EMBED()

        if given_channel is None:
            current_bday_channel_id = (await _get_birthday_channel_id(ctx.guild.id))
            if current_bday_channel_id:
                channel_name = self.bot.get_channel(current_bday_channel_id).name
                msg = f"Current birthday announcement channel is **{channel_name}**. ID: {current_bday_channel_id}"
            else:
                msg = "There is currently no set channel for birthday announcements.\nTo see how to set one, type `!help bd c`."
            
            embed.description = msg
            return await ctx.send(embed=embed)

        ## Below this line, we have been given a parameter that the user wants to set the bday channel as.
        channel_id = None
        try:
            channel_id = int(given_channel)
            if not isinstance(self.bot.get_channel(channel_id), discord.TextChannel):
                channel_id = None

        except ValueError:
            for channel in ctx.guild.channels:
                if isinstance(channel, discord.TextChannel) and given_channel.lower() in channel.name.lower():
                    channel_id = channel.id

        if channel_id is None:
            msg = "I could not find that channel in this guild."
        elif not self.bot.get_channel(channel_id) in ctx.guild.channels:
            msg = "I could not find that channel in this guild, please make sure I have valid roles to see the channel."
        elif not ctx.me.permissions_in(self.bot.get_channel(channel_id)).send_messages:
            msg = "I do not have the permission to send messages in that channel."

        if msg is not None:
            embed.description = msg
            sent = await ctx.send(embed=embed)
            return sent

        ## handle not found channels above, handle found channels and confirmation below

        channel = self.bot.get_channel(channel_id)
        msg = f"You would like to set **{channel.name}**, (ID: {channel.id}) to be the birthday announcement channel.\n\nReact with ☑️ if this is correct."
        embed.description = msg

        prompt = await ctx.send(embed=embed, delete_after=30.0)

        def reaction_check(reaction, user):
            if user.id == author_id and reaction.emoji == "☑️" and prompt.id == reaction.message.id:
                return True
            return False

        await _add_prompt("set_bday_channel", author_id, prompt)
        await prompt.add_reaction("☑️")

        try:
            await self.bot.wait_for("reaction_add", check=reaction_check, timeout=30.0)
        except asyncio.TimeoutError:
            pass
        else:
            ## make bday_channel permanent
            
            await _set_birthday_channel_id(ctx.guild.id, channel.id)
            embed.description = f"🥳 Birthday channel has been updated to **{channel.name}**. 🎊"
            await ctx.send(embed=embed, delete_after=120.0)

        await _delete_prompt("set_bday_channel", author_id)


def setup(bot):
    bot.add_cog(Birthday(bot))
