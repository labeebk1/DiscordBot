# bot.py
import os
import random
import datetime

import discord
from discord.ext import commands
from dotenv import load_dotenv

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from models import Hourly, Miner, Rob, Timestamp, User

# Load Discord Bot
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
bot = commands.Bot(command_prefix='.')

# Load Database
engine = create_engine('sqlite:///gamble.db', echo=False)
session = Session(engine)

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

@bot.command(name='bal', help='Check your balance or create your account.')
async def balance(ctx):
    
    members = ctx.message.mentions
    if members:
        member = members[0]
        member_name = members[0].name

    # Query if User exists
    if members:
        user = session.query(User).filter_by(name=member_name).first()
    else:
        user = session.query(User).filter_by(name=ctx.author.name).first()

    if not user and not members:
        user = create_user(ctx.author.name)

    if user:
        embed = discord.Embed(title=f"{user.name}'s Bank", 
                        color=discord.Color.random())

        if members:
            embed.set_thumbnail(url=member.avatar_url)
        else:
            embed.set_thumbnail(url=ctx.author.avatar_url)

        embed.add_field(name="Level",
                        value=f"```cs\n{str(user.level)}```", inline=True)
        embed.add_field(name="Wallet",
                        value=f"```cs\n${user.wallet:,d} Gold```", inline=True)
        embed.add_field(name="Bank",
                        value=f"```cs\n${user.bank:,d} Gold```", inline=True)

        embed.set_footer(text=f"{user.shields} Active Shields", icon_url = "https://thumbs.dreamstime.com/b/well-organized-fully-editable-antivirus-protection-security-icon-any-use-like-print-media-web-commercial-use-any-kind-158454387.jpg")

        await ctx.send(embed=embed)
    else:
        await ctx.send('User not found.')

@bot.command(name='flip', help='Do a 50-50 to double your money.')
async def flip(ctx, bet: str):
    # Query if User exists
    user = session.query(User).filter_by(name=ctx.author.name).first()

    if not user:
        user = create_user(ctx.author.name)

    bet = validate_bet(bet)

    if not bet:
        await ctx.send("Invalid bet. Format's Available: 1, 1k, 1K, 1m, 1M")
    
    elif bet > user.wallet:
        await ctx.send('Insufficient Funds.')
    
    else:
        if random.randint(0,1):
            user.wallet += bet
            embed = discord.Embed(title='Coin Flip', color=discord.Color.green())

            embed.add_field(name=f'{ctx.author.display_name}', value="You Won ^.^! :thumbsup:", inline=False)

            embed.add_field(name="Wallet",
                            value=f"```cs\n${user.wallet:,d} Gold```", inline=True)
            
            await ctx.send(embed=embed)
        else:
            user.wallet -= bet

            embed = discord.Embed(title='Coin Flip', color=discord.Color.red())

            embed.add_field(name=f'{ctx.author.display_name}', value="RIP You Lost X_X! :thumbsdown:", inline=False)

            embed.add_field(name="Wallet",
                            value=f"```cs\n${user.wallet:,d} Gold```", inline=True)
                            
            await ctx.send(embed=embed)

    session.commit()

@bot.command(name='dice', help='Do a 1 in 6 to 6x your money.')
async def dice(ctx, bet: str, dice_bet: str):
    # Query if User exists
    user = session.query(User).filter_by(name=ctx.author.name).first()

    if not user:
        user = create_user(ctx.author.name)

    bet = validate_bet(bet)

    if not bet:
        await ctx.send("Invalid bet. Format's Available: 1, 1k, 1K, 1m, 1M")
        return
    
    if not dice_bet or not dice_bet.isnumeric():
        await ctx.send("Invalid Selection for Dice Roll. Format's Available: 1, 2, 3, 4, 5, 6")
        return
    else:
        dice_bet = int(dice_bet)

    if dice_bet not in [1,2,3,4,5,6]:
        await ctx.send("Invalid Selection for Dice Roll. Format's Available: 1, 2, 3, 4, 5, 6")
        return

    elif bet > user.wallet:
        await ctx.send('Insufficient Funds.')
    else:
        bot_bet = random.randint(1,6)
        win = False
        if bot_bet == dice_bet:
            win = True

        if win:
            user.wallet += 6*bet
            embed = discord.Embed(title='Dice', color=discord.Color.green())
            embed.add_field(name=f'{ctx.author.display_name}', value="Holy shit You Won ^.^! :thumbsup:", inline=False)
            embed.add_field(name="Winnings",
                            value=f"```cs\n${6*bet:,d} Gold```", inline=False)
            embed.add_field(name="Wallet",
                            value=f"```cs\n${user.wallet:,d} Gold```", inline=False)
            embed.set_thumbnail(url=osrs_gp_url)
            await ctx.send(embed=embed)
        else:
            user.wallet -= bet
            embed = discord.Embed(title='Dice', color=discord.Color.red())
            embed.add_field(name=f'{ctx.author.display_name}', value="RIP You Lost X_X! :thumbsdown:", inline=False)
            embed.add_field(name="Your Move", value=f"```{dice_bet}```", inline=True)
            embed.add_field(name="Bot's Move", value=f"```{bot_bet}```", inline=True)
            embed.add_field(name="Wallet",
                            value=f"```cs\n${user.wallet:,d} Gold```", inline=False)
            await ctx.send(embed=embed)

    session.commit()

@bot.command(name='roll', help='Roll against the bot.')
async def roll(ctx, bet: str):
    # Query if User exists
    user = session.query(User).filter_by(name=ctx.author.name).first()

    if not user:
        user = create_user(ctx.author.name)

    bet = validate_bet(bet)

    if not bet:
        await ctx.send("Invalid bet. Format's Available: 1, 1k, 1K, 1m, 1M")
        return
    
    if bet > user.wallet:
        await ctx.send('Insufficient Funds.')
    else:
        bot_bet = random.randint(1,100)
        user_bet = random.randint(1,100)

        win = False
        if user_bet >= bot_bet:
            win = True

        if win:
            user.wallet += bet
            embed = discord.Embed(title='Roll', color=discord.Color.green())
            embed.add_field(name=f'{ctx.author.display_name}', value="Holy shit You Won ^.^! :thumbsup:", inline=False)
            embed.add_field(name="Your Roll", value=f"```{user_bet}```", inline=True)
            embed.add_field(name="Bot's Roll", value=f"```{bot_bet}```", inline=True)
            embed.add_field(name="Wallet",
                            value=f"```cs\n${user.wallet:,d} Gold```", inline=False)
            embed.set_thumbnail(url=osrs_gp_url)
            await ctx.send(embed=embed)
        else:
            user.wallet -= bet
            embed = discord.Embed(title='Roll', color=discord.Color.red())
            embed.add_field(name=f'{ctx.author.display_name}', value="RIP You Lost X_X! :thumbsdown:", inline=False)
            embed.add_field(name="Your Roll", value=f"```{user_bet}```", inline=True)
            embed.add_field(name="Bot's Roll", value=f"```{bot_bet}```", inline=True)
            embed.add_field(name="Wallet",
                            value=f"```cs\n${user.wallet:,d} Gold```", inline=False)
            await ctx.send(embed=embed)

    session.commit()

@bot.command(name='rps', help='Do a Rock Paper Scissors match.')
async def rps(ctx, bet: str, rps: str):
    # Query if User exists
    user = session.query(User).filter_by(name=ctx.author.name).first()

    if not user:
        user = create_user(ctx.author.name)

    bet = validate_bet(bet)

    if not bet:
        await ctx.send("Invalid bet. Format's Available: 1, 1k, 1K, 1m, 1M")
        return
    
    if not rps:
        await ctx.send("You must specify Rock (r), Paper (p), or Scissors (s) after the bet. Format: !rps 1k r")
        return
    
    if rps not in ['r', 'p', 's', 'rock', 'Rock', 'paper', 'Paper', 'Scissors']:
        await ctx.send("You must specify Rock (r), Paper (p), or Scissors (s) after the bet. Format: !rps 1k r")
        return

    if rps in ['r', 'rock']:
        rps = 'Rock'
    
    if rps in ['p', 'paper']:
        rps = 'Paper'
    
    if rps in ['s', 'scissors']:
        rps = 'Scissors'

    if bet > user.wallet:
        await ctx.send('Insufficient Funds.')
        return
    
    else:
        win = False
        draw = False

        bot_move = rps_moves[random.randint(0,2)] # 0 = rock, 1 = paper, 2 = scissors
    
        # Draw Criteria
        if bot_move == rps:
            draw = True

        # Win Criteria        
        if (rps == 'Rock' and bot_move == 'Scissors') or \
            (rps == 'Scissors' and bot_move == 'Paper') or \
                (rps == 'Paper' and bot_move == 'Rock'):
            
            win=True

        if draw:
            embed = discord.Embed(title='Rock Paper Scissors', color=discord.Color.blue())
            embed.add_field(name=f'{ctx.author.display_name}', value="Draw!", inline=False)
            embed.add_field(name="Your Move", value=f"```{rps}```", inline=True)
            embed.add_field(name="Bot's Move", value=f"```{bot_move}```", inline=True)
            embed.add_field(name="Wallet",
                            value=f"```cs\n${user.wallet:,d} Gold```", inline=False)
            await ctx.send(embed=embed)

        elif win:
            user.wallet += bet
            embed = discord.Embed(title='Rock Paper Scissors', color=discord.Color.green())
            embed.add_field(name=f'{ctx.author.display_name}', value="You Won ^.^! :thumbsup:", inline=False)
            embed.add_field(name="Your Move", value=f"```{rps}```", inline=True)
            embed.add_field(name="Bot's Move", value=f"```{bot_move}```", inline=True)
            embed.add_field(name="Wallet",
                            value=f"```cs\n${user.wallet:,d} Gold```", inline=False)
            
            await ctx.send(embed=embed)
        else:
            user.wallet -= bet
            embed = discord.Embed(title='Rock Paper Scissors', color=discord.Color.red())
            embed.add_field(name=f'{ctx.author.display_name}', value="RIP You Lost X_X! :thumbsdown:", inline=False)
            embed.add_field(name="Your Move", value=f"```{rps}```", inline=True)
            embed.add_field(name="Bot's Move", value=f"```{bot_move}```", inline=True)
            embed.add_field(name="Wallet",
                            value=f"```cs\n${user.wallet:,d} Gold```", inline=False)
            await ctx.send(embed=embed)
    
    session.commit()

@bot.command(name='work', help='Make some money.')
async def work(ctx):
    # Query if User exists
    user = session.query(User).filter_by(name=ctx.author.name).first()

    if not user:
        user = create_user(ctx.author.name)
        user.wallet += 1000

        embed = discord.Embed(title=f'Work Level {user.level}', color=discord.Color.green())
        embed.add_field(name=f'{ctx.author.display_name}', value="You earned $1,000", inline=False)
        embed.add_field(name="Wallet",
                        value=f"```cs\n${user.wallet:,d} Gold```", inline=True)
        await ctx.send(embed=embed)

        timestamp = Timestamp(
            user_id=user.id,
            last_worked=datetime.datetime.now()
        )
        session.add(timestamp)

    else:
        recent_job = session.query(Timestamp).filter_by(user_id=user.id).first()

        earnings = 10 ** (user.level + 2)
        if not recent_job:
            user.wallet += earnings
            embed = discord.Embed(title=f'Work Level {user.level}', color=discord.Color.green())
            embed.add_field(name=f'{ctx.author.display_name}', value=f"You earned ${earnings:,d}", inline=False)
            embed.add_field(name="Wallet",
                            value=f"```cs\n${user.wallet:,d} Gold```", inline=True)
            await ctx.send(embed=embed)

            timestamp = Timestamp(
                user_id=user.id,
                last_worked=datetime.datetime.now()
            )
            session.add(timestamp)
        else:
            time_delta = datetime.datetime.now() - recent_job.last_worked
            minutes = round(time_delta.total_seconds() / 60,0)
            if minutes > 10:
                user.wallet += earnings
                embed = discord.Embed(title=f'Work Level {user.level}', color=discord.Color.green())
                embed.add_field(name=f'{ctx.author.display_name}', value=f"You earned ${earnings:,d}", inline=False)
                embed.add_field(name="Wallet",
                                value=f"```cs\n${user.wallet:,d} Gold```", inline=True)
                await ctx.send(embed=embed)
                recent_job.last_worked = datetime.datetime.now()

            else:
                time_remaining = int(10-minutes)
                embed = discord.Embed(title=f'Work Level {user.level}', color=discord.Color.red())
                embed.add_field(name=f'{ctx.author.display_name}', value=f"{time_remaining} minutes remaining...", inline=False)
                await ctx.send(embed=embed)
    
    session.commit()

@bot.command(name='hourly', help='Make some money every hour.')
async def hourly(ctx):
    # Query if User exists
    user = session.query(User).filter_by(name=ctx.author.name).first()

    if not user:
        user = create_user(ctx.author.name)
        user.wallet += 5000

        embed = discord.Embed(title=f'Hourly Rewards!', color=discord.Color.green())
        embed.add_field(name=f'{ctx.author.display_name}', value="You earned $5,000", inline=False)
        embed.add_field(name="Wallet",
                        value=f"```cs\n${user.wallet:,d} Gold```", inline=True)
        await ctx.send(embed=embed)

        timestamp = Hourly(
            user_id=user.id,
            last_worked=datetime.datetime.now()
        )
        session.add(timestamp)

    else:
        recent_job = session.query(Hourly).filter_by(user_id=user.id).first()

        if not recent_job:
            user.wallet += 5000
            embed = discord.Embed(title=f'Hourly Rewards!', color=discord.Color.green())
            embed.add_field(name=f'{ctx.author.display_name}', value="You earned $5,000", inline=False)
            embed.add_field(name="Wallet",
                            value=f"```cs\n${user.wallet:,d} Gold```", inline=True)
            await ctx.send(embed=embed)

            timestamp = Hourly(
                user_id=user.id,
                last_worked=datetime.datetime.now()
            )
            session.add(timestamp)
        else:
            time_delta = datetime.datetime.now() - recent_job.last_worked
            minutes = round(time_delta.total_seconds() / 60,0)
            if minutes > 60:
                user.wallet += 5000
                embed = discord.Embed(title=f'Hourly Rewards!', color=discord.Color.green())
                embed.add_field(name=f'{ctx.author.display_name}', value="You earned $5,000", inline=False)
                embed.add_field(name="Wallet",
                                value=f"```cs\n${user.wallet:,d} Gold```", inline=True)
                await ctx.send(embed=embed)
                recent_job.last_worked = datetime.datetime.now()

            else:
                time_remaining = int(60-minutes)
                embed = discord.Embed(title=f'Hourly', color=discord.Color.red())
                embed.add_field(name=f'{ctx.author.display_name}', value=f"{time_remaining} minutes remaining...", inline=False)
                await ctx.send(embed=embed)
    
    session.commit()

@bot.command(name='miner', help='Check your miners earnings.')
async def miner(ctx):
    # Query if User exists
    user = session.query(User).filter_by(name=ctx.author.name).first()

    if not user:
        user = create_user(ctx.author.name)

    miner = session.query(Miner).filter_by(user_id=user.id).first()

    embed = discord.Embed(title=f"{user.name}'s Miner", 
                            color=discord.Color.random())

    # Update the balance of how much the miner collected since this was last checked
    time_delta = datetime.datetime.now() - miner.last_worked
    minutes = round(time_delta.total_seconds() / 60,0)

    # A miner will gaurantee you a reward at the (miner) level equivalent of doing !work 3 times every hour (30 minutes of the 60 minutes)
    miner.balance += int(3 * (10 ** (miner.level + 2)) * (minutes / 60))
    miner.last_worked = datetime.datetime.now()
    session.commit()

    embed.set_thumbnail(url=miner_level_urs[miner.level])
    embed.add_field(name="Level",
                    value=f"```cs\n{str(miner.level)}```", inline=True)
    embed.add_field(name="Collected",
                    value=f"```cs\n${miner.balance:,d} Gold```", inline=True)
    await ctx.send(embed=embed)

@bot.command(name='collect', help='Collect your miners earnings.')
async def collect(ctx):
    # Query if User exists
    user = session.query(User).filter_by(name=ctx.author.name).first()

    if not user:
        await ctx.send('User does not exist.')
        return

    miner = session.query(Miner).filter_by(user_id=user.id).first()

    embed = discord.Embed(title=f"Money Collected!", 
                            color=discord.Color.green())

    # Update the balance of how much the miner collected since this was last checked
    time_delta = datetime.datetime.now() - miner.last_worked
    minutes = round(time_delta.total_seconds() / 60,0)

    # A miner will gaurantee you a reward at the (miner) level equivalent of doing !work 3 times every hour (30 minutes of the 60 minutes)
    amount_to_collect = miner.balance + int(3 * (10 ** (miner.level + 2)) * (minutes / 60))
    user.wallet += amount_to_collect
    miner.balance = 0
    miner.last_worked = datetime.datetime.now()
    session.commit()

    embed.set_thumbnail(url=osrs_gp_url)
    embed.add_field(name="Collected",
                    value=f"```cs\n${amount_to_collect:,d}```", inline=True)
    embed.add_field(name="Wallet",
                    value=f"```cs\n${user.wallet:,d} Gold```", inline=True)
    await ctx.send(embed=embed)

@bot.command(name='buy', help='Buy some stuff.')
async def buy(ctx, item=None):
    user = session.query(User).filter_by(name=ctx.author.name).first()
    
    if not user:
        await ctx.send('User not found.')
    else:
        miner = session.query(Miner).filter_by(user_id=user.id).first()
        if not item:
            level_up_cost = 10 ** (user.level + 4)
            shield_cost = int(1.5 * (10 ** (user.level + 2)))
            miner_upgrade_cost = 2 * 10 ** (miner.level + 4)
            embed = discord.Embed(title=f"{ctx.author.display_name}'s Shop", color=discord.Color.random())
            embed.add_field(name='[ID: 1] Shield', value=f"```cs\n${shield_cost:,d} Gold```", inline=False)
            embed.add_field(name='[ID: 2] Level Up', value=f"```cs\n${level_up_cost:,d} Gold```", inline=False)
            embed.add_field(name='[ID: 3] Miner Upgrade', value=f"```cs\n${miner_upgrade_cost:,d} Gold```", inline=False)
            embed.add_field(name="Wallet",
                            value=f"```cs\n${user.wallet:,d} Gold```", inline=True)
            await ctx.send(embed=embed)

        if item == '1':
            shield_cost = int(1.5 * (10 ** (user.level + 2)))

            if user.wallet < shield_cost:
                await ctx.send('Insufficient Funds to buy a shield.')
            else:
                user.wallet -= shield_cost
                user.shields += 1
                embed = discord.Embed(title=f"{ctx.author.display_name} has bought a shield!", color=discord.Color.random())
                embed.add_field(name="Shields",
                                value=f"```cs\n{str(user.shields)}```", inline=True)
                await ctx.send(embed=embed)

        elif item == '2':
            level_up_cost = 10 ** (user.level + 4)
            if user.wallet < level_up_cost:
                await ctx.send('Insufficient Funds in wallet to level up.')
            else:
                user.wallet -= level_up_cost
                user.level += 1
                embed = discord.Embed(title=f"{ctx.author.display_name} has leveled up!", color=discord.Color.green())
                embed.add_field(name="Level",
                                value=f"```cs\n{str(user.level)}```", inline=True)
                await ctx.send(embed=embed)

        elif item == '3':
            miner_upgrade_cost = 2 * 10 ** (user.level + 4)
            if user.wallet < miner_upgrade_cost:
                await ctx.send('Insufficient Funds in wallet to level up Miner.')
            else:
                user.wallet -= miner_upgrade_cost
                miner.level += 1
                embed = discord.Embed(title=f"{ctx.author.display_name}'s Miner has leveled up!", color=discord.Color.green())
                embed.add_field(name="Miner Level",
                                value=f"```cs\n{str(miner.level)}```", inline=True)
                await ctx.send(embed=embed)
        else:
            await ctx.send('Item not in shop.')

    session.commit()

@bot.command(name='give', help='Give money to a player.')
async def give(ctx, tagged_user, amount):
    user = session.query(User).filter_by(name=ctx.author.name).first()
    
    amount = validate_bet(amount)

    if not amount:
        await ctx.send('Invalid amount to send.')
    
    members = ctx.message.mentions
    if members:
        member_name = members[0].name

    if not members:
        await ctx.send('You must tag someone to send money to them.')

    recipient = session.query(User).filter_by(name=member_name).first()

    if not recipient:
        await ctx.send('User does not exist. They must create an account by typing !bal')
    
    if user.name == 'Koltzan':
        recipient.wallet += amount
        embed = discord.Embed(title=f"Money Sent!", color=discord.Color.green())
        embed.add_field(name=f"{recipient.name}'s' Wallet",
                        value=f"```cs\n${recipient.wallet:,d} Gold```", inline=True)
        embed.add_field(name=f"Your Wallet",
                        value=f"```cs\n${user.wallet:,d} Gold```", inline=True)
        await ctx.send(embed=embed)
        
    elif amount > user.wallet:
        await ctx.send("You don't own that kind of money...")

    else:
        user.wallet -= amount
        recipient.wallet += amount
        embed = discord.Embed(title=f"Money Sent!", color=discord.Color.green())
        embed.add_field(name=f"{recipient.name}'s' Wallet",
                        value=f"```cs\n${recipient.wallet:,d} Gold```", inline=True)
        embed.add_field(name=f"Your Wallet",
                        value=f"```cs\n${user.wallet:,d} Gold```", inline=True)
        await ctx.send(embed=embed)

    session.commit()

@bot.command(name='rob', help='Rob money from a player.')
async def rob(ctx, tagged_user):
    user = session.query(User).filter_by(name=ctx.author.name).first()
    
    members = ctx.message.mentions
    if members:
        member_name = members[0].name

    if not members:
        await ctx.send('You must tag someone to rob them.')
        return

    recipient = session.query(User).filter_by(name=member_name).first()

    if not recipient:
        await ctx.send('User does not exist. They must create an account by typing !bal')
        
    elif user.wallet < 1500:
        await ctx.send("You need at least 1500 Gold to rob someone")

    else:
        recent_robbery = session.query(Rob).filter_by(user_id=user.id).first()
        
        rob_user = False
        if not recent_robbery:
            rob_user = True
            timestamp = Rob(
                user_id = user.id,
                last_worked=datetime.datetime.now()
            )
            session.add(timestamp)
        else:
            time_delta = datetime.datetime.now() - recent_robbery.last_worked
            minutes = round(time_delta.total_seconds() / 60,0)
            if minutes > 20:
                rob_user = True
                recent_robbery.last_worked = datetime.datetime.now()
            else:
                time_remaining = int(20-minutes)
                embed = discord.Embed(title=f'Robbery', color=discord.Color.red())
                embed.add_field(name=f'{ctx.author.display_name}', value=f"{time_remaining} minutes remaining...", inline=False)
                await ctx.send(embed=embed)
        
        if rob_user:
            rob_result = random.randint(1,10)
            if rob_result >= 6:
                if recipient.shields > 0:
                    recipient.shields -= 1
                    user.wallet -= 1500
                    embed = discord.Embed(title=f"{recipient.name} defended the attack!", color=discord.Color.red())
                    embed.add_field(name="Shields Remaining",
                                    value=f"```cs\n{str(recipient.shields)}```", inline=True)
                    await ctx.send(embed=embed)
                else:
                    proportion_to_take = random.uniform(0,1)
                    amount_to_take = int(proportion_to_take * recipient.wallet)
                    user.wallet += amount_to_take
                    recipient.wallet -= amount_to_take

                    embed = discord.Embed(title=f"You Robbed {recipient.name}", color=discord.Color.green())
                    embed.add_field(name=f"Amount Stolen",
                                    value=f"```cs\n${amount_to_take:,d} Gold```", inline=False)
                    embed.add_field(name=f"{recipient.name}'s' Wallet",
                                    value=f"```cs\n${recipient.wallet:,d} Gold```", inline=True)
                    embed.add_field(name=f"Your Wallet",
                                    value=f"```cs\n${user.wallet:,d} Gold```", inline=True)
                    await ctx.send(embed=embed)

            elif rob_result >= 3:
                user.wallet -= 1500
                embed = discord.Embed(title=f"{recipient.name} got away!", color=discord.Color.red())
                embed.add_field(name=f"Amount Stolen",
                                value=f"```cs\n${0} Gold```", inline=False)
                await ctx.send(embed=embed)

            else:
                proportion_to_give = random.uniform(0,0.5)
                amount_to_give = max(int(proportion_to_give * user.wallet), int(0.1 * user.bank))
                
                if amount_to_give > user.wallet:
                    user.bank -= amount_to_give
                else:
                    user.wallet -= amount_to_give

                recipient.wallet += amount_to_give

                embed = discord.Embed(title=f"You lost the fight and {recipient.name} Robbed you back!", color=discord.Color.red())
                embed.add_field(name=f"Amount Lost",
                                value=f"```cs\n${amount_to_give:,d} Gold```", inline=False)
                embed.add_field(name=f"{recipient.name}'s' Wallet",
                                value=f"```cs\n${recipient.wallet:,d} Gold```", inline=True)
                embed.add_field(name=f"Your Wallet",
                                value=f"```cs\n${user.wallet:,d} Gold```", inline=True)
                await ctx.send(embed=embed)

    session.commit()

@bot.command(name='deposit', help='Deposit money to your bank.')
async def deposit(ctx, amount):
    user = session.query(User).filter_by(name=ctx.author.name).first()

    if amount == 'all':
        user.bank += user.wallet
        user.wallet = 0

        embed = discord.Embed(title=f"Deposited Complete!", color=discord.Color.green())
        embed.set_thumbnail(url=ctx.author.avatar_url)
        embed.add_field(name="Level",
                        value=f"```cs\n{str(user.level)}```", inline=True)
        embed.add_field(name="Wallet",
                        value=f"```cs\n${user.wallet:,d} Gold```", inline=True)
        embed.add_field(name="Bank",
                        value=f"```cs\n${user.bank:,d} Gold```", inline=True)
        await ctx.send(embed=embed)

    else:
        amount = validate_bet(amount)
                
        if not amount:
            await ctx.send('Invalid amount to deposit.')
        
        if amount > user.wallet:
            await ctx.send("You don't own that kind of money...")

        else:
            user.wallet -= amount
            user.bank += amount
            embed = discord.Embed(title=f"Deposited Complete!", color=discord.Color.green())
            embed.set_thumbnail(url=ctx.author.avatar_url)
            embed.add_field(name="Level",
                            value=f"```cs\n{str(user.level)}```", inline=True)
            embed.add_field(name="Wallet",
                            value=f"```cs\n${user.wallet:,d} Gold```", inline=True)
            embed.add_field(name="Bank",
                            value=f"```cs\n${user.bank:,d} Gold```", inline=True)
            await ctx.send(embed=embed)

    session.commit()

@bot.command(name='withdraw', help='Withdraw money to your bank.')
async def withdraw(ctx, amount):
    user = session.query(User).filter_by(name=ctx.author.name).first()
    
    if amount == 'all':
        user.wallet += user.bank
        user.bank = 0

        embed = discord.Embed(title=f"Withdraw Complete!", color=discord.Color.green())
        embed.set_thumbnail(url=ctx.author.avatar_url)
        embed.add_field(name="Level",
                        value=f"```cs\n{str(user.level)}```", inline=True)
        embed.add_field(name="Wallet",
                        value=f"```cs\n${user.wallet:,d} Gold```", inline=True)
        embed.add_field(name="Bank",
                        value=f"```cs\n${user.bank:,d} Gold```", inline=True)
        await ctx.send(embed=embed)
    
    else:
        amount = validate_bet(amount)
                
        if not amount:
            await ctx.send('Invalid amount to deposit.')

        elif amount > user.bank:
            await ctx.send("You don't own that kind of money...")

        else:
            user.bank -= amount
            user.wallet += amount
            embed = discord.Embed(title=f"Withdraw Complete!", color=discord.Color.green())
            embed.set_thumbnail(url=ctx.author.avatar_url)
            embed.add_field(name="Level",
                            value=f"```cs\n{str(user.level)}```", inline=True)
            embed.add_field(name="Wallet",
                            value=f"```cs\n${user.wallet:,d} Gold```", inline=True)
            embed.add_field(name="Bank",
                            value=f"```cs\n${user.bank:,d} Gold```", inline=True)
            await ctx.send(embed=embed)

        session.commit()

@bot.command(name='cmd', help='Bot Commands.')
async def commands(ctx):
    embed = discord.Embed(title=f"Bot Commands", color=discord.Color.green())
    embed.add_field(name="bal", value="Check your balance or create your account.", inline=False)
    embed.add_field(name="buy", value="Buy some stuff. Format: .buy ItemId", inline=False)
    embed.add_field(name="flip", value="Play a coin toss to double your money. Format: .flip Amount.", inline=False)
    embed.add_field(name="rps", value="Play Rock Paper Scissors. Format: .rps Amount r/p/s", inline=False)
    embed.add_field(name="dice", value="Play Dice. Format: .dice Amount 1-6", inline=False)
    embed.add_field(name="roll", value="Roll against the bot (1 to 100). Winner takes all!", inline=False)
    embed.add_field(name="give", value="Give money to a player. Format: .give @Player Amount.", inline=False)
    embed.add_field(name="rob", value="Rob the shit out of a player. Format: .rob @Player", inline=False)
    embed.add_field(name="work", value="Work for some money. Level up to get more money.", inline=False)
    embed.add_field(name="hourly", value="Make $5000 every hour.", inline=False)
    embed.add_field(name="miner", value="Check the status of your miner.", inline=False)
    embed.add_field(name="collect", value="Collect money from your miner.", inline=False)
    await ctx.send(embed=embed)

# Helper Functions

def validate_bet(bet):
    bet = bet.replace('k', '000').replace('K','000').replace('m','000000').replace('M','000000')

    if bet.isnumeric():
        bet = int(bet)
        if bet <= 0:
            return False
        
        return int(bet)

def create_user(name):
    # If user doesn't exist - create a new user
    user = User(
        name=name,
        level=1,
        wallet=1000,
        bank=0,
        shields=0
    )
    session.add(user)
    session.commit()

    miner = Miner(
        user_id=user.id,
        level=1,
        balance=0,
        last_worked=datetime.datetime.now()
    )
    session.add(miner)
    session.commit()

    return user

rps_moves = {
    0: 'Rock',
    1: 'Paper',
    2: 'Scissors'
}

miner_level_urs = {
    1: 'https://i.pinimg.com/originals/75/61/5a/75615a37309f44c6f07353277429a4f2.png',
    2: 'https://static.wikia.nocookie.net/leagueoflegends/images/9/96/Season_2019_-_Gold_1.png/revision/latest/scale-to-width-down/250?cb=20181229234920',
    3: 'https://static.wikia.nocookie.net/leagueoflegends/images/7/74/Season_2019_-_Platinum_1.png/revision/latest/scale-to-width-down/250?cb=20181229234932',
    4: 'https://i.pinimg.com/originals/6a/10/c7/6a10c7e84c9f4e4aa9412582d28f3fd2.png',
    5: 'https://i.pinimg.com/originals/69/61/ab/6961ab1af799f02df28fa74278d78120.png',
}

osrs_gp_url = 'https://oldschool.runescape.wiki/images/Coins_detail.png?404bc'

bot.run(TOKEN)