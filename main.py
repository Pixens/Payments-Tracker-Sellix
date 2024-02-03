import yaml
import time
import json
import discord
import logging

from threading import Thread
from datetime import datetime
from flask import Flask, request, jsonify


log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)


with open("config.yml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)


class FlaskServer:
    def __init__(self):
        self.app = Flask("cashapp-payments")
        self.app.route(rule="/cashapp", methods=["POST"], callback=FlaskServer.receive_cashapp_payments)

    @staticmethod
    def receive_cashapp_payments():
        data = request.json
        if data["data"]["gateway"] == "CASH_APP":
            with open("balance.json", "r", encoding="utf-8") as file:
                balance = json.load(file)

            balance["balance"] += data["data"]["total"]
            with open("balance.json", "w", encoding="utf-8") as file:
                json.dump(balance, file, indent=4)

            print(f"Received cashapp payment of {data['data']['total']}")
            with open("log.log", "a", encoding="utf-8") as file:
                file.write(f"{datetime.now()} | Received cashapp payment of {data['data']['total']}\n")

            return jsonify(
                {
                    "status": "received"
                }
            ), 200

    def start(self):
        self.app.run(port=6969)


bot = discord.Bot(status=discord.Status.online)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} ({bot.user.id})")

@bot.slash_command(guild_ids=[config["guild-id"]], name="check-balance", description="Check the current cashapp balance.")
async def check_balance(ctx):
    if ctx.author.id not in config["whitelisted"]:
        return await ctx.send("You are not whitelisted to use this command.")

    with open("balance.json", "r", encoding="utf-8") as file:
        balance = json.load(file)

    return await ctx.send(f"The current balance is {balance['balance']}")

@bot.slash_command(guild_ids=[config["guild-id"]], name="remove-balance", description="Remove balance from the cashapp balance.")
async def remove_balance(ctx, amount: discord.Option(int, "The amount to remove from the balance.", required=False)):
    if ctx.author.id not in config["whitelisted"]:
        return await ctx.send("You are not whitelisted to use this command.")

    if not amount:
        with open("balance.json", "r", encoding="utf-8") as file:
            balance = json.load(file)

        old_balance = balance["balance"]

        balance["balance"] = 0
        with open("balance.json", "w", encoding="utf-8") as file:
            json.dump(balance, file, indent=4)

        return await ctx.send(f"Removed {old_balance} from the balance.")
    else:
        with open("balance.json", "r", encoding="utf-8") as file:
            balance = json.load(file)

        balance["balance"] -= amount
        with open("balance.json", "w", encoding="utf-8") as file:
            json.dump(balance, file, indent=4)

        return await ctx.send(f"Removed {amount} from the balance.")


@bot.slash_command(guild_ids=[config["guild-id"]], name="whitelist", description="Whitelist a user to use the commands.")
async def whitelist(ctx, user: discord.User):
    if ctx.author.id not in config["whitelisted"]:
        return await ctx.send("You are not whitelisted to use this command.")

    config["whitelisted"].append(user.id)
    with open("config.yml", "w", encoding="utf-8") as file:
        yaml.dump(config, file, indent=4)

    return await ctx.send(f"Whitelisted {user.mention}")


Thread(target=FlaskServer().start).start()
time.sleep(2)
print()
bot.run(config["bot-token"])