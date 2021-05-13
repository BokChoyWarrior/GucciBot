import asyncio
import datetime as dt
from collections import defaultdict#

import discord
from discord.ext import commands, tasks

from cogs.utils import db
from constants import ZERO_WIDTH_CHAR, GET_BASE_EMBED

def _2020ify_date(iso_date):
    return "2020" + iso_date[4:]

def _beautify_date(iso_date):
    date = dt.date.fromisoformat(iso_date)
    return date.strftime("%d %B").strip("0")

async def _set_birthday(user_id, iso_birthday):
    await db.set_data(
        "INSERT OR REPLACE INTO users VALUES (?, ?)",
        (user_id, iso_birthday,))

async def _get_birthday(user_id):
    birthday = (await db.get_one_data(
        "SELECT bday_date FROM users WHERE id = ?",
        (user_id,)))

    if birthday is None or birthday["bday_date"] is None:
        return None
    return birthday["bday_date"]

async def _set_birthday_channel_id(guild_id, channel_id):
    await db.set_data(
        "UPDATE guild_info SET bday_channel_id=? WHERE guild_id=?",
        (channel_id, guild_id,))

async def _get_birthday_channel_id(guild_id):
    birthday_channel_id = (await db.get_one_data(
        "SELECT bday_channel_id FROM guild_info WHERE guild_id=?",
        (guild_id,)))["bday_channel_id"]
    return birthday_channel_id

def _extract_birthday_to_iso(user_given_date):
    # Here we try to split up the given data into a correct format to be
    #  parsed into a dt.date() object
    # We allow separate delimiters just in-case

    # First try to find which delimiter was used
    chosen_delimiter = "."
    delimiters = [",", "/", "-", "_"]
    for delimiter in delimiters:
        if user_given_date.find(delimiter) != -1:
            chosen_delimiter = delimiter
            break

    #  "55.11" ---> ["55", "11"]
    data = user_given_date.split(chosen_delimiter)

    try:
        day, month = data[0], data[1]
    except IndexError:
        raise IndexError(f"{data} could not be split into (day, month)") from None
    # ["55", "11"] ---> [55, 11]
    try:
        day, month = int(day), int(month)
    except ValueError:
        raise ValueError(f"Error converting birthday to integers. {day, month}") from None

    # try to convert into datetime object (let)
    try:
        # (mm, dd) --> dt.Date object
        given_birthday = dt.date(2020, month, day)
        # dt.Date object --> "YYYY-MM-DD"
        iso_birthday = given_birthday.isoformat()
    except ValueError:
        raise ValueError(
            f"Error converting ({day}, {month}) into (day, month)") from None

    return iso_birthday


async def _is_birthday_shown_here(user_id, guild_id):
    shown = await db.get_one_data(
        """SELECT EXISTS(
            SELECT 1 FROM user_bday_shown_guilds
            WHERE user_id=?
            AND guild_id=?)
        """,
        (user_id, guild_id))

    # Return first item since either (1,) or (0,) is returned from EXISTS()
    return shown[0]

async def _birthday_toggle_visibility(user_id, guild_id):
    visible = await _is_birthday_shown_here(user_id, guild_id)

    if visible:
        await db.set_data(
            """DELETE FROM user_bday_shown_guilds
            WHERE user_id=? AND guild_id=?""",
            (user_id, guild_id)
        )
        return False
    # implicit else:
    await db.set_data(
        "INSERT INTO user_bday_shown_guilds VALUES (?, ?)",
        (user_id, guild_id))
    return True

async def _delete_birthday(user_id):
    await db.set_data("UPDATE users SET bday_date=null WHERE id=?", (user_id,))

async def _get_shown_guild_ids(user_id):
    guilds = await db.get_all_data(
        """
        SELECT guild_id FROM user_bday_shown_guilds
        WHERE user_id=?
        """,
        (user_id,)
    )
    guild_ids = [guild_id for guild in guilds if (guild_id:=guild["guild_id"]) is not None]
    return guild_ids

# These functions help keep track of which is the most recent set birthday prompt given to a user
#########################################################
prompt_dicts = {"set_bday": {}, "set_bday_channel": {}}

async def _add_prompt(prompt_dict, user_id, prompt):
    if user_id in prompt_dicts[prompt_dict]:
        await _delete_prompt(prompt_dict, user_id)

    prompt_dicts[prompt_dict][user_id] = prompt

async def _delete_prompt(prompt_dict, user_id):
    try:
        await prompt_dicts[prompt_dict][user_id].delete()
    except (discord.Forbidden, discord.NotFound, discord.HTTPException):
        pass
    try:
        del prompt_dicts[prompt_dict][user_id]
    except KeyError:
        pass

async def _delete_prompt_if_exists(prompt_dict, user_id, prompt):
    if user_id in prompt_dicts[prompt_dict] and prompt_dicts[prompt_dict][user_id] == prompt:
        await _delete_prompt(prompt_dict, user_id)
#########################################################

async def _get_last_birthday_scan():
    data = await db.get_one_data("SELECT last_bd_scan FROM bot_info", ())
    return data["last_bd_scan"]


class Birthday(commands.Cog):
    """Add your birthday to be announced in servers!"""

    def __init__(self, bot):
        self.bot = bot
        self.name = "Birthday"
        # pylint: disable=maybe-no-member
        self.birthday_bg_task.start()


    async def _get_guild_names(self, guild_ids):

        guild_names = [
            guild.name
            for guild_id in guild_ids
            if (guild := self.bot.get_guild(guild_id)) is not None
        ]

        return guild_names

    async def _get_enumerated_guild_names(self, guild_names, sep="\n"):
        enumerated_names = sep.join(
            [f"**{i}.** {name}" for i, name in enumerate(guild_names, start=1)]
        )

        return enumerated_names


    @tasks.loop(hours=2)
    async def birthday_bg_task(self):
        last_birthday_scan_2020_iso = await _get_last_birthday_scan()
        current_scan = dt.datetime.now(dt.timezone.utc)
        todays_date_2020_iso = _2020ify_date(dt.date.today().isoformat())

        if (not current_scan.hour > 9 and
            last_birthday_scan_2020_iso == todays_date_2020_iso):
            return

        await db.set_data(
            "UPDATE bot_info SET last_bd_scan=?",
            (todays_date_2020_iso,))

        await self.message_imminent_birthdays()

        birthday_list = await db.get_all_data(
            """
            SELECT guild_info.bday_channel_id, users.id
            FROM users, user_bday_shown_guilds, guild_info

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
            channel = self.bot.get_channel(channel_id)
            if not channel:
                return

            users_string = " ".join(
                [self.bot.get_user(user_id).mention for user_id in user_ids])

            embed.description = (
                "🥳 **_HAPPY BIRTHDAY TO_** 🎂\n"
                f"{users_string}\n"
                "✨ 🎊 Hopefully your day is as amazing as you are! 🎉 🎆"
            )

            await channel.send(embed=embed)


    @birthday_bg_task.before_loop
    async def before_birthday_bg_task(self):
        await self.bot.wait_until_ready()


    async def _get_common_guild_ids(self, user_id):
        user = self.bot.get_user(user_id)

        guilds = []
        for guild in self.bot.guilds:
            if user in guild.members:
                guilds.append(guild.id)

        return guilds

    async def message_imminent_birthdays(self):
        week_from_today = dt.date.today() + dt.timedelta(days=7)
        week_from_today_2020_iso = _2020ify_date(week_from_today.isoformat())

        users_with_birthday_soon = await db.get_all_data(
            """
            SELECT users.id FROM users
            WHERE users.bday_date = ?
            """,
            (week_from_today_2020_iso,)
        )

        if not users_with_birthday_soon:
            return

        for user_id_row in users_with_birthday_soon:
            user_id = user_id_row["id"]
            embed = GET_BASE_EMBED()
            main_title = (
                "Hey there! It seems like you've set a birthday, "
                "but you have not set it to announce in any servers."
            )
            main_desc = "To announce it in a server, type `!bd toggle` in a channel there."

            shown_guild_ids = await _get_shown_guild_ids(user_id)
            shown_guild_names = await self._get_guild_names(shown_guild_ids)
            enumerated_guild_names = await self._get_enumerated_guild_names(shown_guild_names)

            if enumerated_guild_names:
                main_title = "Your birthday will be announced in the following servers:"
                main_desc = enumerated_guild_names


            common_guild_ids = set((await self._get_common_guild_ids(user_id)))
            common_guild_ids_not_shown = list(common_guild_ids.difference(set(shown_guild_ids)))
            common_not_shown_guild_names = await self._get_guild_names(common_guild_ids_not_shown)

            extra_desc = ""
            if common_not_shown_guild_names:
                names = " ---- ".join(common_not_shown_guild_names)
                extra_desc = (
                    "\n\n\n\n"
                    "**Servers in which you could choose to announce your birthday:**\n"
                    f"_{names}_"
                )

            user = self.bot.get_user(user_id)

            embed.title = main_title
            embed.description = main_desc + extra_desc
            await user.send(embed=embed)


    @commands.group(name="birthday", aliases=["bd", "bday"])
    async def birthday(self, ctx):
        """
        Base command. Shows the status of your birthday and whether it is announced in this server.


        "!birthday" or "!bd"
        "!bd <subcommand>" eg "!bd servers"
        """
        if ctx.invoked_subcommand:
            return
        elif ctx.subcommand_passed:
            await ctx.send_help("birthday")
            return

        embed = GET_BASE_EMBED()

        birthday = await _get_birthday(ctx.author.id)
        if not birthday:
            await ctx.invoke(self.bot.get_command("birthday set"))
        else:
            birthday_msg = ""
            visible_msg = ""
            if isinstance(ctx.channel, discord.DMChannel):
                birthday_msg = (
                    "Your current birthday is 🎉 **"
                    f"{_beautify_date(birthday)}** 🎁"
                )
            elif isinstance(ctx.channel, discord.abc.GuildChannel):
                visible_msg = "\n**Announced in this server:** "
                if await _is_birthday_shown_here(ctx.author.id, ctx.guild.id):
                    visible_msg += "☑️"
                else:
                    visible_msg += "❌"

            msg = (
                birthday_msg +
                visible_msg
            )
            end_tip = (
                "\n\n_Use command `!birthday servers` "
                "to see in which servers your birthday will be announced._"
            )

            embed.description = msg
            embed.add_field(
                name=ZERO_WIDTH_CHAR,
                value=end_tip,
                inline=False
            )
            sent = await ctx.send(embed=embed)
            return sent

    @birthday.group(name="set", aliases=["add"])
    async def user_set(self, ctx, date="", override=None):
        """
        Sets your birthday to a specific date.

        "!birthday set 25.12"
        """
        description = ""
        end_tip = (
            "_To show or hide your birthday in a server, "
            "use the command `!bd toggle` in a channel in the server._"
        )
        end_warning = (
            "\N{WARNING SIGN}** Warning: Setting your birthday "
            "is currently __permanent__. Please make sure it is correct!**"
        )
        embed = GET_BASE_EMBED()
        author_id = ctx.author.id
        description = ""

        # case: user has a birthday (and is not overriding function)
        if ((await _get_birthday(author_id)) and
            not (override == "o" and ctx.author.id == 114458356491485185)):
            pre_description = "You already set a birthday!\n\n"
            message = await ctx.invoke(self.bot.get_command("birthday"))
            embed = message.embeds[0]
            embed.description = pre_description + embed.description
            await message.edit(embed=embed)
            return

        # case: user did not enter a date
        if not date:
            embed.description = (
                "Hi! 👋\n\nTo set your birthday use the command "
                "`!birthday set dd.mm`. 📋 For example:\n `!birthday set 25.12` "
                "for 25th of December. 🎄 \n\n**You should *not* enter the year.**"
            )
            embed.add_field(name=ZERO_WIDTH_CHAR, value=end_tip, inline=False)
            await ctx.send(embed=embed)
            return

        # case: user entered a date
        try:
            # "YYYY-MM-DD" == isoformat
            iso_birthday = _extract_birthday_to_iso(date)

        except (IndexError, ValueError):
            description = (
                f"I'm sorry, but **{date}** is not valid.⛔\n\n"
                "👨🏽‍💻 Please input a valid date as follows: `dd.mm`. "
                "For example: `!birthday set 8.1` for 8th Januray. ☸️"
                "\n\nYou should **not** enter the year."
            )
            embed.description = description
            embed.add_field(name=ZERO_WIDTH_CHAR, value=end_tip, inline=False)
            await ctx.send(embed=embed)
            return


        # implicit "else:"
        embed.description = (
            "You would like to set your birthday to "
            f"**{_beautify_date(iso_birthday)}"
            "**. Please react with ☑️ if this is correct."
            "\nUse the command again if you would like a different date."
        )
        embed.add_field(name=ZERO_WIDTH_CHAR, value=end_warning, inline=False)
        prompt = await ctx.send(embed=embed, delete_after=30.0)

        def reaction_check(reaction, user):
            if (user.id == author_id and
                reaction.emoji == "☑️" and
                prompt.id == reaction.message.id):
                return True
            else:
                return False

        await _add_prompt("set_bday", author_id, prompt)
        await prompt.add_reaction("☑️")

        try:
            await self.bot.wait_for(
                "reaction_add",
                check=reaction_check,
                timeout=30.0
            )
        except asyncio.TimeoutError:
            await _delete_prompt_if_exists("set_bday", author_id, prompt)
        else:
            ## make bday permanent
            await _set_birthday(ctx.author.id, iso_birthday)
            not_shown_msg = (
                "\n\n\N{WARNING SIGN}Your birthday will **not** "
                "be announced in any servers. To enable announcements here,"
                " type `!bd toggle`"
            )

            embed.description = (
                "🥳 Congratulations! Your birthday has been updated to "
                f"**{_beautify_date(iso_birthday)}**. 🎊"
            )

            if not await _get_shown_guild_ids(ctx.author.id):
                embed.description += not_shown_msg
            embed.clear_fields()
            embed.add_field(
                name=ZERO_WIDTH_CHAR,
                value=(
                    "_This message will auto conceal "
                    "your birthday in 1 minute..._"
                ),
                inline=False)

            sent = await ctx.send(embed=embed)
            await _delete_prompt_if_exists("set_bday", author_id, prompt)

            await asyncio.sleep(60.0)
            embed.description = (
                "🥳 Congratulations! Your birthday has been updated! 🎊"
            )
            if not await _get_shown_guild_ids(ctx.author.id):
                embed.description += not_shown_msg

            embed.clear_fields()
            await sent.edit(embed=embed)


    @commands.is_owner()
    @birthday.group(name="delete", aliases=["del", "remove"])
    async def user_delete(self, ctx):
        """
        Deletes your own birthday from the database.

        "!birthday delete"
        """
        msg = ""
        embed = GET_BASE_EMBED()

        if await _get_birthday(ctx.author.id):
            await _delete_birthday(ctx.author.id)
            msg = (
                "Your birthday was successfully **removed**. "
                "Feel free to add it again when you're ready! 🤞"
            )
        else:
            msg = (
                "I didn't know your birthday, 🤷🏼‍♀️ but we "
                "made sure to keep the place extra clean in case you'd "
                "like to add it one day!💪🏾"
            )

        #add the tip if the user now has no birthday
        end_tip = "_To set your birthday use the command `!birthday set dd.mm`_"
        embed.add_field(name=ZERO_WIDTH_CHAR, value=end_tip, inline=False)

        embed.description = msg
        await ctx.send(embed=embed)

    @birthday.group(name="toggle", aliases=["hide", "show"])
    async def user_toggle_visibility(self, ctx):
        """
        Toggles whether birthday will be announced in this server.

        "!birthday toggle"
        """
        embed = GET_BASE_EMBED()
        msg = ""

        if not isinstance(ctx.channel, discord.abc.GuildChannel):
            msg = "You can only use this command in a server."

        if not await _get_birthday(ctx.author.id):
            await ctx.invoke(self.bot.get_command("birthday set"))
            return

        shown = await _birthday_toggle_visibility(ctx.author.id, ctx.guild.id)
        if shown:
            msg = "Your birthday **will be announced** in this server. ☑️"
        else:
            msg = "Your birthday **will not be announced** in this server. ❌"

        embed.description = msg
        await ctx.send(embed=embed)


    @birthday.group(name="servers", aliases=["s", "server"])
    async def user_get_shown_guilds(self, ctx):
        """
        Shows the servers in which your birthday will be announced.

        "!birthday servers"
        """
        author_id = ctx.author.id

        ## declare priv message variables so that the second
        # block can access them
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

        end_tip = (
            "\n\n_To hide or show in a particular server, type "
            "`!birthday toggle` in a text channel there._"
        )


        user_birthday = await _get_birthday(author_id)
        if user_birthday:
            priv_title = f"Your birthday is: {_beautify_date(user_birthday)}"
        else:
            priv_title = "You have not set a birthday. Use `!bd set` to see how."

        shown_guild_ids = await _get_shown_guild_ids(author_id)
        shown_guild_names = await self._get_guild_names(shown_guild_ids)
        enumerated_guild_names= await self._get_enumerated_guild_names(shown_guild_names)

        # check just in case one or more guild_id didnt convert to a name
        if len(enumerated_guild_names) > 0:
            priv_description = (
                "**Your birthday will be announced in the following servers:**\n"
            )
            priv_description += enumerated_guild_names
        else:
            priv_title = "Your birthday will not be announced in any servers."

        # format & send private message, saving it's URL in case
        # we need to link to it below.
        priv_embed.title = priv_title
        priv_embed.description = priv_description
        priv_embed.add_field(name=ZERO_WIDTH_CHAR, value=end_tip, inline=False)
        priv_msg = await ctx.author.send(embed=priv_embed)
        priv_msg_url = priv_msg.jump_url


        if not isinstance(ctx.channel, discord.abc.GuildChannel):
            return
        # implicit else:
        pub_description = (
            "🕵🏽 For privacy reasons, we sent you a DM with the information "
            f"requested. 🛰\n\n[**Jump to DM** ⤴️]({priv_msg_url})"
        )

        pub_embed.add_field(name=ZERO_WIDTH_CHAR, value=end_tip, inline=False)
        pub_embed.description = pub_description
        pub_msg = await ctx.send(embed=pub_embed)
        pub_msg_url = pub_msg.jump_url

        priv_embed.description += (
            f"\n\n\n[**Jump back to channel** ↩️]({pub_msg_url})"
        )

        await priv_msg.edit(embed=priv_embed)

    @birthday.group(name="channel", aliases=["c"])
    @commands.has_permissions(manage_channels=True)
    async def user_set_channel(self, ctx, given_channel=None):
        """
        You need the \"Manage Channels\" permissions to use this command.
        Either type part of a channel name e.g "!birthday channel chicken-cottage" \
for a channel called "🍗-chicken-cottage-place". \
Or paste the channel ID. "!birthday channel 54325254325432"

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
                msg = (
                    "Current birthday announcement channel is "
                    f"**{channel_name}**. ID: {current_bday_channel_id}"
                )
            else:
                msg = (
                    "There is currently no set channel for birthday announcements."
                    "\nTo see how to set one, type `!help bd c`."
                )
            embed.description = msg
            return await ctx.send(embed=embed)

        # Case: We have been given a string that the user wishes to set channel as
        channel_id = None
        try:
            channel_id = int(given_channel)
            if not isinstance(self.bot.get_channel(channel_id), discord.TextChannel):
                channel_id = None

        except ValueError:
            for channel in ctx.guild.channels:
                if (isinstance(channel, discord.TextChannel) and
                    given_channel.lower() in channel.name.lower()):
                    channel_id = channel.id

        if channel_id is None:
            msg = "I could not find that channel in this server."
        elif not self.bot.get_channel(channel_id) in ctx.guild.channels:
            msg = (
                "I could not find that channel in this server. "
                "Please make sure I have valid roles to see the channel."
            )
        elif not ctx.me.permissions_in(self.bot.get_channel(channel_id)).send_messages:
            msg = "I do not have the permission to send messages in that channel."

        if msg is not None:
            embed.description = msg
            sent = await ctx.send(embed=embed)
            return sent

        ## handle not found channels above, handle found channels and confirmation below

        channel = self.bot.get_channel(channel_id)
        msg = (
            f"You would like to set **{channel.name}**, (ID: {channel.id})"
            " to be the birthday announcement channel.\n\nReact with ☑️ if this is correct."
        )
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
