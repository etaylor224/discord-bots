import disnake
from disnake.ext import commands
from disnake.ext.commands import is_owner, NotOwner
from disnake.ui import View
import db_helpers
from monitor import UniversalMonitor
import traceback
import os
from conf import TOKEN, approved_guilds, webhook_url
from helpers import *

intents = disnake.Intents.default()
intents.members = True
intents.guilds = True
intents.message_content = True

bot = commands.InteractionBot(intents=intents, test_guilds=approved_guilds)

bot_name = "CAR Arrest Logger"
monitor = UniversalMonitor(bot, bot_name, webhook_url)
flag_path = "restart.flag"

AGENCY_CHOICES = [
    disnake.OptionChoice(name="CBI",  value="CBI <:cbi:1261600832906858558>"),
    disnake.OptionChoice(name="CANG", value="CANG <:cang:1353168128611450940>"),
    disnake.OptionChoice(name="PIT",  value="PIT <:pit:1323111232818905171>"),
    disnake.OptionChoice(name="FWS",  value="FWS <:cfws:1128065873022820453>"),
]

# todo #1 add warrant logic, that interacts with database somehow (i can handle the db helper calls)
# todo #2 paginate or do something to prevent the user_lookup command from breaking at the 25 embed field limit (it will happen)


async def collect_evidence(inter: disnake.ApplicationCommandInteraction, session):
    """Wait for the user to upload an image in the channel."""
    def check(msg: disnake.Message):
        return (
            msg.author.id == inter.author.id
            and msg.channel.id == inter.channel.id
            and msg.attachments
        )

    while True:
        msg = await bot.wait_for("message", check=check)
        attachment = msg.attachments[0]
        if attachment.content_type and attachment.content_type.startswith("image"):
            session.evidence_message = msg
            return
        else:
            await inter.followup.send("Please upload a valid image file.", ephemeral=True)

class ArrestSession:
    def __init__(self, defendant):
        self.defendant = defendant
        self.charges = []
        self.evidence_message = None
        self.agency = None

class ChargeSearchModal(disnake.ui.Modal):
    def __init__(self, session):
        self.session = session
        components = [
            disnake.ui.TextInput(
                label="Search charges",
                placeholder="e.g., murder, evading, assault",
                custom_id="query",
                style=disnake.TextInputStyle.short,
                required=True,
            )
        ]
        super().__init__(title="Search Charges", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        query = inter.text_values["query"].lower().strip()
        search = await db_helpers.search_legal_code(query)
        matches = [result for result in search[:25]]

        if not matches:
            return await inter.response.send_message("No charges found.", ephemeral=True)

        await inter.response.send_message(
            "Select charge(s):",
            view=ChargeSelectView(matches, self.session),
            ephemeral=True
        )

class NarrativeModal(disnake.ui.Modal):
    def __init__(self, session: ArrestSession):
        self.session = session
        components = [
            disnake.ui.TextInput(
                label="Incident Narrative",
                custom_id="narrative",
                style=disnake.TextInputStyle.paragraph,
                required=True,
                max_length=1024,
            )
        ]
        super().__init__(title="Incident Narrative", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        narrative = inter.text_values["narrative"]
        officer = inter.author
        session = self.session
        defendant = ""
        defendant_id = ""

        await inter.response.send_message(
            "**Upload ONE evidence screenshot now**\n• First image will be used",
            ephemeral=True
        )

        await collect_evidence(inter, session)

        felony = []
        misdemeanor = []
        for c in session.charges:
            entry = f"{c['code']} — {c['offense']}"
            if c["classification"].lower() == "felony":
                felony.append(entry)
            else:
                misdemeanor.append(entry)

        embed = disnake.Embed(title="ARREST REPORT", color=0x2F3136)

        embed.add_field(
            name="ARRESTING OFFICER",
            value=f"{officer.display_name} | {officer.id}",
            inline=True
        )

        if getattr(session, "agency", None):
            embed.add_field(name="AGENCY", value=session.agency, inline=True)

        if session.defendant:
            if isinstance(session.defendant, disnake.Member):
                embed.add_field(
                    name="DEFENDANT",
                    value=f"{session.defendant.display_name} | {session.defendant.id}",
                    inline=True
                )
                defendant += session.defendant.display_name
                defendant_id += str(session.defendant.id)
            else:
                embed.add_field(name="DEFENDANT", value=str(session.defendant), inline=True)
                defendant += session.defendant
        else:
            embed.add_field(name="DEFENDANT", value="UNKNOWN", inline=True)

        if felony:
            embed.add_field(name="FELONY CHARGE(S)", value="\n".join(felony), inline=False)
        if misdemeanor:
            embed.add_field(name="MISDEMEANOR CHARGE(S)", value="\n".join(misdemeanor), inline=False)

        embed.add_field(name="INCIDENT NARRATIVE", value=narrative, inline=False)
        embed.set_footer(text="Berkeley County MDT • Developed by bat_nation0224")

        files = []
        if session.evidence_message:
            attachment = session.evidence_message.attachments[0]
            file = await attachment.to_file()
            file.filename = "evidence.png"
            files.append(file)
            embed.set_image(url="attachment://evidence.png")

        await inter.channel.send(embed=embed, files=files, content=officer.mention)
        await inter.followup.send("Arrest report filed.", ephemeral=True)
        try:
            await session.evidence_message.delete()
        except disnake.Forbidden:
            pass

        await db_helpers.arrest_record_insert(
            defendant,
            str(officer.id),
            officer.display_name,
            narrative,
            session.agency,
            defendant_id,
            felony,
            misdemeanor
        )
        
class ChargeSelect(disnake.ui.StringSelect):
    def __init__(self, charges, session: ArrestSession):
        self.charge_data = charges
        self.session = session

        seen = set()
        options = []
        for c in charges:
            if c["code"] not in seen:
                seen.add(c["code"])
                options.append(
                    disnake.SelectOption(
                        label=c["code"],
                        description=f"{c['offense']} ({c['classification']})"[:100]
                    )
                )

        super().__init__(
            placeholder="Select charges to add",
            min_values=1,
            max_values=min(len(options), 25),
            options=options
        )

    async def callback(self, inter: disnake.MessageInteraction):
        added = 0
        for c in self.charge_data:
            if c["code"].strip() in self.values and c not in self.session.charges:
                self.session.charges.append(c)
                added += 1

        await inter.response.send_message(
            f"Added {added} charge(s).\nCurrent total: **{len(self.session.charges)}**",
            ephemeral=True
        )

class SearchAgainButton(disnake.ui.Button):
    def __init__(self, session: ArrestSession):
        super().__init__(label="Search Again", style=disnake.ButtonStyle.secondary)
        self.session = session

    async def callback(self, inter: disnake.MessageInteraction):
        await inter.response.send_modal(ChargeSearchModal(self.session))

class SubmitArrestButton(disnake.ui.Button):
    def __init__(self, session: ArrestSession):
        super().__init__(label="Submit Arrest", style=disnake.ButtonStyle.danger)
        self.session = session

    async def callback(self, inter: disnake.MessageInteraction):
        if not self.session.charges:
            return await inter.response.send_message("No charges selected.", ephemeral=True)
        await inter.response.send_modal(NarrativeModal(self.session))

class ChargeSelectView(View):
    def __init__(self, charges, session: ArrestSession):
        super().__init__(timeout=180)
        self.add_item(ChargeSelect(charges, session))
        self.add_item(SearchAgainButton(session))
        self.add_item(SubmitArrestButton(session))

async def member_autocomplete(inter: disnake.ApplicationCommandInteraction, current: str):
    if not inter.guild:
        return []
    current_lower = current.lower()
    choices = []
    for member in inter.guild.members:
        if current_lower in member.display_name.lower() or current_lower in member.name.lower():
            choices.append(disnake.OptionChoice(
                name=f"{member.display_name} ({member})",
                value=str(member.id)
            ))
        if len(choices) >= 25:
            break
    return choices

@bot.slash_command(name="arrest", description="File an arrest report")
async def arrest(
    inter: disnake.ApplicationCommandInteraction,
    target: str = commands.Param(description="The Discord member or the name of the defendant", autocomplete=member_autocomplete),
    agency: str = commands.Param(description="Select your agency", choices=AGENCY_CHOICES),
):
    member = None
    if inter.guild and target.isdigit():
        try:
            member = await inter.guild.fetch_member(int(target))
        except disnake.NotFound:
            member = None

    defendant = member or target

    session = ArrestSession(defendant)
    session.agency = agency

    await inter.response.send_modal(ChargeSearchModal(session))


@bot.slash_command(name="user_arrest_lookup", description="Look up the arrest records for a given user")
async def user_arrest_lookup(inter: disnake.ApplicationCommandInteraction,
                             username: str = commands.Param(description="The Discord member or the name of the defendant", autocomplete=member_autocomplete)):

    await inter.response.defer(ephemeral=True)
    records = await db_helpers.user_record_search(username)

    if records:
        embed = disnake.Embed(title=f"Arrest Records Report",
                              color=disnake.Color.blue(),
                              description=f"User has {len(records)} record(s)")

        for record in records:
            embed.add_field(name=f"File: {record['id']}",
                            value=f"Defendant: {record['defendant_username']}\n"
                                  f"Arresting Officer: {record['officer_username']}\n"
                                  f"Arresting Agency: {record['agency']}\n"
                                  f"Felony Charges: {record['charges_f']}\n"
                                  f"Misdemeanor Charges: {record['charges_m']}")

        await inter.followup.send(embed=embed)

    else:
        await inter.followup.send(f"No Records found for user")

@bot.slash_command(name="update_law", description="[OWNER] Updates the legal code")
@is_owner()
async def update_law(inter: disnake.ApplicationCommandInteraction):

    await inter.response.defer(ephemeral=True)

    data = load_legal_code()
    await db_helpers.clear_legal_code()
    await db_helpers.insert_legal_code(data)
    await inter.edit_original_response("Legal code updated")

@bot.slash_command(name="guild_check", description="Joined Guild details")
@is_owner()
async def guild_check(interaction: disnake.ApplicationCommandInteraction):
    joined_guilds = bot.guilds
    for guild in joined_guilds:
        await monitor.guild_report(guild)

@bot.slash_command(name="remove")
@is_owner()
async def remove(interaction: disnake.ApplicationCommandInteraction, guild_id):
    await interaction.response.defer(ephemeral=True)
    guild = bot.get_guild(int(guild_id))

    if guild is None:
        await interaction.followup.send("Error in guild id")

    guild_name = guild.name
    await guild.leave()
    await interaction.followup.send(f"Left {guild_name}", ephemeral=True)

@bot.event
async def on_slash_command(inter: disnake.ApplicationCommandInteraction):
    monitor.command_count += 1
    monitor.track_request()
    await monitor.check_rate_limit()

@bot.event
async def on_user_command(inter: disnake.UserCommandInteraction):
    monitor.command_count += 1
    monitor.track_request()
    await monitor.check_rate_limit()

@bot.event
async def on_message_command(inter: disnake.MessageCommandInteraction):
    monitor.command_count += 1
    monitor.track_request()
    await monitor.check_rate_limit()

@bot.event
async def on_button_click(inter: disnake.MessageInteraction):
    monitor.track_request()
    await monitor.check_rate_limit()

@bot.event
async def on_dropdown(inter: disnake.MessageInteraction):
    monitor.track_request()
    await monitor.check_rate_limit()

@bot.event
async def on_modal_submit(inter: disnake.ModalInteraction):
    monitor.track_request()
    await monitor.check_rate_limit()

@bot.event
async def on_error(event, *args, **kwargs):
    await monitor.report_error(Exception(traceback.format_exc()))

@bot.event
async def on_slash_command_error(inter: disnake.ApplicationCommandInteraction, error):
    if isinstance(error, NotOwner):
        ran_by = inter.user.display_name
        await inter.send("This command is owner-only.",ephemeral=True)
        if inter.guild.name:
            await monitor.report_warn(f"User: {ran_by} tried to run this command in {inter.guild.name}",
            context=f"/{inter.application_command.name}")
        else:
            await monitor.report_warn(f"User: {ran_by} tried to run this command.",
            context=f"/{inter.application_command.name}")

    else:
        await monitor.report_error(error, context=f"/{inter.application_command.name}")

@bot.event
async def on_modal_error(inter: disnake.ModalInteraction, error):
    await monitor.report_error(error, context=f"Modal: {inter.custom_id}")

@bot.event
async def on_button_click_error(inter: disnake.MessageInteraction, error):
    await monitor.report_error(error, context=f"Button: {inter.component.custom_id}")

@bot.event
async def on_dropdown_error(inter: disnake.MessageInteraction, error):
    await monitor.report_error(error, context=f"Dropdown: {inter.component.custom_id}")

@bot.event
async def on_guild_join(guild: disnake.Guild):
    new_guild = guild.id
    guild_owner = guild.owner_id

    if new_guild not in approved_guilds:

        inviter = None

        try:
            async for entry in guild.audit_logs(action=disnake.AuditLogAction.bot_add, limit=5):
                if entry.target.id == bot.user.id:
                    inviter = entry.user
                    break
        except disnake.Forbidden:
            print(f"[on_guild_join] No audit log access")
            await monitor.leave_report(guild, f"[on_guild_join] No audit log access")

        try:
            await guild.get_member(guild_owner).send(f"BOT NOT APPROVED FOR USE IN {guild.name}. BOT WILL BE LEAVING NOW!\n"
                                                     f"BOT INVITED BY {inviter}.\n"
                                                     f"FOR AUTHORIZATION CONTACT THE DEVELOPER.")
        except disnake.Forbidden:
            pass

        await monitor.leave_report(guild, inviter)
        await guild.leave()

@bot.event
async def on_ready():
    if os.path.exists(flag_path):
        await monitor.report_restart()

    with open(flag_path, "w") as f:
        f.write("running")

    await monitor.report_online()
    bot.loop.create_task(monitor.heartbeat())
    print(f"Logged in as {bot.user}")
    print(f"Rate limit threshold: {monitor.rate_limit_threshold} RPM")

bot.run(TOKEN)
