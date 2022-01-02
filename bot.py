# bot.py
import os
import random
import datetime

import discord
from discord.ext import commands
from dotenv import load_dotenv

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from database import Hourly, Timestamp, User

# Load Discord Bot
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
bot = commands.Bot(command_prefix='!')

# Load Database
engine = create_engine('sqlite:///gamble.db', echo=True)
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
            embed.add_field(name="Your move", value=f"```{rps}```", inline=True)
            embed.add_field(name="Bot's Move", value=f"```{bot_move}```", inline=True)
            embed.add_field(name="Wallet",
                            value=f"```cs\n${user.wallet:,d} Gold```", inline=False)
            await ctx.send(embed=embed)

        elif win:
            user.wallet += bet
            embed = discord.Embed(title='Rock Paper Scissors', color=discord.Color.green())
            embed.add_field(name=f'{ctx.author.display_name}', value="You Won ^.^! :thumbsup:", inline=False)
            embed.add_field(name="Your move", value=f"```{rps}```", inline=True)
            embed.add_field(name="Bot's Move", value=f"```{bot_move}```", inline=True)
            embed.add_field(name="Wallet",
                            value=f"```cs\n${user.wallet:,d} Gold```", inline=False)
            
            await ctx.send(embed=embed)
        else:
            user.wallet -= bet
            embed = discord.Embed(title='Rock Paper Scissors', color=discord.Color.red())
            embed.add_field(name=f'{ctx.author.display_name}', value="RIP You Lost X_X! :thumbsdown:", inline=False)
            embed.add_field(name="Your move", value=f"```{rps}```", inline=True)
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

@bot.command(name='buy', help='Buy some stuff.')
async def buy(ctx, item=None):
    user = session.query(User).filter_by(name=ctx.author.name).first()
    
    if not user:
        await ctx.send('User not found.')
    else:
        if not item:
            level_up_cost = 10 ** (user.level + 4)
            embed = discord.Embed(title=f"{ctx.author.display_name}'s Shop", color=discord.Color.random())
            embed.add_field(name='[ID: 1] Level Up', value=f"```cs\n${level_up_cost:,d} Gold```", inline=False)
            embed.add_field(name="Wallet",
                            value=f"```cs\n${user.wallet:,d} Gold```", inline=True)
            await ctx.send(embed=embed)

        elif item == '1':
            level_up_cost = 10 ** (user.level + 4)
            if user.wallet < level_up_cost:
                await ctx.send('Insufficient Funds in Wallet to level up.')
            else:
                user.wallet -= level_up_cost
                user.level += 1
                embed = discord.Embed(title=f"{ctx.author.display_name} has leveled up!", color=discord.Color.random())
                embed.add_field(name="Level",
                                value=f"```cs\n{str(user.level)}```", inline=True)
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

@bot.command(name='cmd', help='Bot Commands.')
async def commands(ctx):
    embed = discord.Embed(title=f"Bot Commands", color=discord.Color.green())
    embed.add_field(name="bal", value="Check your balance or create your account.", inline=False)
    embed.add_field(name="buy", value="Buy some stuff. Format: !buy ItemId", inline=False)
    embed.add_field(name="flip", value="Do a 50-50 to double your money. Format: !flip Amount.", inline=False)
    embed.add_field(name="rps", value="Play Rock Paper Scissors. Format: !rps Amount r/p/s", inline=False)
    embed.add_field(name="give", value="Give money to a player. Format: !give @Player Amount.", inline=False)
    embed.add_field(name="work", value="Work for some money. Level up to get more money.", inline=False)
    embed.add_field(name="hourly", value="Make $5000 every hour.", inline=False)
    await ctx.send(embed=embed)

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
        investments=0
    )
    session.add(user)
    session.commit()
    
    return user

rps_moves = {
    0: 'Rock',
    1: 'Paper',
    2: 'Scissors'
}

bot.run(TOKEN)