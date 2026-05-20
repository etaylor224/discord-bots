import disnake
#from captcha.image import ImageCaptcha
import random
import string
import os
import json
import psutil
from conf import ticket_data

# def create_captcha():
#     random_text = random.choices(string.ascii_uppercase + string.digits, k=6)
#     captcha_text = ''.join(random_text)
#     image = ImageCaptcha(width=280, height=90)
#     data = image.generate(captcha_text)
#     return data, captcha_text

def is_role(role, member:disnake.Member):
    if member is None:
        return False
    return any(r.id in role for r in member.roles)

def load_ticket_data():
    if not os.path.exists(ticket_data):
        return {"last_ticket_id": 0}
    with open(ticket_data, "r") as f:
        return json.load(f)

def save_ticket_data(data):
    with open(ticket_data, "w") as f:
        json.dump(data, f, indent=4)

def get_next_ticket_number():
    data = load_ticket_data()
    data["last_ticket_id"] += 1
    save_ticket_data(data)
    return data["last_ticket_id"]

def bot_status(bot_name):
    return os.system(f"systemctl is-active --quiet {bot_name}")

def system_status():
    cpu_use = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    return cpu_use, mem
