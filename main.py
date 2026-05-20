import disnake
from disnake.ext import commands
from disnake.ext.commands import NotOwner
from conf import *
from helpers import *
from monitor import *

intents = disnake.Intents.default()
intents.members = True
intents.guilds = True
intents.message_content = True
bot = commands.InteractionBot(intents=intents)

bot_name = "CAR Judicial Services"
monitor = UniversalMonitor(bot, bot_name, webhook_url)
flag_path = "restart.flag"
tickets_to_claim = {}

@bot.slash_command(name="ticketpanel", description="Post the support ticket panel.")
async def ticketpanel(interaction: disnake.ApplicationCommandInteraction):

    if not is_role(admins, interaction.user):
        return await interaction.response.send_message(
            "Admins only.", ephemeral=True
        )

    support_channel = interaction.guild.get_channel(support_channel_id)

    desc = ("# Concord Court Services\n"
            "## Trial Courts <:gov_cjs_trial:1431370068960481420>\n"
            "**District Court**\n"
            "- This court handles civil matters ranging from disputes to lawsuits\n"
            "\n"
            "**Superior Court**\n"
            "- This court processes criminal offenses ranging from infractions to felonies. "
            "Law Enforcement officials go through this court to get approval for warrants.\n"
            "\n"
            "## Supreme Court <:gov_cjs_sc:1431370019056386290>\n"
            "- This court is the highest appellate court in the state. Matters brought before this court are reviewed and all decisions are final.\n"
            "\n"
            "## Attorney Services\n"
            "**District Attorney's Office** <:gov_cjs_da:1431370570838179870>\n"
            "- This office brings charges against defendants in criminal trials and represents the state in civil suits.\n"
            "\n"
            "**State Bar Association** <:gov_cjs_bar:1432818197610102845> \n"
            "- This is an association of all certified attorneys in the state representing clients in legal matters.")

    embed = disnake.Embed(
        title="<:gov_cjs:1429566931962302734> Concord Judicial Services",
        description=desc
    )

    view = SupportPanelView()

    await support_channel.send(
        embed=embed,
        view=view
    )

    await interaction.response.send_message("Support panel posted!", ephemeral=True)

class SupportPanelView(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @disnake.ui.button(
        label="District Courts",
        style=disnake.ButtonStyle.blurple,
        custom_id="ticket_create"
    )
    async def district_court_ticket(
            self,
            button: disnake.ui.Button,
            interaction: disnake.Interaction,

    ):
        await district_court_thread(interaction)

    @disnake.ui.button(
        label="Superior Court Ticket",
        style=disnake.ButtonStyle.blurple,
        custom_id="superior_create"
    )
    async def superior_court_ticket(
            self,
            button: disnake.ui.Button,
            interaction: disnake.Interaction,
    ):
        await superior_court_thread(interaction)

    @disnake.ui.button(
        label="Supreme Court Ticket",
        style=disnake.ButtonStyle.blurple,
        custom_id="supereme_create"
    )
    async def supreme_court_ticket(
            self,
            button: disnake.ui.Button,
            interaction: disnake.Interaction,
    ):
        await supreme_court_thread(interaction)

    @disnake.ui.button(
        label="District Attorney Ticket",
        style=disnake.ButtonStyle.blurple,
        custom_id="da_create"
    )
    async def da_ticket(
            self,
            button: disnake.ui.Button,
            interaction: disnake.Interaction,
    ):
        await da_thread(interaction)

    @disnake.ui.button(
        label="Attorney Ticket",
        style=disnake.ButtonStyle.blurple,
        custom_id="bar_create"
    )
    async def bar_court_ticket(
            self,
            button: disnake.ui.Button,
            interaction: disnake.Interaction,
    ):
        await lawyer_thread(interaction)

async def district_court_thread(interaction: disnake.Interaction):

    user = interaction.user
    channel = interaction.client.get_channel(support_channel_id)
    guild = interaction.guild

    ticket_number = get_next_ticket_number()
    thread_name = f"district-ticket-{ticket_number:04d}"

    thread = await channel.create_thread(
        name=thread_name,
        type=disnake.ChannelType.private_thread,
        invitable=False
    )

    await thread.add_user(user)

    overwrites = {
        guild.default_role: disnake.PermissionOverwrite(view_channel=False),  # Hide from everyone
        user: disnake.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True
        )
    }

    for role_id in trial_roles:
        role = guild.get_role(role_id)
        if role:
            overwrites[role] = disnake.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_messages=True
            )

    embed = disnake.Embed(
        title="District Court Ticket",
        description="Please fill out the following information before this ticket is claimed.\n"
                    "```\n"
                    "Username of Defendant: \n"
                    "Username of Plaintiff: \n"
                    "\n" 
                    "Alleged Offenses: \n" 
                    "- [Penal Code] [Offense]\n"
                    "Description: \n"
                    "Evidence: \n"
                    "```"
    )

    await thread.send(
        f"**New Ticket** created by {user.mention}\n",
        embed=embed,
    )

    test_claim_forum = guild.get_channel(ticket_claim_forum)
    forum_post = await test_claim_forum.create_thread(name=thread_name,
                                         content="New ticket created please type 'Claim' to claim this ticket")
    tickets_to_claim[forum_post.thread.id] = thread.id

    await interaction.response.send_message(
        f"Your ticket has been created: {thread.mention}",
        ephemeral=True, delete_after=15
    )

async def superior_court_thread(interaction: disnake.Interaction):
    user = interaction.user
    channel = interaction.client.get_channel(support_channel_id)
    guild = interaction.guild

    ticket_number = get_next_ticket_number()
    thread_name = f"superior-ticket-{ticket_number:04d}"

    thread = await channel.create_thread(
        name=thread_name,
        type=disnake.ChannelType.private_thread,
        invitable=False
    )

    await thread.add_user(user)

    overwrites = {
        guild.default_role: disnake.PermissionOverwrite(view_channel=False),  # Hide from everyone
        user: disnake.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True
        )
    }

    for role_id in trial_roles:
        role = guild.get_role(role_id)
        if role:
            overwrites[role] = disnake.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_messages=True
            )

    embed = disnake.Embed(
        title="Superior Court Ticket",
        description="Please fill out the following information before this ticket is claimed.\n"
                    "```\n"
                    "Username of Defendant: \n"
                    "\n" 
                    "Alleged Offenses: \n" 
                    "- [Penal Code] [Offense]\n"
                    "Description: \n"
                    "Evidence: \n"
                    "Signatures: \n"
                    "```"
    )

    await thread.send(
        f"**New Ticket** created by {user.mention}\n",
        embed=embed
    )

    test_claim_forum = guild.get_channel(ticket_claim_forum)
    forum_post = await test_claim_forum.create_thread(name=thread_name,
                                         content="New ticket created please type 'Claim' to claim this ticket")
    tickets_to_claim[forum_post.thread.id] = thread.id

    await interaction.response.send_message(
        f"Your ticket has been created: {thread.mention}",
        ephemeral=True, delete_after=15
    )

async def supreme_court_thread(interaction: disnake.Interaction):
    user = interaction.user
    channel = interaction.client.get_channel(support_channel_id)
    guild = interaction.guild

    ticket_number = get_next_ticket_number()
    thread_name = f"supreme-court-ticket-{ticket_number:04d}"

    thread = await channel.create_thread(
        name=thread_name,
        type=disnake.ChannelType.private_thread,
        invitable=False
    )

    await thread.add_user(user)

    overwrites = {
        guild.default_role: disnake.PermissionOverwrite(view_channel=False),  # Hide from everyone
        user: disnake.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True
        )
    }

    for role_id in supreme_court_roles:
        role = guild.get_role(role_id)
        if role:
            overwrites[role] = disnake.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_messages=True
            )

    staff_ping = " ".join(f"<@&{rid}>" for rid in supreme_court_roles)

    embed = disnake.Embed(
        title="Supreme Court Ticket",
        description="Hello, \n"
                    "Please provide all information of what you would need reviewed by the Justices. Please be as detailed as possible so a proper review is conducted on the matter. \n"
    )

    await thread.send(
        f"{staff_ping}\n"
        f"**New Ticket** created by {user.mention}\n",
        embed=embed,
    )

    test_claim_forum = guild.get_channel(ticket_claim_forum)
    forum_post = await test_claim_forum.create_thread(name=thread_name,
                                         content="New ticket created please type 'Claim' to claim this ticket")
    tickets_to_claim[forum_post.thread.id] = thread.id

    await interaction.response.send_message(
        f"Your ticket has been created: {thread.mention}",
        ephemeral=True, delete_after=15
    )

async def da_thread(interaction: disnake.Interaction):
    user = interaction.user
    channel = interaction.client.get_channel(support_channel_id)
    guild = interaction.guild

    ticket_number = get_next_ticket_number()
    thread_name = f"da-court-ticket-{ticket_number:04d}"

    thread = await channel.create_thread(
        name=thread_name,
        type=disnake.ChannelType.private_thread,
        invitable=False
    )

    await thread.add_user(user)

    overwrites = {
        guild.default_role: disnake.PermissionOverwrite(view_channel=False),  # Hide from everyone
        user: disnake.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True
        )
    }

    for role_id in da_roles:
        role = guild.get_role(role_id)
        if role:
            overwrites[role] = disnake.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_messages=True
            )

    embed = disnake.Embed(
        title="District Attorney Ticket",
        description="Hello, please provide detailed information for the DA or ADA to review. If you are wishing for them to prosecute an individual, please utilize the following format.\n"
                    "```\n"
                    "Username of Defendant: \n"
                    "\n" 
                    "Alleged Offenses: \n" 
                    "- [Penal Code] [Offense]\n"
                    "Description: \n"
                    "Evidence: \n"
                    "```"
    )

    await thread.send(
        f"**New Ticket** created by {user.mention}\n",
        embed=embed
    )

    test_claim_forum = guild.get_channel(ticket_claim_forum)
    forum_post = await test_claim_forum.create_thread(name=thread_name,
                                         content="New ticket created please type 'Claim' to claim this ticket")
    tickets_to_claim[forum_post.thread.id] = thread.id

    await interaction.response.send_message(
        f"Your ticket has been created: {thread.mention}",
        ephemeral=True, delete_after=15
    )

async def lawyer_thread(interaction: disnake.Interaction):
    user = interaction.user
    channel = interaction.client.get_channel(support_channel_id)
    guild = interaction.guild

    ticket_number = get_next_ticket_number()
    thread_name = f"bar-ticket-{ticket_number:04d}"

    thread = await channel.create_thread(
        name=thread_name,
        type=disnake.ChannelType.private_thread,
        invitable=False
    )

    await thread.add_user(user)

    overwrites = {
        guild.default_role: disnake.PermissionOverwrite(view_channel=False),  # Hide from everyone
        user: disnake.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True
        )
    }

    for role_id in bar_roles:
        role = guild.get_role(role_id)
        if role:
            overwrites[role] = disnake.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_messages=True
            )

    embed = disnake.Embed(
        title="BAR Ticket",
        description="Hello, please provide a detailed description of what you are looking for so an Attorney can assist you.\n"
    )

    await thread.send(
        f"**New Ticket** created by {user.mention}\n",
        embed=embed
    )

    test_claim_forum = guild.get_channel(ticket_claim_forum)
    forum_post = await test_claim_forum.create_thread(name=thread_name,
                                         content="New ticket created please type 'Claim' to claim this ticket")
    tickets_to_claim[forum_post.thread.id] = thread.id

    await interaction.response.send_message(
        f"Your ticket has been created: {thread.mention}",
        ephemeral=True, delete_after=15
    )

@bot.slash_command(name="closeticket", description="Close the current ticket.")
async def close_ticket(interaction: disnake.ApplicationCommandInteraction):
    thread = interaction.channel
    if not isinstance(thread, disnake.Thread):
        return await interaction.response.send_message(
            "This command can only be used inside a ticket thread.",
            ephemeral=True
        )

    if not any(role.id in staff_roles for role in interaction.user.roles):
        return await interaction.response.send_message(
            "Only staff can close tickets.",
            ephemeral=True
        )

    await interaction.response.send_message("📝 Generating transcript...")

    transcript_lines = []
    async for msg in thread.history(limit=None, oldest_first=True):
        timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M")
        author = msg.author.display_name
        content = msg.content.replace("\n", "\\n")
        transcript_lines.append(f"[{timestamp}] {author}: {content}")

    transcript_text = "\n".join(transcript_lines)

    filename = f"tickets/{thread.name}_transcript.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(transcript_text)

    transcript_channel = interaction.guild.get_channel(transcript_channelId)

    if transcript_channel:
        await transcript_channel.send(
            f"**Transcript for {thread.name}**",
            file=disnake.File(filename)
        )

    await thread.send("🧾 Transcript generated and saved. This ticket will be deleted in **5 seconds**...")
    await thread.edit(archived=True, locked=True)
    await asyncio.sleep(5)

    try:
        await thread.delete()
    except Exception as e:
        print(f"Error deleting thread: {e}")

@bot.event
async def on_message(message: disnake.Message):
    if message.author.bot:
        return

    if not isinstance(message.channel, disnake.Thread):
        return

    claim_thread_id = message.channel.id
    claim_thread = message.guild.get_thread(claim_thread_id)
    keyword = "Claim"

    if message.content == keyword:
        ticket_thread = await message.guild.fetch_channel(tickets_to_claim[claim_thread_id])
        msg = f"Ticket has been **claimed** by {message.author.mention}!"
        await ticket_thread.send(msg)
        await claim_thread.delete()
        del tickets_to_claim[claim_thread_id]

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
async def on_ready():
    if os.path.exists(flag_path):
        await monitor.report_restart()

    with open(flag_path, "w") as f:
        f.write("running")

    await monitor.report_online()
    bot.loop.create_task(monitor.heartbeat())

    bot.add_view(SupportPanelView())
    print(f"Bot started {bot.user}")

bot.run(bot_token)