import disnake
import os
import json
from conf import ticket_data

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