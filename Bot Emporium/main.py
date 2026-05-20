import disnake
from disnake import TextInputStyle, ModalInteraction
from disnake.ext import commands, tasks
from conf import *
from helpers import *

intents = disnake.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.InteractionBot(intents=intents)
dashboard_msg_id = 0

class VerificationModal(disnake.ui.Modal):
    def __init__(self, captcha_text, data):
        self.captcha_text = captcha_text
        self.data = data
        components = [
            disnake.ui.File(fp=data, filename="captcha.png"),

            disnake.ui.TextInput(
                label="Solve the CAPTCHA to Verify",
                placeholder="Enter the CAPTCHA...",
                custom_id="user_captcha",
                style=TextInputStyle.short,
                max_length=6,
                min_length=6,
                required=True
            )
        ]
        super().__init__(
            title="CAPTCHA Verification",
            components=components,
            custom_id="verification_modal"
        )

    async def callback(self, interaction: ModalInteraction):
        user_captcha = interaction.text_values['user_captcha']

# @bot.slash_command(name="verify", description="Verification process for the server")
# async def verify(inter: disnake.ApplicationCommandInteraction):
#     data, captcha_text = create_captcha()
#     temp_file = disnake.File(fp=data, filename="captcha.png")
#     await inter.send("Solve the CAPTCHA to verify", file=temp_file)


class SupportPanelView(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @disnake.ui.button(
        label="Bot Request",
        style=disnake.ButtonStyle.blurple,
        custom_id="request_create"
    )
    async def bot_request_ticket(
            self,
            button: disnake.ui.Button,
            interaction: disnake.Interaction,

    ):
        await bot_request_thread(interaction)

    @disnake.ui.button(
        label="Bot Incident",
        style=disnake.ButtonStyle.red,
        custom_id="incident_create"
    )
    async def bot_incident_ticket(
            self,
            button: disnake.ui.Button,
            interaction: disnake.Interaction,

    ):
        await bot_incident_thread(interaction)

async def bot_request_thread(interaction: disnake.Interaction):
    user = interaction.user
    channel = interaction.client.get_channel(support_channel_id)
    guild = interaction.guild

    ticket_number = get_next_ticket_number()
    thread_name = f"bot-request-{ticket_number:04d}"

    # Create private thread
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

    for role_id in developer_role_id:
        role = guild.get_role(role_id)
        if role:
            overwrites[role] = disnake.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_messages=True
            )

    staff_ping = " ".join(f"<@&{rid}>" for rid in developer_role_id)

    embed = disnake.Embed(
        title="Bot Request Ticket",
        description="Please fill out the following information: \n"
                    "```\n"
                    "What kind of bot are you seeking? \n"
                    "How large of a community? \n"
                    "Do you require data storage? \n"
                    "Any other important information: \n"
                    "```"
    )

    await thread.send(
        f"{staff_ping}\n"
        f"**New Request** created by {user.mention}\n",
        embed=embed
    )
    await interaction.response.send_message(
        f"Your ticket has been created: {thread.mention}",
        ephemeral=True, delete_after=15
    )

async def bot_incident_thread(interaction: disnake.Interaction):
    user = interaction.user
    channel = interaction.client.get_channel(support_channel_id)
    guild = interaction.guild

    ticket_number = get_next_ticket_number()
    thread_name = f"bot-incident-{ticket_number:04d}"

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

    for role_id in developer_role_id:
        role = guild.get_role(role_id)
        if role:
            overwrites[role] = disnake.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_messages=True
            )

    staff_ping = " ".join(f"<@&{rid}>" for rid in developer_role_id)

    embed = disnake.Embed(
        title="Bot Incident Ticket",
        description="Please fill out the following information: \n"
                    "```\n"
                    "What kind of issue are you seeing? \n"
                    "Urgency: \n "
                    "-# Critical (bot not responding), Moderate (Some commands are not responding), Low (occasional but low impact issues) \n"
                    "How often does this occur? When did it occur last? \n"
                    "Any other important information relating: \n"
                    "```"
    )

    await thread.send(
        f"{staff_ping}\n"
        f"**New Incident** created by {user.mention}\n",
        embed=embed
    )
    await interaction.response.send_message(
        f"Your ticket has been created: {thread.mention}",
        ephemeral=True, delete_after=15
    )


@bot.slash_command(name="information_panel", description="[STAFF] Posts the information panel")
async def info_panel(inter: disnake.ApplicationCommandInteraction):

    if not is_role(admin_roles,inter.user):
        return await inter.response.send_message(
            "Admins only.", ephemeral=True, delete_after=10
        )

    msg = ("# What is offered\n"
           "- Fully customized Discord bot\n"
           "- Bot Hosting ( I do not host code that is not my own)\n"
           "- Custom commands\n"
           "- Custom bot events\n"
           "- Data storing\n"
           "- Bot Support\n"
           "\n"
           "# Pricing\n"
           "- All bot pricing is handled on a case by case basis.\n"
           "\n"
           "### For any questions or inquiries feel free to open a request ticket.\n"
           "### To report any issues send a direct dm to bat_nation0224 or open an incident ticket.\n")

    view = SupportPanelView()

    embed = disnake.Embed(
        title="Information",
        color=disnake.Color.blurple(),
        description=msg
    )

    channel = inter.client.get_channel(support_channel_id)
    await channel.send(embed=embed, view=view)
    await inter.response.send_message("Success", ephemeral=True, delete_after=5)

@bot.slash_command(name="closeticket", description="Close the current ticket.")
async def close_ticket(interaction: disnake.ApplicationCommandInteraction):
    thread = interaction.channel
    if not isinstance(thread, disnake.Thread):
        return await interaction.response.send_message(
            "This command can only be used inside a ticket thread.",
            ephemeral=True
        )

    if not any(role.id in developer_role_id for role in interaction.user.roles):
        return await interaction.response.send_message(
            "Only staff can close tickets.",
            ephemeral=True
        )

    await interaction.response.send_message("Ticket Locked and Archived")
    await thread.edit(archived=True, locked=True)

    return None

@bot.slash_command(name="embed_say")
async def embed_say(interaction: disnake.ApplicationCommandInteraction,
                        title: str = commands.Param(default=None, description="(Optional) Title of the Embed"),
                        color=commands.Param(choices={
                            "Green": "green",
                            "Red": "red",
                            "Blurple": "blurple",
                            "Orange": "orange",
                            "Yellow": "yellow",
                            "Light Grey": "l_gray",
                            "Dark Grey": "d_grey",
                            "Random": "random"
                        })):
    class EmbedSayModel(disnake.ui.Modal):
        def __init__(self, color, title: str = None):

            self.user_title = title
            self.user_color = color
            components = [
                disnake.ui.TextInput(
                    label="Narrative",
                    placeholder="Enter message here....",
                    custom_id="user_message",
                    style=disnake.TextInputStyle.paragraph,
                    max_length=1024,
                    required=True,
                )
            ]
            super().__init__(
                components=components,
                custom_id="embed_modal",
                title=title if title else "Create Message"
            )

        async def callback(self, interaction: disnake.ModalInteraction):
            message = interaction.text_values['user_message']
            if self.user_title:
                embed = disnake.Embed(
                    title=self.user_title,
                    color=self.user_color,
                    description=message
                )
            else:
                embed = disnake.Embed(
                    color=self.user_color,
                    description=message
                )

            await interaction.channel.send(embed=embed)
            await interaction.response.send_message("Embed Sent", ephemeral=True, delete_after=5)

    if not is_role(admin_roles,interaction.user):
        return await interaction.response.send_message(
            "Admins only.", ephemeral=True, delete_after=10
        )

    user_color = disnake.Color.blurple()
    if color == "green":
        user_color = disnake.Color.green()
    elif color == "red":
        user_color = disnake.Color.red()
    elif color == "blurple":
        user_color = disnake.Color.blurple()
    elif color == "orange":
        user_color = disnake.Color.orange()
    elif color == "yellow":
        user_color = disnake.Color.yellow()
    elif color == "l_gray":
        user_color = disnake.Color.light_grey()
    elif color == "d_grey":
        user_color = disnake.Color.dark_grey()
    elif color == "random":
        user_color = disnake.Color.random()

    if title:
        modal = EmbedSayModel(title=title, color=user_color)
    else:
        modal = EmbedSayModel(color=user_color)

    await interaction.response.send_modal(modal)

@tasks.loop(minutes=15)
async def tracked_bots_statuses():
    global dashboard_msg_id
    channel = bot.get_channel(bot_status_channel_id)

    cpu_use, mem = system_status()
    cpu_msg = f"CPU Usage: {cpu_use}%"
    mem_msg = f"Memory Stats: Utilizing {mem.percent}%"

    embed = disnake.Embed(title="Bot Statuses",
                          description=f"Quick Status check on tracked bots. Updates every 15 minutes.\n\n**System Status:**\n{cpu_msg}\n{mem_msg}")

    for botname in tracked_bots:
        bot_code = bot_status(botname)
        if bot_code == 0:
            embed.add_field(name=tracked_bots[botname], value=":green_circle: Bot is Active")
        else:
            embed.add_field(name=tracked_bots[botname], value=":red_circle: Bot is Down!")

    if dashboard_msg_id == 0:
        msg = await channel.send(embed=embed)
        dashboard_msg_id = msg.id
    else:
        dash = await channel.fetch_message(dashboard_msg_id)
        await dash.edit(embed=embed)

@bot.event
async def on_ready():
    print(f"Bot logged in {bot.user}")
    bot.add_view(SupportPanelView())
    if not tracked_bots_statuses.is_running():
        tracked_bots_statuses.start()

bot.run(token)
