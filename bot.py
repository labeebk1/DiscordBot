# bot.py
import asyncio
import os
import random
import datetime

import discord
from discord.ext import commands
from dotenv import load_dotenv

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func

from models import Casino, Miner, User, Ticket, Profession
from card import Card

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

@bot.command(name='bal', aliases=["b"], help='Check your balance or create your account.')
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

    casino = session.query(Casino).filter_by(user_id=user.id).first()
    if not casino:
        casino = create_casino(user)
    
    if not user.casino:
        user.casino = casino.id
    casino_guests = session.query(User).filter_by(casino=casino.id).count()

    if user:
        # Mechanic Earnings
        professions = session.query(Profession).filter_by(user_id=user.id, profession_id=3).all()
        crafter = False
        if professions:
            crafter = True

        if user.diamond == True:
            embed = discord.Embed(title=f"King {user.name} :diamond_shape_with_a_dot_inside:", 
                        color=discord.Color.random())
        elif crafter:
            embed = discord.Embed(title=f"Jewel Crafter {user.name} :diamond_shape_with_a_dot_inside:", 
                        color=discord.Color.random())
        else:            
            embed = discord.Embed(title=f"{user.name}'s Bank", 
                        color=discord.Color.random())

        # Mechanic Earnings
        professions = session.query(Profession).filter_by(user_id=user.id, profession_id=2).all()
        mechanic = False
        if professions:
            mechanic = True

        if mechanic:        
            miner = session.query(Miner).filter_by(user_id=user.id).first()

            # Update the balance of how much the miner collected since this was last checked
            time_delta = datetime.datetime.now() - miner.last_worked
            minutes = round(time_delta.total_seconds() / 60,0)

            # A miner will gaurantee you a reward at the (miner) level equivalent of doing !work 3 times every hour (30 minutes of the 60 minutes)
            miner.balance += int(3 * (10 ** (miner.level + 2)) * (minutes / 60))
            miner.last_worked = datetime.datetime.now()

            earnings = int(3 * (10 ** (miner.level + 2)) * (minutes / 60))
            user.wallet += earnings

            session.commit()

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

        professions = session.query(Profession).filter_by(user_id=user.id).all()

        if professions:
            badges = ', '.join([profession_badges[profession.profession_id] for profession in professions])
            embed.add_field(name="Professions",
                            value=f"{badges}", inline=False)

        embed.set_footer(text=f"{user.shields} Active Shields, {casino_guests} Casino Guests", icon_url = "https://thumbs.dreamstime.com/b/well-organized-fully-editable-antivirus-protection-security-icon-any-use-like-print-media-web-commercial-use-any-kind-158454387.jpg")

        await ctx.send(embed=embed)
    else:
        await ctx.send('User not found.')

@bot.command(name='stats', help='Check your stats.')
async def stats(ctx):
    
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

    casino = session.query(Casino).filter_by(user_id=user.id).first()
    if not casino:
        casino = create_casino(user)

    miner = session.query(Miner).filter_by(user_id=user.id).first()
    
    if not user.casino:
        user.casino = casino.id

    if user:
        embed = discord.Embed(title=f"{user.name}'s Profile", color=discord.Color.random())

        if members:
            embed.set_thumbnail(url=member.avatar_url)
        else:
            embed.set_thumbnail(url=ctx.author.avatar_url)

        embed.add_field(name="User Level",
                        value=f"```cs\n{str(user.level)}```", inline=True)
        embed.add_field(name="Miner Level",
                        value=f"```cs\n{miner.level:,d}```", inline=True)
        embed.add_field(name="Casino Level",
                        value=f"```cs\n{casino.level:,d}```", inline=True)

        embed.set_footer(text=f"{user.shields} Active Shields", icon_url = "https://thumbs.dreamstime.com/b/well-organized-fully-editable-antivirus-protection-security-icon-any-use-like-print-media-web-commercial-use-any-kind-158454387.jpg")

        await ctx.send(embed=embed)
    else:
        await ctx.send('User not found.')

@bot.command(name='flip', aliases=["f"], help='Do a 50-50 to double your money.')
async def flip(ctx, bet: str):
    # Query if User exists
    user = session.query(User).filter_by(name=ctx.author.name).first()

    if not user:
        user = create_user(ctx.author.name)

    check_casino(user)

    bet = validate_bet(bet)

    if not bet:
        await ctx.send("Invalid bet. Format's Available: 1, 1k, 1K, 1m, 1M")
    
    elif bet > user.wallet:
        await ctx.send('Insufficient Funds.')
    
    else:

        # Roll for the change at a ticket
        if bet > int(2 * 10**(user.level+2)):
            embed = roll_ticket(user)
            if embed:
                await ctx.send(embed=embed)

        if random.randint(0,1):
            
            casino = session.query(Casino).filter_by(id=user.casino).first()
            casino_owner = session.query(User).filter_by(id=casino.user_id).first()
            tax_rate = get_tax(casino.level)
            tax_owing = int(tax_rate * bet)

            user.wallet += (bet - tax_owing)
            casino.balance += tax_owing

            embed = discord.Embed(title='Coin Flip', color=discord.Color.green())

            embed.add_field(name=f'{ctx.author.display_name}', value="You Won ^.^! :thumbsup:", inline=False)
            embed.add_field(name=f"Taxes Paid to {casino_owner.name}",
                            value=f"```cs\n${tax_owing:,d} Gold```", inline=False)
            embed.add_field(name="Wallet",
                            value=f"```cs\n${user.wallet:,d} Gold```", inline=False)
            
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

    check_casino(user)

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

        # Roll for the change at a ticket
        if bet > int(2 * 10**(user.level+2)):
            embed = roll_ticket(user)
            if embed:
                await ctx.send(embed=embed)

        bot_bet = random.randint(1,6)
        win = False
        if bot_bet == dice_bet:
            win = True

        if win:

            casino = session.query(Casino).filter_by(id=user.casino).first()
            casino_owner = session.query(User).filter_by(id=casino.user_id).first()
            tax_rate = get_tax(casino.level)
            tax_owing = int(tax_rate * 5*bet)

            user.wallet += (5*bet - tax_owing)
            casino.balance += tax_owing

            embed = discord.Embed(title='Dice', color=discord.Color.green())
            embed.add_field(name=f'{ctx.author.display_name}', value="Holy shit You Won ^.^! :thumbsup:", inline=False)
            embed.add_field(name="Winnings",
                            value=f"```cs\n${(5*bet - tax_owing):,d} Gold```", inline=False)
            embed.add_field(name=f"Taxes Paid to {casino_owner.name}",
                            value=f"```cs\n${tax_owing:,d} Gold```", inline=False)
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

@bot.command(name='roulette', help='Roulette the bot.')
async def roulette(ctx, bet: str, color: str):
    # Query if User exists
    user = session.query(User).filter_by(name=ctx.author.name).first()

    if not user:
        user = create_user(ctx.author.name)

    check_casino(user)

    bet = validate_bet(bet)

    if not bet:
        await ctx.send("Invalid bet. Format's Available: 1, 1k, 1K, 1m, 1M")
        return

    if not color in ['red', 'r', 'green', 'g', 'black' ,'b']:
        await ctx.send("Invalid color selection. Please choose between red, r, green, g, black, b")
        return
    
    if color in ['g', 'green']:
        color = ':green_circle:'
    
    if color in ['r', 'red']:
        color = ':red_circle:'

    if color in ['b', 'black']:
        color = ':black_circle:'

    if bet > user.wallet:
        await ctx.send('Insufficient Funds.')
    else:
        
        # Roll for the change at a ticket
        if bet > int(2 * 10**(user.level+2)):
            embed = roll_ticket(user)
            if embed:
                await ctx.send(embed=embed)

        number = random.randint(0,36)
        big_win = False
        win = False
        table_color = ''
        if number == 0:
            table_color = ':green_circle:'
        elif number % 2 == 0:
            table_color = ':black_circle:'
        else:
            table_color = ':red_circle:'

        if table_color == color and table_color == ':green_circle:':
            big_win = True
        
        if table_color == color:
            win = True

        if big_win:

            casino = session.query(Casino).filter_by(id=user.casino).first()
            casino_owner = session.query(User).filter_by(id=casino.user_id).first()
            tax_rate = get_tax(casino.level)
            tax_owing = int(tax_rate * 36*bet)

            user.wallet += (35*bet - tax_owing)
            casino.balance += tax_owing

            embed = discord.Embed(title='Roulette BIG WIN', color=discord.Color.green())
            embed.add_field(name=f'{ctx.author.display_name}', value="Holy shit You Won the major Prize!! ^.^! :thumbsup:", inline=False)
            embed.add_field(name="Roulette Table", value=f"{number} :green_circle:", inline=True)
            embed.add_field(name="Earning",
                            value=f"```cs\n${int(35*bet - tax_owing):,d} Gold```", inline=False)
            embed.add_field(name=f"Taxes Paid to {casino_owner.name}",
                            value=f"```cs\n${tax_owing:,d} Gold```", inline=False)
            embed.add_field(name="Wallet",
                            value=f"```cs\n${user.wallet:,d} Gold```", inline=False)
            embed.set_thumbnail(url='https://previews.123rf.com/images/hobbitfoot/hobbitfoot1709/hobbitfoot170900484/85929770-big-win-roulette-signboard-game-banner-design-.jpg')
            await ctx.send(embed=embed)
        elif win:
            casino = session.query(Casino).filter_by(id=user.casino).first()
            casino_owner = session.query(User).filter_by(id=casino.user_id).first()
            tax_rate = get_tax(casino.level)
            tax_owing = int(tax_rate * bet)

            user.wallet += (bet - tax_owing)
            casino.balance += tax_owing

            embed = discord.Embed(title='Roulette Win!', color=discord.Color.green())
            embed.add_field(name=f'{ctx.author.display_name}', value="You win! :thumbsup:", inline=False)
            embed.add_field(name="Roulette Table", value=f"{number} {table_color}", inline=True)
            embed.add_field(name="Earning",
                            value=f"```cs\n${bet:,d} Gold```", inline=False)
            embed.add_field(name=f"Taxes Paid to {casino_owner.name}",
                            value=f"```cs\n${tax_owing:,d} Gold```", inline=False)
            embed.add_field(name="Wallet",
                            value=f"```cs\n${user.wallet:,d} Gold```", inline=False)
            await ctx.send(embed=embed)
        else:
            user.wallet -= bet
            embed = discord.Embed(title='Roulette Loss!', color=discord.Color.red())
            embed.add_field(name=f'{ctx.author.display_name}', value="RIP You Lost X_X! :thumbsdown:", inline=False)
            embed.add_field(name="Roulette Table", value=f"{number} {table_color}", inline=True)
            embed.add_field(name="Wallet",
                            value=f"```cs\n${user.wallet:,d} Gold```", inline=False)
            await ctx.send(embed=embed)

    session.commit()

def get_hand_value(hand):
    # rankings: 
    # 0 = Nothing, 
    # 1 = 2 of a kind, 
    # 2 = 2 pair
    # 3 = 3 of a kind, 
    # 4 = Full house, 
    # 5 = 4 of a kind, 
    # 6 = 5 of a kind
    counts = dict()
    for i in hand:
        counts[i] = counts.get(i, 0) + 1

    hand_vals = list(counts.values())
    if max(hand_vals) == 1:
        return 0, 'Nothing'
    # Full house
    elif 3 in hand_vals and 2 in hand_vals:
        return 4, 'Full House!'
    # 5 of a kind
    elif len(hand_vals) == 1:
        return 6, '5 of a Kind!!'
    elif max(hand_vals) == 4:
        return 5, '4 of a Kind!'
    elif max(hand_vals) == 3:
        return 3, '3 of a Kind!'

    pairs = hand_vals.count(2)
    if pairs == 2:
        return 2, '2 Pair!'
    else:
        return 1, 'Pair!'

@bot.command(name='flowerpoker', aliases=["fp"], help='Challenge a player or the host to a game of flower poker.')
async def flowerpoker(ctx, target_player, bet=None):
    # Query if User exists
    user = session.query(User).filter_by(name=ctx.author.name).first()

    members = ctx.message.mentions
    if members:
        member = members[0]
        member_name = members[0].name

    if members:
        challenge_player = session.query(User).filter_by(name=member_name).first()
        if not challenge_player:
            await ctx.send("User does not exist.")
            return

    if not user:
        await ctx.send("User does not exist.")
        return

    if not bet:
        bet = target_player
    bet_str = bet
    bet = validate_bet(bet)

    if not bet:
        await ctx.send("Invalid bet. Format's Available: 1, 1k, 1K, 1m, 1M")
        return

    if user.wallet < bet:
        await ctx.send("Insufficient funds to make this challenge.")

    elif members and challenge_player.wallet < bet:
        await ctx.send(f"{challenge_player.name} is broke af.")

    else:
        if members:
            embed = discord.Embed(title=f'Challenging {challenge_player.name} to Flower Poker', color=discord.Color.random())
            embed.add_field(name=f'{ctx.author.display_name} has challenged you to a game of flower poker for ${bet_str} Gold.', value="Type 'yes' or 'y' to accept.", inline=False)
            embed.set_thumbnail(url='https://oldschool.runescape.wiki/images/thumb/Assorted_flowers_detail.png/1024px-Assorted_flowers_detail.png?14110')
            message = await ctx.send(embed=embed)

            reply = await bot.wait_for(event="message", check=author_check(member), timeout=30.0)
            
            if reply.content in ['yes', 'y', 'Y']:
                
                user.wallet -= bet
                challenge_player.wallet -= bet
                session.commit()
                
                player_hand = random.choices(flowers, k=5)
                challenger_hand = random.choices(flowers, k=5)

                player_hand_display = ' '.join(player_hand)
                challenger_hand_display = ' '.join(challenger_hand)

                player_hand_value, player_hand_str = get_hand_value(player_hand)
                challenger_hand_value, challenger_hand_str = get_hand_value(challenger_hand)

                if player_hand_value > challenger_hand_value:
                    # Player Won
                    user.wallet += 2*bet
                    
                    player_slow_display = [player_hand.pop()]
                    challenger_slow_display = [challenger_hand.pop()]
                    player_hand_display = ' '.join(player_slow_display)
                    challenger_hand_display = ' '.join(challenger_slow_display)

                    embed = discord.Embed(title='Flower Poker!', color=discord.Color.random())
                    embed.add_field(name=f"{user.name}", value=player_hand_display, inline=False)
                    embed.add_field(name=f"{challenge_player.name}", value=challenger_hand_display, inline=False)
                    message = await ctx.send(embed=embed)
                    await asyncio.sleep(1)

                    while len(player_hand):
                        player_slow_display.append(player_hand.pop())
                        challenger_slow_display.append(challenger_hand.pop())
                        player_hand_display = ' '.join(player_slow_display)
                        challenger_hand_display = ' '.join(challenger_slow_display)

                        new_embed = discord.Embed(title='Flower Poker!', color=discord.Color.random())
                        new_embed.add_field(name=f"{user.name}", value=player_hand_display, inline=False)
                        new_embed.add_field(name=f"{challenge_player.name}", value=challenger_hand_display, inline=False)
                        await message.edit(embed=new_embed)
                        await asyncio.sleep(1)

                    new_embed = discord.Embed(title=f'Flower Poker - {user.name} Won!', color=discord.Color.random())
                    new_embed.add_field(name=f"{user.name} :crown:", value=player_hand_display, inline=False)
                    new_embed.add_field(name=f"{challenge_player.name}", value=challenger_hand_display, inline=False)
                    new_embed.add_field(name=f"{user.name} Hand", value=f"```{player_hand_str}```", inline=True)
                    new_embed.add_field(name=f"{challenge_player.name}'s Hand", value=f"```{challenger_hand_str}```", inline=True)
                    new_embed.add_field(name=f"{user.name} Wallet",
                                    value=f"```cs\n${user.wallet:,d} Gold```", inline=False)
                    new_embed.add_field(name=f"{challenge_player.name} Wallet",
                                    value=f"```cs\n${challenge_player.wallet:,d} Gold```", inline=False)
                    new_embed.set_thumbnail(url='https://oldschool.runescape.wiki/images/Mounted_coins_built.png?c6984')
                    await message.edit(embed=new_embed)

                elif challenger_hand_value > player_hand_value:
                    # Receipient won
                    challenge_player.wallet += 2*bet

                    player_slow_display = [player_hand.pop()]
                    challenger_slow_display = [challenger_hand.pop()]
                    player_hand_display = ' '.join(player_slow_display)
                    challenger_hand_display = ' '.join(challenger_slow_display)

                    embed = discord.Embed(title='Flower Poker!', color=discord.Color.random())
                    embed.add_field(name=f"{user.name}", value=player_hand_display, inline=False)
                    embed.add_field(name=f"{challenge_player.name}", value=challenger_hand_display, inline=False)
                    message = await ctx.send(embed=embed)
                    await asyncio.sleep(1)

                    while len(player_hand):
                        player_slow_display.append(player_hand.pop())
                        challenger_slow_display.append(challenger_hand.pop())
                        player_hand_display = ' '.join(player_slow_display)
                        challenger_hand_display = ' '.join(challenger_slow_display)

                        new_embed = discord.Embed(title='Flower Poker!', color=discord.Color.random())
                        new_embed.add_field(name=f"{user.name}", value=player_hand_display, inline=False)
                        new_embed.add_field(name=f"{challenge_player.name}", value=challenger_hand_display, inline=False)
                        await message.edit(embed=new_embed)
                        await asyncio.sleep(1)

                    new_embed = discord.Embed(title=f'Flower Poker - {challenge_player.name} Won!', color=discord.Color.random())
                    new_embed.add_field(name=f"{user.name}", value=player_hand_display, inline=False)
                    new_embed.add_field(name=f"{challenge_player.name} :crown:", value=challenger_hand_display, inline=False)
                    new_embed.add_field(name=f"{user.name} Hand", value=f"```{player_hand_str}```", inline=True)
                    new_embed.add_field(name=f"{challenge_player.name}'s Hand", value=f"```{challenger_hand_str}```", inline=True)
                    new_embed.add_field(name=f"{user.name} Wallet",
                                    value=f"```cs\n${user.wallet:,d} Gold```", inline=False)
                    new_embed.add_field(name=f"{challenge_player.name} Wallet",
                                    value=f"```cs\n${challenge_player.wallet:,d} Gold```", inline=False)
                    new_embed.set_thumbnail(url='https://oldschool.runescape.wiki/images/Mounted_coins_built.png?c6984')
                    await message.edit(embed=new_embed)

                else:
                    # Draw
                    user.wallet += bet
                    challenge_player.wallet += bet
                    player_slow_display = [player_hand.pop()]
                    challenger_slow_display = [challenger_hand.pop()]
                    player_hand_display = ' '.join(player_slow_display)
                    challenger_hand_display = ' '.join(challenger_slow_display)

                    embed = discord.Embed(title='Flower Poker!', color=discord.Color.random())
                    embed.add_field(name=f"{user.name}", value=player_hand_display, inline=False)
                    embed.add_field(name=f"{challenge_player.name}", value=challenger_hand_display, inline=False)
                    message = await ctx.send(embed=embed)
                    await asyncio.sleep(1)

                    while len(player_hand):
                        player_slow_display.append(player_hand.pop())
                        challenger_slow_display.append(challenger_hand.pop())
                        player_hand_display = ' '.join(player_slow_display)
                        challenger_hand_display = ' '.join(challenger_slow_display)

                        new_embed = discord.Embed(title='Flower Poker!', color=discord.Color.random())
                        new_embed.add_field(name=f"{user.name}", value=player_hand_display, inline=False)
                        new_embed.add_field(name=f"{challenge_player.name}", value=challenger_hand_display, inline=False)
                        await message.edit(embed=new_embed)
                        await asyncio.sleep(1)

                    new_embed = discord.Embed(title='Flower Poker - Draw!', color=discord.Color.random())
                    new_embed.add_field(name=f"{user.name}", value=player_hand_display, inline=False)
                    new_embed.add_field(name=f"{challenge_player.name}", value=challenger_hand_display, inline=False)
                    new_embed.add_field(name=f"{user.name} Hand", value=f"```{player_hand_str}```", inline=True)
                    new_embed.add_field(name=f"{challenge_player.name}'s Hand", value=f"```{challenger_hand_str}```", inline=True)
                    new_embed.add_field(name=f"{user.name} Wallet",
                                    value=f"```cs\n${user.wallet:,d} Gold```", inline=False)
                    new_embed.add_field(name=f"{challenge_player.name} Wallet",
                                    value=f"```cs\n${challenge_player.wallet:,d} Gold```", inline=False)
                    new_embed.set_thumbnail(url='https://oldschool.runescape.wiki/images/Mounted_coins_built.png?c6984')
                    await message.edit(embed=new_embed)
            else:
                await ctx.send(f"{challenge_player.name} rejected the request.")
        else:
            player_hand = random.choices(flowers, k=5)
            challenger_hand = random.choices(flowers, k=5)

            player_hand_value, player_hand_str = get_hand_value(player_hand)
            challenger_hand_value, challenger_hand_str = get_hand_value(challenger_hand)

            if player_hand_value > challenger_hand_value:
                # Player Won
                user.wallet += bet
                
                player_slow_display = [player_hand.pop()]
                challenger_slow_display = [challenger_hand.pop()]
                player_hand_display = ' '.join(player_slow_display)
                challenger_hand_display = ' '.join(challenger_slow_display)

                embed = discord.Embed(title='Flower Poker!', color=discord.Color.random())
                embed.add_field(name=f"{user.name}", value=player_hand_display, inline=False)
                embed.add_field(name=f"Bot", value=challenger_hand_display, inline=False)
                message = await ctx.send(embed=embed)
                await asyncio.sleep(1)

                while len(player_hand):
                    player_slow_display.append(player_hand.pop())
                    challenger_slow_display.append(challenger_hand.pop())
                    player_hand_display = ' '.join(player_slow_display)
                    challenger_hand_display = ' '.join(challenger_slow_display)

                    new_embed = discord.Embed(title='Flower Poker!', color=discord.Color.random())
                    new_embed.add_field(name=f"{user.name}", value=player_hand_display, inline=False)
                    new_embed.add_field(name=f"Bot", value=challenger_hand_display, inline=False)
                    await message.edit(embed=new_embed)
                    await asyncio.sleep(1)

                new_embed = discord.Embed(title='Flower Poker - You Win!', color=discord.Color.green())
                new_embed.add_field(name=f"{user.name} :crown:", value=player_hand_display, inline=False)
                new_embed.add_field(name=f"Bot", value=challenger_hand_display, inline=False)
                new_embed.add_field(name=f"{user.name} Hand", value=f"```{player_hand_str}```", inline=True)
                new_embed.add_field(name=f"Bot's Hand", value=f"```{challenger_hand_str}```", inline=True)
                new_embed.add_field(name=f"{user.name} Wallet",
                                value=f"```cs\n${user.wallet:,d} Gold```", inline=False)
                new_embed.set_thumbnail(url='https://oldschool.runescape.wiki/images/Mounted_coins_built.png?c6984')
                await message.edit(embed=new_embed)

            elif challenger_hand_value > player_hand_value:
                user.wallet -= bet
                # Bot won
                player_slow_display = [player_hand.pop()]
                challenger_slow_display = [challenger_hand.pop()]
                player_hand_display = ' '.join(player_slow_display)
                challenger_hand_display = ' '.join(challenger_slow_display)

                embed = discord.Embed(title='Flower Poker!', color=discord.Color.random())
                embed.add_field(name=f"{user.name}", value=player_hand_display, inline=False)
                embed.add_field(name=f"Bot", value=challenger_hand_display, inline=False)
                message = await ctx.send(embed=embed)
                await asyncio.sleep(1)

                while len(player_hand):
                    player_slow_display.append(player_hand.pop())
                    challenger_slow_display.append(challenger_hand.pop())
                    player_hand_display = ' '.join(player_slow_display)
                    challenger_hand_display = ' '.join(challenger_slow_display)

                    new_embed = discord.Embed(title='Flower Poker!', color=discord.Color.random())
                    new_embed.add_field(name=f"{user.name}", value=player_hand_display, inline=False)
                    new_embed.add_field(name=f"Bot", value=challenger_hand_display, inline=False)
                    await message.edit(embed=new_embed)
                    await asyncio.sleep(1)

                new_embed = discord.Embed(title='Flower Poker - You Lose!', color=discord.Color.red())
                new_embed.add_field(name=f"{user.name}", value=player_hand_display, inline=False)
                new_embed.add_field(name=f"Bot :crown:", value=challenger_hand_display, inline=False)
                new_embed.add_field(name=f"{user.name} Hand", value=f"```{player_hand_str}```", inline=True)
                new_embed.add_field(name=f"Bot's Hand", value=f"```{challenger_hand_str}```", inline=True)
                new_embed.add_field(name=f"{user.name} Wallet",
                                value=f"```cs\n${user.wallet:,d} Gold```", inline=False)
                new_embed.set_thumbnail(url='https://oldschool.runescape.wiki/images/Mounted_coins_built.png?c6984')
                await message.edit(embed=new_embed)

            else:
                # Draw
                player_slow_display = [player_hand.pop()]
                challenger_slow_display = [challenger_hand.pop()]
                player_hand_display = ' '.join(player_slow_display)
                challenger_hand_display = ' '.join(challenger_slow_display)

                embed = discord.Embed(title='Flower Poker!', color=discord.Color.random())
                embed.add_field(name=f"{user.name}", value=player_hand_display, inline=False)
                embed.add_field(name=f"Bot", value=challenger_hand_display, inline=False)
                message = await ctx.send(embed=embed)
                await asyncio.sleep(1)

                while len(player_hand):
                    player_slow_display.append(player_hand.pop())
                    challenger_slow_display.append(challenger_hand.pop())
                    player_hand_display = ' '.join(player_slow_display)
                    challenger_hand_display = ' '.join(challenger_slow_display)

                    new_embed = discord.Embed(title='Flower Poker!', color=discord.Color.random())
                    new_embed.add_field(name=f"{user.name}", value=player_hand_display, inline=False)
                    new_embed.add_field(name=f"Bot", value=challenger_hand_display, inline=False)
                    await message.edit(embed=new_embed)
                    await asyncio.sleep(1)

                new_embed = discord.Embed(title='Flower Poker - Draw!', color=discord.Color.random())
                new_embed.add_field(name=f"{user.name}", value=player_hand_display, inline=False)
                new_embed.add_field(name=f"Bot", value=challenger_hand_display, inline=False)
                new_embed.add_field(name=f"{user.name} Hand", value=f"```{player_hand_str}```", inline=True)
                new_embed.add_field(name=f"Bot's Hand", value=f"```{challenger_hand_str}```", inline=True)
                new_embed.add_field(name=f"{user.name} Wallet",
                                value=f"```cs\n${user.wallet:,d} Gold```", inline=False)
                new_embed.set_thumbnail(url='https://oldschool.runescape.wiki/images/Mounted_coins_built.png?c6984')
                await message.edit(embed=new_embed)

    session.commit()

@bot.command(name='challenge', aliases=["ch"], help='Challenge a player to a roll.')
async def challenge(ctx, target_player, bet: str):
    # Query if User exists
    user = session.query(User).filter_by(name=ctx.author.name).first()

    members = ctx.message.mentions
    if members:
        member = members[0]
        member_name = members[0].name

    challenge_player = session.query(User).filter_by(name=member_name).first()

    if not user or not challenge_player:
        await ctx.send("User does not exist.")

    bet = validate_bet(bet)

    if not bet:
        await ctx.send("Invalid bet. Format's Available: 1, 1k, 1K, 1m, 1M")
        return

    if user.wallet < bet:
        await ctx.send("Insufficient funds to make this challenge.")

    elif challenge_player.wallet < bet:
        await ctx.send(f"{challenge_player.name} is broke af.")
    
    else:
        embed = discord.Embed(title=f'Challenging {challenge_player.name}', color=discord.Color.random())
        embed.add_field(name=f'{ctx.author.display_name} has challenged you to a duel for ${bet} Gold.', value="Type 'yes' or 'y' to accept.", inline=False)
        embed.set_thumbnail(url='https://cdn-icons-png.flaticon.com/512/1732/1732452.png')
        message = await ctx.send(embed=embed)

        reply = await bot.wait_for(event="message", check=author_check(member), timeout=30.0)
        
        if reply.content in ['yes', 'y', 'Y']:
            
            user.wallet -= bet
            challenge_player.wallet -= bet
            session.commit()

            player_roll = random.randint(1,100)
            challenge_player_roll = random.randint(1,100)

            if player_roll > challenge_player_roll:
                # Player Won
                user.wallet += 2*bet
                new_embed = discord.Embed(title='Challenge Roll', color=discord.Color.random())
                new_embed.add_field(name=f'{user.name} Won!', value=f"Sit {challenge_player.name} :point_down:", inline=False)
                new_embed.add_field(name=f"{user.name} :crown:", value=f"```{player_roll}```", inline=True)
                new_embed.add_field(name=f"{challenge_player.name}", value=f"```{challenge_player_roll}```", inline=True)
                new_embed.add_field(name=f"{user.name} Wallet",
                                value=f"```cs\n${user.wallet:,d} Gold```", inline=False)
                new_embed.add_field(name=f"{challenge_player.name} Wallet",
                                value=f"```cs\n${challenge_player.wallet:,d} Gold```", inline=False)
                new_embed.set_thumbnail(url='https://cdn-icons-png.flaticon.com/512/1732/1732452.png')
                await message.edit(embed=new_embed)
                
            elif challenge_player_roll > player_roll:
                # Receipient won
                challenge_player.wallet += 2*bet
                new_embed = discord.Embed(title='Challenge Roll', color=discord.Color.random())
                new_embed.add_field(name=f'{challenge_player.name} Won!', value=f"Sit {user.name} :point_down:", inline=False)
                new_embed.add_field(name=f"{user.name}", value=f"```{player_roll}```", inline=True)
                new_embed.add_field(name=f"{challenge_player.name} :crown:", value=f"```{challenge_player_roll}```", inline=True)
                new_embed.add_field(name=f"{user.name} Wallet",
                                value=f"```cs\n${user.wallet:,d} Gold```", inline=False)
                new_embed.add_field(name=f"{challenge_player.name} Wallet",
                                value=f"```cs\n${challenge_player.wallet:,d} Gold```", inline=False)
                new_embed.set_thumbnail(url='https://cdn-icons-png.flaticon.com/512/1732/1732452.png')
                await message.edit(embed=new_embed)
            else:
                # Draw
                user.wallet += bet
                challenge_player.wallet += bet
                new_embed = discord.Embed(title='Challenge Roll', color=discord.Color.random())
                new_embed.add_field(name='Draw!', value=f"Rematch?", inline=False)
                new_embed.add_field(name=f"{user.name} Roll", value=f"```{player_roll}```", inline=True)
                new_embed.add_field(name=f"{challenge_player.name} Roll", value=f"```{challenge_player_roll}```", inline=True)
                new_embed.set_thumbnail(url='https://cdn-icons-png.flaticon.com/512/1732/1732452.png')
                await message.edit(embed=new_embed)

        else:
            await ctx.send(f"No response by {challenge_player.name}")

    session.commit()

@bot.command(name='roll', aliases=["r"], help='Roll against the bot.')
async def roll(ctx, bet: str):
    # Query if User exists
    user = session.query(User).filter_by(name=ctx.author.name).first()

    if not user:
        user = create_user(ctx.author.name)
    
    check_casino(user)

    bet = validate_bet(bet)

    if not bet:
        await ctx.send("Invalid bet. Format's Available: 1, 1k, 1K, 1m, 1M")
        return
    
    if bet > user.wallet:
        await ctx.send('Insufficient Funds.')
    else:

        # Roll for the change at a ticket
        if bet > int(2 * 10**(user.level+2)):
            embed = roll_ticket(user)
            if embed:
                await ctx.send(embed=embed)

        bot_bet = random.randint(1,100)
        user_bet = random.randint(1,100)

        win = False
        if user_bet >= bot_bet:
            win = True

        if win:

            casino = session.query(Casino).filter_by(id=user.casino).first()
            tax_rate = get_tax(casino.level)
            tax_owing = int(tax_rate * bet)

            user.wallet += (bet - tax_owing)
            casino.balance += tax_owing

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

def check_casino(user: User):
    if not user.casino:
        casino = session.query(Casino).order_by(func.random()).first()
        user.casino = casino.id
        session.commit()

def author_check(author):
    return lambda message: message.author == author

def roll_ticket(user: User):
    roll = random.randint(0,50)

    if roll == 50:
        # Add a Ticket to the Database
        ticket = Ticket(
            user_id=user.id,
            level=user.level
        )
        session.add(ticket)
        session.commit()
        ticket_count = session.query(Ticket).filter_by(user_id=user.id).count()

        embed = discord.Embed(title='Ticket Winner!', color=discord.Color.green())
        embed.add_field(name=f'{user.name} just won a Ticket!', value=f"Congrats! $_$", inline=False)
        embed.add_field(name="Tickets",
            value=f"```cs\n{ticket_count:,d} Tickets```", inline=False)
        embed.set_thumbnail(url='https://upload.wikimedia.org/wikipedia/commons/a/a9/Scratch_game.jpg')
        return embed

    return False

@bot.command(name='ticket', help='Check your tickets. Or do .ticket roll to Roll a ticket.')
async def ticket(ctx, roll=None):
    # Query if User exists
    user = session.query(User).filter_by(name=ctx.author.name).first()

    if not user:
        await ctx.send('User does not exist. Type .bal to create an account.')
        return

    ticket_count = session.query(Ticket).filter_by(user_id=user.id).count()

    if not roll:
        embed = discord.Embed(title=f"{user.name}'s Tickets", color=discord.Color.green())
        embed.add_field(name="Tickets",
            value=f"```cs\n{ticket_count:,d} Tickets```", inline=False)
        await ctx.send(embed=embed)
    else:
        if roll == 'roll' and ticket_count > 0:
            ticket = session.query(Ticket).filter_by(user_id=user.id).first()
            dice = random.randint(0,100)
            if dice == 100:
                user.level += 1
                session.commit()
                embed = discord.Embed(title='MAJOR PRIZE!', color=discord.Color.green())
                embed.add_field(name=f'You just won the major prize!', value=f"A level up!!!", inline=False)
                embed.add_field(name="Level",
                    value=f"```cs\n{user.level}```", inline=False)
                embed.set_thumbnail(url='https://cdn1.walsworthyearbooks.com/wyb/2019/09/05090507/Level-Up-Final-02-copy-1.jpg')
                await ctx.send(embed=embed)
            elif dice > 80:
                user.wallet += int(10**(ticket.level + 3))
                session.commit()
                embed = discord.Embed(title='Big Win!', color=discord.Color.green())
                embed.add_field(name=f'You won a BIG prize!', value=f"EZ MONEY", inline=False)
                embed.add_field(name="Earnings",
                    value=f"```cs\n${int(10**(ticket.level + 3)):,d} Gold```", inline=False)
                embed.add_field(name="Wallet",
                    value=f"```cs\n${user.wallet:,d} Gold```", inline=False)
                embed.set_thumbnail(url='https://previews.123rf.com/images/tvoukent/tvoukent1911/tvoukent191100007/135375255-the-winner-retro-banner-with-glowing-lamps-winners-lottery-game-jackpot-prize-logo-vector-background.jpg')
                await ctx.send(embed=embed)
            elif dice > 40:
                user.wallet += int(0.5 * 10**(ticket.level + 3))
                session.commit()
                embed = discord.Embed(title='Big Win!', color=discord.Color.green())
                embed.add_field(name=f'You won a Common prize!', value=f"EZ MONEY", inline=False)
                embed.add_field(name="Earnings",
                    value=f"```cs\n${int(0.5 * 10**(ticket.level + 3)):,d} Gold```", inline=False)
                embed.add_field(name="Wallet",
                    value=f"```cs\n${user.wallet:,d} Gold```", inline=False)
                embed.set_thumbnail(url='https://www.corecu.ie/wp-content/uploads/2019/10/Capture.jpg')
                await ctx.send(embed=embed)
            else:
                user.wallet += int(2 * 10**(ticket.level + 2))
                session.commit()
                embed = discord.Embed(title='Minor Win!', color=discord.Color.green())
                embed.add_field(name=f'You won a Minor prize!', value=f"Fair enough", inline=False)
                embed.add_field(name="Earnings",
                    value=f"```cs\n${int(2 * 10**(ticket.level + 2)):,d} Gold```", inline=False)
                embed.add_field(name="Wallet",
                    value=f"```cs\n${user.wallet:,d} Gold```", inline=False)
                embed.set_thumbnail(url='https://www.casinoreports.ca/wp-content/uploads/2020/01/the_winner_of_the_largest_lottery_jackpot_-in_canadian_history.jpg')
                await ctx.send(embed=embed)
            
            session.delete(ticket)
            session.commit()

        elif roll == 'roll' and ticket_count == 0:
            await ctx.send('Not enough tickets buddy.')     
        else:
            await ctx.send("Invalid Command. Options are .ticket or .ticket roll")

@bot.command(name='blackjack', aliases=["bj"], help='Roll against the bot.')
async def blackjack(ctx, bet: str):
    # Query if User exists
    user = session.query(User).filter_by(name=ctx.author.name).first()

    if not user:
        user = create_user(ctx.author.name)

    check_casino(user)

    bet = validate_bet(bet)

    if not bet:
        await ctx.send("Invalid bet. Format's Available: 1, 1k, 1K, 1m, 1M")
        return
    
    if bet > user.wallet:
        await ctx.send('Insufficient Funds.')
    else:

        # Roll for the change at a ticket
        if bet >= int(2 * 10**(user.level+2)):
            embed = roll_ticket(user)
            if embed:
                await ctx.send(embed=embed)

        user.wallet -= bet
        session.commit()
        
        embed = discord.Embed(title='Blackjack', color=discord.Color.random())

        player_cards = []
        dealer_cards = []
        player_score = 0
        dealer_score = 0
        game = True
        win = False

        while len(player_cards) < 2:
            player_card = Card()
            player_cards.append(player_card)
            player_score += player_card.card_value

            if len(player_cards) == 2:
                if player_cards[0].card_value == 11 and player_cards[1].card_value == 11:
                    player_cards[0].card_value = 1
                    player_score -= 10
            else:
                dealer_card = Card()
                dealer_cards.append(dealer_card)
                dealer_score += dealer_card.card_value

            player_cards_display = ' '.join([card.card + card.suits_value for card in player_cards])
            dealer_cards_display = ' '.join([card.card + card.suits_value for card in dealer_cards])
            
            if player_score == 21:
                game = False
                win = True

        if game:
            embed.add_field(name=f'Your Hand', value=f"{player_cards_display}", inline=True)
            embed.add_field(name=f'Total', value=f"```cs\n{player_score}```", inline=False)
            embed.add_field(name=f"Bot's Hand", value=f"{dealer_cards_display}", inline=False)
            embed.add_field(name=f'Total', value=f"```cs\n{dealer_score}```", inline=True)
            embed.add_field(name=f'Your Move', value=f"hit (or h), stand (or s)", inline=False)
            embed.set_thumbnail(url='https://icon-library.com/images/blackjack-icon/blackjack-icon-27.jpg')
            embed.set_footer(text=f"{user.name}", icon_url = ctx.author.avatar_url)
            message = await ctx.send(embed=embed)

        if not game and win:
            # blackjack off the bat

            casino = session.query(Casino).filter_by(id=user.casino).first()
            tax_rate = get_tax(casino.level)
            tax_owing = int(tax_rate * 2.5*bet)

            user.wallet += int(2.5*bet - tax_owing)
            casino.balance += tax_owing

            new_embed = discord.Embed(title='Blackjack - Win!', color=discord.Color.green())
            new_embed.add_field(name=f'Your Hand', value=f"{player_cards_display}", inline=False)
            new_embed.add_field(name=f'Total', value=f"```cs\n{player_score}```", inline=False)
            new_embed.add_field(name=f"Bot's Hand", value=f"{dealer_cards_display}", inline=False)
            new_embed.add_field(name=f'Total', value=f"```cs\n{dealer_score}```", inline=False)
            new_embed.add_field(name="Result",
                value=f"BLACKJACK! ^.^", inline=False)
            new_embed.add_field(name="Earnings",
                value=f"```cs\n${int(2.5*bet - tax_owing):,d} Gold```", inline=False)
            new_embed.add_field(name="Wallet",
                value=f"```cs\n${user.wallet:,d} Gold```", inline=False)
            new_embed.set_thumbnail(url='https://icon-library.com/images/blackjack-icon/blackjack-icon-27.jpg')
            new_embed.set_footer(text=f"{user.name}", icon_url = ctx.author.avatar_url)
            await ctx.send(embed=new_embed)
            return

        while player_score < 21 and game:
            reply = await bot.wait_for(event="message", check=author_check(ctx.author), timeout=30.0)
            
            while reply.content not in ['hit', 'stand', 'h', 's', "Hit", "H", "Stand", "S"]:
                await ctx.send("Invalid Command for Blackjack. Please use keywords 'hit', 'stand', 'h', or 's'")
                reply = await bot.wait_for(event="message", check=author_check(ctx.author), timeout=30.0)
            
            if reply.content in ['hit', 'h', "Hit", "H"]:
                
                player_card = Card()
                player_cards.append(player_card)
                player_score += player_card.card_value

                # Updating player score in case player's card have ace in them
                c = 0
                while player_score > 21 and c < len(player_cards):
                    if player_cards[c].card_value == 11:
                        player_cards[c].card_value = 1
                        player_score -= 10
                        c += 1
                    else:
                        c += 1 

            if reply.content in ['stand', 's', "Stand", "S"]:
                game = False
            
            player_cards_display = ' '.join([card.card + card.suits_value for card in player_cards])
            new_embed = discord.Embed(title='Blackjack', color=discord.Color.random())
            new_embed.add_field(name=f'Your Hand', value=f"{player_cards_display}", inline=True)
            new_embed.add_field(name=f'Total', value=f"```cs\n{player_score}```", inline=False)
            new_embed.add_field(name=f"Bot's Hand", value=f"{dealer_cards_display}", inline=False)
            new_embed.add_field(name=f'Total', value=f"```cs\n{dealer_score}```", inline=False)
            new_embed.add_field(name=f'Your Move', value=f"hit (or h), stand (or s)", inline=False)
            new_embed.set_thumbnail(url='https://icon-library.com/images/blackjack-icon/blackjack-icon-27.jpg')
            new_embed.set_footer(text=f"{user.name}", icon_url = ctx.author.avatar_url)
            await message.edit(embed=new_embed)

        while dealer_score < 17 and player_score <= 21:

            dealer_card = Card()
            dealer_cards.append(dealer_card)
            dealer_score += dealer_card.card_value

            # Updating player score in case player's card have ace in them
            c = 0
            while dealer_score > 21 and c < len(dealer_cards):
                if dealer_cards[c].card_value == 11:
                    dealer_cards[c].card_value = 1
                    dealer_score -= 10
                    c += 1
                else:
                    c += 1

            dealer_cards_display = ' '.join([card.card + card.suits_value for card in dealer_cards])
            new_embed = discord.Embed(title="Blackjack - Bot's Turn", color=discord.Color.random())
            new_embed.add_field(name=f'Your Hand', value=f"{player_cards_display}", inline=True)
            new_embed.add_field(name=f'Total', value=f"```cs\n{player_score}```", inline=False)
            new_embed.add_field(name=f"Bot's Hand", value=f"{dealer_cards_display}", inline=False)
            new_embed.add_field(name=f'Total', value=f"```cs\n{dealer_score}```", inline=False)
            new_embed.set_thumbnail(url='https://icon-library.com/images/blackjack-icon/blackjack-icon-27.jpg')
            new_embed.set_footer(text=f"{user.name}", icon_url = ctx.author.avatar_url)
            await message.edit(embed=new_embed)
            await asyncio.sleep(1)

        if dealer_score > 21 or dealer_score < player_score:
            win = True

        draw = False
        if dealer_score <= 21 and player_score <= 21 and dealer_score == player_score:
            draw = True

        if player_score > 21:
            win = False

        if win:

            casino = session.query(Casino).filter_by(id=user.casino).first()
            tax_rate = get_tax(casino.level)
            tax_owing = int(tax_rate * 2*bet)

            user.wallet += int(2*bet - tax_owing)
            casino.balance += tax_owing

            new_embed = discord.Embed(title='Blackjack - Win!', color=discord.Color.green())
            new_embed.add_field(name=f'Your Hand', value=f"{player_cards_display}", inline=False)
            new_embed.add_field(name=f'Total', value=f"```cs\n{player_score}```", inline=False)
            new_embed.add_field(name=f"Bot's Hand", value=f"{dealer_cards_display}", inline=False)
            new_embed.add_field(name=f'Total', value=f"```cs\n{dealer_score}```", inline=False)
            new_embed.add_field(name="Result",
                value=f"You Win! ^.^", inline=False)
            new_embed.add_field(name="Wallet",
                value=f"```cs\n${user.wallet:,d} Gold```", inline=False)
            new_embed.set_thumbnail(url='https://icon-library.com/images/blackjack-icon/blackjack-icon-27.jpg')
            new_embed.set_footer(text=f"{user.name}", icon_url = ctx.author.avatar_url)
            await message.edit(embed=new_embed)

        elif not win and not draw:
            new_embed = discord.Embed(title='Blackjack - Loss', color=discord.Color.red())
            new_embed.add_field(name=f'Your Hand', value=f"{player_cards_display}", inline=False)
            new_embed.add_field(name=f'Total', value=f"```cs\n{player_score}```", inline=False)
            new_embed.add_field(name=f"Bot's Hand", value=f"{dealer_cards_display}", inline=False)
            new_embed.add_field(name=f'Total', value=f"```cs\n{dealer_score}```", inline=False)
            new_embed.add_field(name="Result",
                value=f"You lose! X_X", inline=False)
            new_embed.add_field(name="Wallet",
                value=f"```cs\n${user.wallet:,d} Gold```", inline=False)
            new_embed.set_thumbnail(url='https://icon-library.com/images/blackjack-icon/blackjack-icon-27.jpg')
            new_embed.set_footer(text=f"{user.name}", icon_url = ctx.author.avatar_url)
            await message.edit(embed=new_embed)

        else:
            user.wallet += bet
            new_embed = discord.Embed(title='Blackjack - Draw', color=discord.Color.red())
            new_embed.add_field(name=f'Your Hand', value=f"{player_cards_display}", inline=False)
            new_embed.add_field(name=f'Total', value=f"```cs\n{player_score}```", inline=False)
            new_embed.add_field(name=f"Bot's Hand", value=f"{dealer_cards_display}", inline=False)
            new_embed.add_field(name=f'Total', value=f"```cs\n{dealer_score}```", inline=False)
            new_embed.add_field(name="Result",
                value=f"Draw Game!", inline=False)
            new_embed.set_thumbnail(url='https://icon-library.com/images/blackjack-icon/blackjack-icon-27.jpg')
            new_embed.set_footer(text=f"{user.name}", icon_url = ctx.author.avatar_url)
            await message.edit(embed=new_embed)

    session.commit()

@bot.command(name='highlow', aliases=["hl"], help='Play High and Low against the bot. Min bet is 2M.')
async def highlow(ctx, bet: str):
    # Query if User exists
    user = session.query(User).filter_by(name=ctx.author.name).first()

    if not user:
        user = create_user(ctx.author.name)

    check_casino(user)

    bet = validate_bet(bet)

    if not bet:
        await ctx.send("Invalid bet. Format's Available: 1, 1k, 1K, 1m, 1M")
        return
    
    if bet < int(2 * (10**(user.level+2))):
        await ctx.send(f"Minimum bet is {int(2 * (10**(user.level+2))):,d}.")
        return

    if bet > user.wallet:
        await ctx.send('Insufficient Funds.')
    else:
        # Roll for the change at a ticket
        embed = roll_ticket(user)
        if embed:
            await ctx.send(embed=embed)

        user.wallet -= bet
        session.commit()

        game = True
        win = False
        reward = bet
        player_cards = []
        player_card = Card()

        # Ace counts as 1, J as 11, Q as 12, K as 13
        if player_card.card_value == 11:
            player_card.card_value = 14
        if player_card.card == 'J':
            player_card.card_value = 11
        if player_card.card == 'Q':
            player_card.card_value = 12
        if player_card.card == 'K':
            player_card.card_value = 13

        player_cards.append(player_card)
        player_cards_display = ' '.join([card.card + card.suits_value for card in player_cards])

        embed = discord.Embed(title='High Low - Round 1', color=discord.Color.random())
        embed.add_field(name=f'Your Hand', value=f"{player_cards_display}", inline=False)
        embed.add_field(name=f'Your Move', value=f"High (h) or Low (l)", inline=False)
        embed.set_thumbnail(url='https://smartcasinoguide.com/app/uploads/2018/04/how-to-play-high-low-card-game.png')
        embed.set_footer(text=f"{user.name}", icon_url = ctx.author.avatar_url)
        message = await ctx.send(embed=embed)

        round = 1
        while game:

            if round == 5:
                win = True
                break

            if round > 1:
                new_embed = discord.Embed(title=f'High Low - Round {round}', color=discord.Color.random())
                new_embed.add_field(name=f'Your Hand', value=f"{player_cards_display}", inline=False)
                new_embed.add_field(name=f'Current Reward', value=f"```cs\n${reward:,d} Gold```", inline=False)
                new_embed.add_field(name=f'Your Move', value=f"High (h) or Low (l)", inline=False)
                new_embed.set_thumbnail(url='https://smartcasinoguide.com/app/uploads/2018/04/how-to-play-high-low-card-game.png')
                new_embed.set_footer(text=f"{user.name}", icon_url = ctx.author.avatar_url)
                await message.edit(embed=new_embed)

            reply = await bot.wait_for(event="message", check=author_check(ctx.author), timeout=30.0)
            
            while reply.content not in ['h', "H", 'l', "L"]:
                await ctx.send("Invalid Command for High/Low. Please use keywords 'h' ,'H', 'l', or 'L'")
                reply = await bot.wait_for(event="message", check=author_check(ctx.author), timeout=30.0)
            
            next_card = Card()
            # Ace counts as 1, J as 11, Q as 12, K as 13
            if next_card.card_value == 11:
                next_card.card_value = 14
            if next_card.card == 'J':
                next_card.card_value = 11
            if next_card.card == 'Q':
                next_card.card_value = 12
            if next_card.card == 'K':
                next_card.card_value = 13
            
            player_cards.append(next_card)
            player_cards_display = ' '.join([card.card + card.suits_value for card in player_cards])

            if reply.content in ['h', 'H']:
                if next_card.card_value < player_card.card_value:
                    game = False
            
            if reply.content in ['l', 'L']:
                if next_card.card_value > player_card.card_value:
                    game = False

            if next_card.card_value == player_card.card_value:
                game = False
            
            if game:
                player_card = next_card
                round += 1
                reward = int(reward *  1.25)
                new_embed = discord.Embed(title="Round Won!", color=discord.Color.green())
                new_embed.add_field(name=f'Your Hand', value=f"{player_cards_display}", inline=False)
                new_embed.add_field(name=f'Potential Reward', value=f"```cs\n${reward:,d} Gold```", inline=False)
                new_embed.add_field(name=f'Your Move', value=f"High (h) or Low (l)", inline=False)
                new_embed.set_thumbnail(url='https://smartcasinoguide.com/app/uploads/2018/04/how-to-play-high-low-card-game.png')
                new_embed.set_footer(text=f"{user.name}", icon_url = ctx.author.avatar_url)
                await message.edit(embed=new_embed)
                await asyncio.sleep(0.5)
            
        if not win:
            new_embed = discord.Embed(title='High Low - Loss', color=discord.Color.red())
            new_embed.add_field(name=f'Your Hand', value=f"{player_cards_display}", inline=False)
            new_embed.add_field(name="Result",
                value=f"You lose! X_X", inline=False)
            new_embed.add_field(name="Wallet",
                value=f"```cs\n${user.wallet:,d} Gold```", inline=False)
            new_embed.set_thumbnail(url='https://smartcasinoguide.com/app/uploads/2018/04/how-to-play-high-low-card-game.png')
            new_embed.set_footer(text=f"{user.name}", icon_url = ctx.author.avatar_url)
            await message.edit(embed=new_embed)
        else:
            # Winner
            casino = session.query(Casino).filter_by(id=user.casino).first()
            casino_owner = session.query(User).filter_by(id=casino.user_id).first()
            tax_rate = get_tax(casino.level)
            tax_owing = int(tax_rate * reward)

            user.wallet += int(reward - tax_owing)
            casino.balance += tax_owing
            session.commit()

            new_embed = discord.Embed(title='High Low - Winner!', color=discord.Color.green())
            new_embed.add_field(name=f'Your Hand', value=f"{player_cards_display}", inline=False)
            new_embed.add_field(name="Result",
                value=f"HOLY SHIT YOU WON! ^.^", inline=False)
            new_embed.add_field(name="Earnings",
                value=f"```cs\n${int(reward):,d} Gold```", inline=False)
            new_embed.add_field(name=f"Taxes Paid to {casino_owner.name}",
                            value=f"```cs\n${tax_owing:,d} Gold```", inline=False)
            new_embed.add_field(name="Wallet",
                value=f"```cs\n${user.wallet:,d} Gold```", inline=False)
            new_embed.set_thumbnail(url='https://www.onlineunitedstatescasinos.com/wp-content/uploads/2021/02/Online-Slot-Spinning-Reels-Jackpot-Icon.png')
            new_embed.set_footer(text=f"{user.name}", icon_url = ctx.author.avatar_url)
            await message.edit(embed=new_embed)

@bot.command(name='bottle', aliases=["bg"], help='Play the bottle game against the bot.')
async def bottle(ctx, target_player, bet: str):
    # Query if User exists
    user = session.query(User).filter_by(name=ctx.author.name).first()

    members = ctx.message.mentions
    if members:
        member = members[0]
        member_name = members[0].name

    challenge_player = session.query(User).filter_by(name=member_name).first()

    if not user or not challenge_player:
        await ctx.send("User does not exist.")

    bet = validate_bet(bet)

    if not bet:
        await ctx.send("Invalid bet. Format's Available: 1, 1k, 1K, 1m, 1M")
        return

    if user.wallet < bet:
        await ctx.send("Insufficient funds to make this challenge.")

    elif challenge_player.wallet < bet:
        await ctx.send(f"{challenge_player.name} is broke af.")
    else:

        embed = discord.Embed(title=f'Challenging {challenge_player.name}', color=discord.Color.random())
        embed.add_field(name=f'{ctx.author.display_name} has challenged you to a duel for ${bet} Gold.', value="Type 'yes' or 'y' to accept.", inline=False)
        embed.set_thumbnail(url='https://cdn-icons-png.flaticon.com/512/1732/1732452.png')
        message = await ctx.send(embed=embed)

        reply = await bot.wait_for(event="message", check=author_check(member), timeout=30.0)
        
        if reply.content in ['yes', 'y', 'Y']:
            
            user.wallet -= bet
            challenge_player.wallet -= bet
            session.commit()

            game = True
            win = False
            bottle_position = 4
            player_balance = 100
            challenge_player_balance = 100
            spots = 9
            game_pieces = ['_' for idx in range(spots)]
            game_pieces[bottle_position] = 'B'
            game_board_display = ' '.join(game_pieces)

            embed = discord.Embed(title='Bottle Game', color=discord.Color.random())
            embed.add_field(name=f"{user.name} Balance",
                            value=f"```{100}```", inline=True)
            embed.add_field(name=f"{challenge_player.name} Balance",
                            value=f"```{100}```", inline=True)
            embed.add_field(name="Game",
                            value=f"```{game_board_display}```", inline=False)
            embed.add_field(name="Action",
                            value=f"{user.name} needs to make a bet.", inline=False)
            await message.edit(embed=embed)

            while game:
                if bottle_position == 0:
                    user.wallet += 2*bet
                    new_embed = discord.Embed(title='Bottle Game', color=discord.Color.random())
                    new_embed.add_field(name=f'{user.name} Won!', value=f"Good game.", inline=False)
                    new_embed.add_field(name=f"{user.name} Wallet",
                                    value=f"```cs\n${user.wallet:,d} Gold```", inline=False)
                    new_embed.add_field(name=f"{challenge_player.name} Wallet",
                                    value=f"```cs\n${challenge_player.wallet:,d} Gold```", inline=False)
                    await message.edit(embed=new_embed)
                    session.commit()
                    game = False
                elif bottle_position == 8:
                    challenge_player.wallet += 2*bet
                    new_embed = discord.Embed(title='Bottle Game', color=discord.Color.random())
                    new_embed.add_field(name=f'{challenge_player.name} Won!', value=f"Good game.", inline=False)
                    new_embed.add_field(name=f"{user.name} Wallet",
                                    value=f"```cs\n${user.wallet:,d} Gold```", inline=False)
                    new_embed.add_field(name=f"{challenge_player.name} Wallet",
                                    value=f"```cs\n${challenge_player.wallet:,d} Gold```", inline=False)
                    await message.edit(embed=new_embed)
                    session.commit()
                    game = False
                elif player_balance == 0 and challenge_player_balance == 0:
                    challenge_player.wallet += bet
                    user.wallet += bet
                    new_embed = discord.Embed(title='Bottle Game', color=discord.Color.random())
                    new_embed.add_field(name=f'{challenge_player.name} Draw!', value=f"Good game.", inline=False)
                    new_embed.add_field(name=f"{user.name} Wallet",
                                    value=f"```cs\n${user.wallet:,d} Gold```", inline=False)
                    new_embed.add_field(name=f"{challenge_player.name} Wallet",
                                    value=f"```cs\n${challenge_player.wallet:,d} Gold```", inline=False)
                    await message.edit(embed=new_embed)
                    session.commit()
                    game = False

                if not game:
                    break
                
                # Player bets
                if player_balance == 0:
                    player_bet = 0
                else:
                    player_reply = await bot.wait_for(event="message", check=author_check(ctx.author), timeout=30.0)
                    while not player_reply.content.isnumeric() or int(player_reply.content) < 0 or int(player_reply.content) > player_balance:
                        await ctx.send(f"Invalid Response. Please bet a number between 0 and {player_balance}")
                        player_reply = await bot.wait_for(event="message", check=author_check(ctx.author), timeout=30.0)
                    player_bet = int(player_reply.content)
                    if not player_reply.channel.type == discord.ChannelType.private:
                        await player_reply.delete()

                    # If user does not reply
                    if player_reply is None:
                        challenge_player.wallet += 2*bet
                        new_embed = discord.Embed(title='Bottle Game', color=discord.Color.random())
                        new_embed.add_field(name=f'{challenge_player.name} Won due to {user.name} timing out!', value=f"Good game.", inline=False)
                        new_embed.add_field(name=f"{user.name} Wallet",
                                        value=f"```cs\n${user.wallet:,d} Gold```", inline=False)
                        new_embed.add_field(name=f"{challenge_player.name} Wallet",
                                        value=f"```cs\n${challenge_player.wallet:,d} Gold```", inline=False)
                        await message.edit(embed=new_embed)
                        session.commit()
                        game = False
                        break
                    
                new_embed = discord.Embed(title='Bottle Game', color=discord.Color.random())
                new_embed.add_field(name=f"{user.name} Balance",
                                value=f"```{player_balance}```", inline=True)
                new_embed.add_field(name=f"{challenge_player.name} Balance",
                                value=f"```{challenge_player_balance}```", inline=True)
                new_embed.add_field(name="Game",
                                value=f"```{game_board_display}```", inline=False)
                new_embed.add_field(name="Action",
                                value=f"{user.name} has placed their bet. \n{challenge_player.name} needs to make a bet.", inline=False)
                await message.edit(embed=new_embed)
                
                # Challenger bets
                if challenge_player_balance == 0:
                    challenge_player_bet = 0
                else:
                    challenge_player_reply = await bot.wait_for(event="message", check=author_check(member), timeout=30.0)
                    while not challenge_player_reply.content.isnumeric() or int(challenge_player_reply.content) < 0 or int(challenge_player_reply.content) > player_balance:
                        await ctx.send(f"Invalid Response. Please bet a number between 0 and {challenge_player_balance}")
                        challenge_player_reply = await bot.wait_for(event="message", check=author_check(member), timeout=30.0)
                    challenge_player_bet = int(challenge_player_reply.content)
                    if not challenge_player_reply.channel.type == discord.ChannelType.private:
                        await challenge_player_reply.delete()
                    
                    # If Challenger does not reply
                    if challenge_player_reply is None:
                        user.wallet += 2*bet
                        new_embed = discord.Embed(title='Bottle Game', color=discord.Color.random())
                        new_embed.add_field(name=f'{user.name} Won due to {challenge_player.name} timing out!', value=f"Good game.", inline=False)
                        new_embed.add_field(name=f"{user.name} Wallet",
                                        value=f"```cs\n${user.wallet:,d} Gold```", inline=False)
                        new_embed.add_field(name=f"{challenge_player.name} Wallet",
                                        value=f"```cs\n${challenge_player.wallet:,d} Gold```", inline=False)
                        await message.edit(embed=new_embed)
                        session.commit()
                        game = False
                        break
                    
                new_embed = discord.Embed(title='Bottle Game', color=discord.Color.random())
                new_embed.add_field(name=f"{user.name} Balance",
                                value=f"```{100}```", inline=True)
                new_embed.add_field(name=f"{challenge_player.name} Balance",
                                value=f"```{100}```", inline=True)
                new_embed.add_field(name="Game",
                                value=f"```{game_board_display}```", inline=False)
                new_embed.add_field(name="Action",
                                value=f"Both players have placed their bet.", inline=False)
                await message.edit(embed=new_embed)

                if player_bet > challenge_player_bet:
                    bottle_position -= 1
                    player_balance -= player_bet
                    round_winner = user
                elif player_bet < challenge_player_bet:
                    bottle_position += 1
                    challenge_player_balance -= challenge_player_bet
                    round_winner = challenge_player
                else:
                    if random.randint(0,1):
                        bottle_position -= 1
                        player_balance -= player_bet
                        round_winner = user
                    else:
                        bottle_position += 1
                        challenge_player_balance -= challenge_player_bet
                        round_winner = challenge_player

                game_pieces = ['_' for idx in range(spots)]
                game_pieces[bottle_position] = 'B'
                game_board_display = ' '.join(game_pieces)

                if round_winner == user:
                    new_embed = discord.Embed(title='Bottle Game', color=discord.Color.random())
                    new_embed.add_field(name=f"{user.name} Bet",
                                    value=f"```{player_bet}```", inline=True)
                    new_embed.add_field(name=f"{challenge_player.name} Bet",
                                    value=f"```{challenge_player_bet}```", inline=True)
                    new_embed.add_field(name='\u200b', value='\u200b', inline=False)
                    new_embed.add_field(name=f"{user.name} Balance",
                                    value=f"```{player_balance}```", inline=True)
                    new_embed.add_field(name=f"{challenge_player.name} Balance",
                                    value=f"```{challenge_player_balance}```", inline=True)
                    new_embed.add_field(name="Game",
                                    value=f"```{game_board_display}```", inline=False)
                    new_embed.add_field(name="Winner",
                                    value=f"{user.name} won this round.", inline=False)
                    await message.edit(embed=new_embed)
                    await asyncio.sleep(1)
                else:
                    new_embed = discord.Embed(title='Bottle Game', color=discord.Color.random())
                    new_embed.add_field(name=f"{user.name} Bet",
                                    value=f"```{player_bet}```", inline=True)
                    new_embed.add_field(name=f"{challenge_player.name} Bet",
                                    value=f"```{challenge_player_bet}```", inline=True)
                    new_embed.add_field(name='\u200b', value='\u200b', inline=False)
                    new_embed.add_field(name=f"{user.name} Balance",
                                    value=f"```{player_balance}```", inline=True)
                    new_embed.add_field(name=f"{challenge_player.name} Balance",
                                    value=f"```{challenge_player_balance}```", inline=True)
                    new_embed.add_field(name="Game",
                                    value=f"```{game_board_display}```", inline=False)
                    new_embed.add_field(name="Winner",
                                    value=f"{challenge_player.name} won this round.", inline=False)
                    await message.edit(embed=new_embed)
                    await asyncio.sleep(1)

        else:
            await ctx.send(f'{challenge_player.name} rejected the offer.')
        
@bot.command(name='rps', help='Do a Rock Paper Scissors match.')
async def rps(ctx, bet: str, rps: str):
    # Query if User exists
    user = session.query(User).filter_by(name=ctx.author.name).first()

    if not user:
        user = create_user(ctx.author.name)

    check_casino(user)

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

        # Roll for the change at a ticket
        if bet > int(2 * 10**(user.level+2)):
            embed = roll_ticket(user)
            if embed:
                await ctx.send(embed=embed)

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
            embed = discord.Embed(title='Rock Paper Scissors', color=discord.Color.red())
            embed.add_field(name=f'{ctx.author.display_name}', value="Draw!", inline=False)
            embed.add_field(name="Your Move", value=f"```{rps}```", inline=True)
            embed.add_field(name="Bot's Move", value=f"```{bot_move}```", inline=True)
            embed.add_field(name="Wallet",
                            value=f"```cs\n${user.wallet:,d} Gold```", inline=False)
            await ctx.send(embed=embed)

        elif win:

            casino = session.query(Casino).filter_by(id=user.casino).first()
            casino_owner = session.query(User).filter_by(id=casino.user_id).first()
            tax_rate = get_tax(casino.level)
            tax_owing = int(tax_rate * bet)

            user.wallet += int(bet - tax_owing)
            casino.balance += tax_owing
            session.commit()

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
        user.last_work=datetime.datetime.now()

        # Entering a casino
        casino = session.query(Casino).order_by(func.random()).first()
        casino_owner = session.query(User).filter_by(id=casino.user_id).first()
        user.casino = casino.id
        tax_rate = get_tax(casino.level)
        session.commit()

        embed = discord.Embed(title=f'Work Level {user.level}', color=discord.Color.green())
        embed.add_field(name=f'{ctx.author.display_name}', value="You earned $1,000", inline=False)
        embed.add_field(name="Wallet",
                        value=f"```cs\n${user.wallet:,d} Gold```", inline=True)
        embed.add_field(name=f"Entering {casino_owner.name}'s Casino",
                        value=f"```cs\n{tax_rate:.0%} Tax```", inline=True)
        await ctx.send(embed=embed)

    else:

        if ctx.channel.type == discord.ChannelType.private:
            await ctx.send("Don't PM me bro.")
            return

        recent_job = user.last_work

        earnings = 10 ** (user.level + 2)

        # Mechanic Earnings
        professions = session.query(Profession).filter_by(user_id=user.id, profession_id=3).all()
        crafter = False
        if professions:
            crafter = True

        if user.diamond == True or crafter:
            earnings *= 2


        time_delta = datetime.datetime.now() - recent_job
        minutes = round(time_delta.total_seconds() / 60,0)
        if minutes > 10:
            user.wallet += earnings

            # Entering a casino
            casino = session.query(Casino).order_by(func.random()).first()
            casino_owner = session.query(User).filter_by(id=casino.user_id).first()
            user.casino = casino.id
            tax_rate = get_tax(casino.level)

            embed = discord.Embed(title=f'Work Level {user.level}', color=discord.Color.green())
            embed.add_field(name=f'{ctx.author.display_name}', value=f"You earned ${earnings:,d}", inline=False)
            embed.add_field(name="Wallet",
                            value=f"```cs\n${user.wallet:,d} Gold```", inline=False)
            embed.add_field(name=f"Entering {casino_owner.name}'s Casino",
                        value=f"```cs\n{tax_rate:.0%} Tax```", inline=False)
            await ctx.send(embed=embed)
            user.last_work = datetime.datetime.now()
        else:
            time_remaining = int(10-minutes)
            embed = discord.Embed(title=f'Work Level {user.level}', color=discord.Color.red())
            embed.add_field(name=f'{ctx.author.display_name}', value=f"{time_remaining} minutes remaining...", inline=False)
            await ctx.send(embed=embed)
    
    session.commit()

@bot.command(name='hourly', aliases=["h"], help='Make some money every hour.')
async def hourly(ctx):
    # Query if User exists
    user = session.query(User).filter_by(name=ctx.author.name).first()

    if not user:
        user = create_user(ctx.author.name)
        user.wallet += 5000

        embed = discord.Embed(title=f'Hourly Rewards!', color=discord.Color.green())
        embed.add_field(name=f'{ctx.author.display_name}', value="You earned some money!", inline=False)
        embed.add_field(name="Wallet",
                        value=f"```cs\n${user.wallet:,d} Gold```", inline=True)
        await ctx.send(embed=embed)

        user.last_hourly = datetime.datetime.now()
        session.commit()
    else:
        if ctx.channel.type == discord.ChannelType.private:
            await ctx.send("Don't PM me bro.")
            return

        time_delta = datetime.datetime.now() - user.last_hourly
        minutes = round(time_delta.total_seconds() / 60,0)
        if minutes > 60:
            user.wallet += int(2*(10 ** (user.level + 2)))
            embed = discord.Embed(title=f'Hourly Rewards!', color=discord.Color.green())
            embed.add_field(name=f'{ctx.author.display_name}', value="You earned some money!", inline=False)
            embed.add_field(name="Wallet",
                            value=f"```cs\n${user.wallet:,d} Gold```", inline=True)
            await ctx.send(embed=embed)
            user.last_hourly = datetime.datetime.now()
            session.commit()
        else:
            time_remaining = int(60-minutes)
            embed = discord.Embed(title=f'Hourly', color=discord.Color.red())
            embed.add_field(name=f'{ctx.author.display_name}', value=f"{time_remaining} minutes remaining...", inline=False)
            await ctx.send(embed=embed)
    
    session.commit()

@bot.command(name='daily', help='Make some money every hour.')
async def daily(ctx):
    # Query if User exists
    user = session.query(User).filter_by(name=ctx.author.name).first()

    if not user:
        user = create_user(ctx.author.name)
        user.wallet += 10000

        embed = discord.Embed(title=f'Daily Rewards!', color=discord.Color.green())
        embed.add_field(name=f'{ctx.author.display_name}', value="You earned some money!", inline=False)
        embed.add_field(name="Wallet",
                        value=f"```cs\n${user.wallet:,d} Gold```", inline=True)
        await ctx.send(embed=embed)

        user.last_daily = datetime.datetime.now()
        session.commit()
    else:
        time_delta = datetime.datetime.now() - user.last_daily
        minutes = round(time_delta.total_seconds() / 60,0)
        if minutes > 1440:
            user.wallet += int(10*(10 ** (user.level + 2)))
            embed = discord.Embed(title=f'Daily Rewards!', color=discord.Color.green())
            embed.add_field(name=f'{ctx.author.display_name}', value="You earned some money!", inline=False)
            embed.add_field(name="Wallet",
                            value=f"```cs\n${user.wallet:,d} Gold```", inline=True)
            await ctx.send(embed=embed)
            user.last_daily = datetime.datetime.now()
            session.commit()
        else:
            time_remaining = int(1440-minutes)
            embed = discord.Embed(title=f'Daily', color=discord.Color.red())
            embed.add_field(name=f'{ctx.author.display_name}', value=f"{time_remaining} minutes remaining...", inline=False)
            await ctx.send(embed=embed)
    
    session.commit()

@bot.command(name='miner', help='Check your miners earnings.')
async def miner(ctx):
    # Query if User exists
    user = session.query(User).filter_by(name=ctx.author.name).first()

    members = ctx.message.mentions
    if members:
        member = members[0]
        member_name = members[0].name

    # Query if User exists
    if members:
        user = session.query(User).filter_by(name=member_name).first()
    else:
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

    # Mechanic Earnings
    professions = session.query(Profession).filter_by(user_id=user.id, profession_id=2).first()
    mechanic = False
    if professions:
        mechanic = True

    if mechanic:
        earnings = int(3 * (10 ** (miner.level + 2)) * (minutes / 60))
        user.wallet += earnings

    session.commit()

    embed.set_thumbnail(url=miner_level_urs[miner.level])
    embed.add_field(name="Level",
                    value=f"```cs\n{str(miner.level)}```", inline=True)
    embed.add_field(name="Collected",
                    value=f"```cs\n${miner.balance:,d} Gold```", inline=True)
    if mechanic:
        embed.add_field(name="Mechanic Earnings",
                        value=f"```cs\n${earnings:,d} Gold```", inline=False)

    await ctx.send(embed=embed)

@bot.command(name='collect', aliases=["coll"], help='Collect your miners earnings.')
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

@bot.command(name='casino', help='Check or collect from your casino.')
async def casino(ctx, cmd=None):
    user = session.query(User).filter_by(name=ctx.author.name).first()
    
    members = ctx.message.mentions
    if members:
        member_name = members[0].name

    # Query if User exists
    if members:
        user = session.query(User).filter_by(name=member_name).first()
    else:
        user = session.query(User).filter_by(name=ctx.author.name).first()

    if not user:
        await ctx.send('User not found.')
    else:
        casino = session.query(Casino).filter_by(user_id=user.id).first()

        if not casino:
            casino = create_casino(user)

        casino_members = session.query(User).filter_by(casino=casino.id).all()

        member_names = '\n'.join([member.name for member in casino_members])

        tax_rate = get_tax(casino.level)
        
        if members or not cmd:
            embed = discord.Embed(title=f"{user.name}'s Casino", color=discord.Color.green())
            embed.add_field(name="Total Earned",
                            value=f"```cs\n${casino.balance:,d} Gold```", inline=True)
            embed.add_field(name="Tax Rate",
                            value=f"```cs\n{tax_rate:.0%} Tax```", inline=True)

            if len(casino_members):
                embed.add_field(name="Casino Guests",
                                value=f"```cs\n{member_names}```", inline=False)
            else:
                embed.add_field(name="Casino Guests",
                                value=f"```Empty```", inline=False)

            await ctx.send(embed=embed)
        elif cmd == 'collect' or cmd == 'coll':
            earnings = casino.balance
            user.wallet += earnings
            casino.balance = 0
            session.commit()
            embed = discord.Embed(title=f'{user.name} Casino Cashout', color=discord.Color.green())
            embed.add_field(name=f"Earnings",
                        value=f"```cs\n${earnings:,d} Gold```", inline=True)
            embed.add_field(name="Wallet",
                            value=f"```cs\n${user.wallet:,d} Gold```", inline=True)
            await ctx.send(embed=embed)
        else:
            await ctx.send("Invalid command. Do .casino or .casino collect")

@bot.command(name='buy', aliases=["shop"], help='Buy some stuff.')
async def buy(ctx, item=None):
    user = session.query(User).filter_by(name=ctx.author.name).first()
    
    if not user:
        await ctx.send('User not found.')
    else:

        check_casino(user)

        miner = session.query(Miner).filter_by(user_id=user.id).first()
        casino = session.query(Casino).filter_by(user_id=user.id).first()
        if not item:
            level_up_cost = 10 ** (user.level + 4)
            shield_cost = int(1.5 * (10 ** (user.level + 2)))

            # Mechanic Earnings
            professions = session.query(Profession).filter_by(user_id=user.id, profession_id=2).all()
            if professions:
                miner_upgrade_cost = 10 ** (miner.level + 4)
            else:
                miner_upgrade_cost = 2 * 10 ** (miner.level + 4)

            casino_upgarde_cost = 10 ** (casino.level + 4)
            embed = discord.Embed(title=f"{ctx.author.display_name}'s Shop", color=discord.Color.random())
            embed.add_field(name='[ID: 1] Shield', value=f"```cs\n${shield_cost:,d} Gold```", inline=False)

            if user.level < 5:
                embed.add_field(name='[ID: 2] Level Up', value=f"```cs\n${level_up_cost:,d} Gold```", inline=False)

            if miner.level < 5:
                embed.add_field(name='[ID: 3] Miner Upgrade', value=f"```cs\n${miner_upgrade_cost:,d} Gold```", inline=False)

            embed.add_field(name='[ID: 4] Casino Upgrade', value=f"```cs\n${casino_upgarde_cost:,d} Gold```", inline=False)

            embed.add_field(name="Wallet",
                            value=f"```cs\n${user.wallet:,d} Gold```", inline=True)
            await ctx.send(embed=embed)

        elif item == '1':
            shield_cost = int(1.5 * (10 ** (user.level + 2)))

            if user.wallet < shield_cost:
                await ctx.send('Insufficient Funds to buy a shield.')
            elif user.shields >= 3:
                embed = discord.Embed(title=f"{ctx.author.display_name} already has max number of shields!", color=discord.Color.red())
                embed.add_field(name="Shields",
                                value=f"```cs\n{str(user.shields)}```", inline=True)
                await ctx.send(embed=embed)
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
            elif user.level >= 5:
                await ctx.send('You have hit the max level. Consider a profession instead.')
            else:
                user.wallet -= level_up_cost
                user.level += 1
                embed = discord.Embed(title=f"{ctx.author.display_name} has leveled up!", color=discord.Color.green())
                embed.add_field(name="Level",
                                value=f"```cs\n{str(user.level)}```", inline=True)
                await ctx.send(embed=embed)

        elif item == '3':
            # Mechanic Earnings
            professions = session.query(Profession).filter_by(user_id=user.id, profession_id=2).all()
            if professions:
                miner_upgrade_cost = 10 ** (miner.level + 4)
            else:
                miner_upgrade_cost = 2 * 10 ** (miner.level + 4)


            if user.wallet < miner_upgrade_cost:
                await ctx.send('Insufficient Funds in wallet to level up Miner.')
            elif miner.level >= 5:
                await ctx.send('You have hit the max level. Consider a profession instead.')
            else:
                user.wallet -= miner_upgrade_cost
                # Update the balance of how much the miner collected since this was last checked
                time_delta = datetime.datetime.now() - miner.last_worked
                minutes = round(time_delta.total_seconds() / 60,0)
                # A miner will gaurantee you a reward at the (miner) level equivalent of doing !work 3 times every hour (30 minutes of the 60 minutes)
                miner.balance += int(3 * (10 ** (miner.level + 2)) * (minutes / 60))
                miner.last_worked = datetime.datetime.now()
                session.commit()
                miner.level += 1
                embed = discord.Embed(title=f"{ctx.author.display_name}'s Miner has leveled up!", color=discord.Color.green())
                embed.add_field(name="Miner Level",
                                value=f"```cs\n{str(miner.level)}```", inline=True)
                await ctx.send(embed=embed)

        elif item == '4':
            casino_upgarde_cost = 10 ** (casino.level + 4)
            if user.wallet < casino_upgarde_cost: 
                await ctx.send('Insufficient Funds in wallet to level up your casino.')
            else:
                user.wallet -= casino_upgarde_cost
                casino.level += 1
                tax_rate = get_tax(casino.level)
                embed = discord.Embed(title=f"{ctx.author.display_name}'s Casino has leveled up!", color=discord.Color.green())
                embed.add_field(name="New Tax Rate",
                                value=f"```cs\n{tax_rate:.0%} Tax```", inline=True)
                await ctx.send(embed=embed)
        else:
            await ctx.send('Item not in shop.')

    session.commit()

@bot.command(name='prof', aliases=["profession"], help='Specialize in professions.')
async def profession(ctx, item=None):
    user = session.query(User).filter_by(name=ctx.author.name).first()
    
    if not user:
        await ctx.send('User not found.')
    else:

        miner = session.query(Miner).filter_by(user_id=user.id).first()

        if not item:
            embed = discord.Embed(title=f"{ctx.author.display_name}'s Profession Shop", color=discord.Color.random())
            embed.add_field(name='Profession', value=f"A profession costs a user and miner level of 5. \n You will be reset to level 1 once you specialize.", inline=False)
            
            embed.add_field(name='[ID: 2] The Mechanic', value=f"- Your miner collects gold at a 2x rate \n \
                                                          - The boosted gold goes straight to your wallet\n \
                                                          - Cost to upgrade the miner is reduced by half", inline=False)

            embed.add_field(name='[ID: 3] The Jewel Crafter', value=f"- Own your own diamond permanently", inline=False)

            embed.add_field(name='Buying', value=f"To specialize, enter the id in this command. Example:\n .prof 1", inline=False)
            
            await ctx.send(embed=embed)

        elif item == '2':
            if user.level < 5 or miner.level < 5:
                await ctx.send("You need a user and miner level of 5 to buy this.")
            elif session.query(Profession).filter_by(user_id=user.id, profession_id=2).first():
                await ctx.send("You already have this profession.")
            else:
                user.level = 1
                miner.level = 1
                profession = Profession(
                    user_id=user.id,
                    profession_id=2
                )
                user.wallet = 0
                user.bank = 0
                miner.balance = 0
                session.add(profession)
                session.commit()
                await ctx.send("Upgrade successful. You are now a Mechanic!")
        elif item == '3':
            if user.level < 5 or miner.level < 5:
                await ctx.send("You need a user and miner level of 5 to buy this.")
            elif session.query(Profession).filter_by(user_id=user.id, profession_id=3).first():
                await ctx.send("You already have this profession.")
            else:
                user.level = 1
                miner.level = 1
                profession = Profession(
                    user_id=user.id,
                    profession_id=3
                )
                user.wallet = 0
                user.bank = 0
                miner.balance = 0
                session.add(profession)
                session.commit()
                await ctx.send("Upgrade successful. You are now a Jewel Crafter!")
        else:
            await ctx.send('Item not in shop.')

@bot.command(name='give', aliases=["t","transfer"], help='Give money to a player.')
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
        await ctx.send("Admin command only")
        # user.wallet -= amount
        # recipient.wallet += amount
        # embed = discord.Embed(title=f"Money Sent!", color=discord.Color.green())
        # embed.add_field(name=f"{recipient.name}'s' Wallet",
        #                 value=f"```cs\n${recipient.wallet:,d} Gold```", inline=True)
        # embed.add_field(name=f"Your Wallet",
        #                 value=f"```cs\n${user.wallet:,d} Gold```", inline=True)
        # await ctx.send(embed=embed)

    session.commit()

@bot.command(name='giveticket', help='Give a ticket to a player (Admin command only)')
async def giveticket(ctx, tagged_user):
    user = session.query(User).filter_by(name=ctx.author.name).first()
    
    members = ctx.message.mentions
    if members:
        member_name = members[0].name

    if not members:
        await ctx.send('You must tag someone to send money to them.')

    recipient = session.query(User).filter_by(name=member_name).first()

    if not recipient:
        await ctx.send('User does not exist. They must create an account by typing !bal')
    
    if user.name == 'Koltzan':
        ticket = Ticket(
            user_id=recipient.id,
            level=recipient.level
        )
        session.add(ticket)
        session.commit()
        
        ticket_count = session.query(Ticket).filter_by(user_id=user.id).count()

        embed = discord.Embed(title=f"Ticket Sent!", color=discord.Color.green())
        embed.add_field(name=f"{recipient.name}'s' Tickets",
                        value=f"```cs\n{ticket_count:,d} Tickets```", inline=True)
        await ctx.send(embed=embed)
        
@bot.command(name='take', help='Take money from a player (admin only command).')
async def take(ctx, tagged_user, amount):
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
        recipient.wallet -= amount
        embed = discord.Embed(title=f"Money Taken!", color=discord.Color.green())
        embed.add_field(name=f"{recipient.name}'s' Wallet",
                        value=f"```cs\n${recipient.wallet:,d} Gold```", inline=True)
        embed.add_field(name=f"Your Wallet",
                        value=f"```cs\n${user.wallet:,d} Gold```", inline=True)
        await ctx.send(embed=embed)

    session.commit()

@bot.command(name='setlevel', help='Admin command only.')
async def setlevel(ctx, tagged_user, amount):
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
        embed = discord.Embed(title=f"Level Set for {recipient.name}", color=discord.Color.green())
        recipient.level = amount
        embed.add_field(name=f"{recipient.name}'s' Level",
                        value=f"```cs\n{recipient.level:,d}```", inline=True)
        await ctx.send(embed=embed)
    
    else:
        await ctx.send("Admin command only")

    session.commit()

@bot.command(name='setcasinolevel', help='Admin command only.')
async def setcasinolevel(ctx, tagged_user, amount):
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
        embed = discord.Embed(title=f"Casino Level Set for {recipient.name}", color=discord.Color.green())
        casino = session.query(Casino).filter_by(user_id=recipient.id).first()
        casino.level = amount
        embed.add_field(name=f"{recipient.name}'s' Level",
                        value=f"```cs\n{casino.level:,d}```", inline=True)
        await ctx.send(embed=embed)
    else:
        await ctx.send("Admin command only")

    session.commit()

@bot.command(name='setminerlevel', help='Admin command only.')
async def setminerlevel(ctx, tagged_user, amount):
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
        embed = discord.Embed(title=f"Miner Level Set for {recipient.name}", color=discord.Color.green())
        miner = session.query(Miner).filter_by(user_id=recipient.id).first()
        miner.level = amount
        embed.add_field(name=f"{recipient.name}'s' Level",
                        value=f"```cs\n{miner.level:,d}```", inline=True)
        await ctx.send(embed=embed)
    else:
        await ctx.send("Admin command only")

    session.commit()

@bot.command(name='givediamond', help='Admin command only.')
async def givediamond(ctx, tagged_user):
    user = session.query(User).filter_by(name=ctx.author.name).first()
    
    members = ctx.message.mentions
    if members:
        member_name = members[0].name

    if not members:
        await ctx.send('You must tag someone to send money to them.')

    recipient = session.query(User).filter_by(name=member_name).first()

    if not recipient:
        await ctx.send('User does not exist. They must create an account by typing !bal')
    
    if user.name == 'Koltzan':
        embed = discord.Embed(title=f"Diamond given to: {recipient.name}", color=discord.Color.green())
        recipient.diamond = True
        session.commit()
        embed.add_field(name=f"Result",
                        value=f"A new King has arrived.", inline=True)
        await ctx.send(embed=embed)
    
    else:
        await ctx.send("Admin command only")

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
        rob_user = False
        time_delta = datetime.datetime.now() - user.last_rob
        minutes = round(time_delta.total_seconds() / 60,0)

        if minutes > 20:
            rob_user = True
            user.last_rob = datetime.datetime.now()
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
            else:
                user.wallet -= 1500
                embed = discord.Embed(title=f"{recipient.name} got away!", color=discord.Color.red())
                embed.add_field(name=f"Amount Stolen",
                                value=f"```cs\n${0} Gold```", inline=False)
                await ctx.send(embed=embed)

    session.commit()

@bot.command(name='steal', help='Steal the diamond from a player.')
async def steal(ctx, tagged_user):
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
    
    steal_cost = int(10 ** (user.level + 2))

    if user.wallet <  steal_cost:
        await ctx.send(f"You need at least {steal_cost} Gold to rob someone")
    elif recipient.diamond == False:
        await ctx.send("User doesn't have the diamond dumbass..")
    else:
        rob_result = random.randint(1,10)
        user.wallet -= 10 ** (user.level + 2)
        if rob_result == 10:
            user.diamond = True
            recipient.diamond = False
            embed = discord.Embed(title=f"You Robbed the Diamond off of {recipient.name}!!", color=discord.Color.green())
            embed.add_field(name=f"Diamond Owner",
                            value=f"```cs\n{user.name}```", inline=True)
            embed.add_field(name=f"Result",
                            value=f"A new King has arrived.", inline=True)
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title=f"You failed to rob the diamond off of {recipient.name}", color=discord.Color.red())
            embed.add_field(name=f"Result",
                            value=f"Don't fuck with the king.", inline=True)
            await ctx.send(embed=embed)

    session.commit()

@bot.command(name='deposit', aliases=["d"],  help='Deposit money to your bank.')
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

@bot.command(name='withdraw', aliases=["w"], help='Withdraw money to your bank.')
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

@bot.command(name='leaderboard', aliases=["lb"], help='Leaderboards.')
async def leaderboard(ctx, board_type: str):

    if board_type not in ['wallet', 'bank', 'level']:
        await ctx.send('Command should have an argument of wallet, bank, or level. Example: .leaderboard wallet')

    else:
        embed = discord.Embed(title=f"Leaderboards by {board_type}", color=discord.Color.green())
        if board_type == 'wallet':
            users = session.query(User).order_by(User.wallet.desc()).limit(5).all()
            for idx, user in enumerate(users):
                if idx == 0:
                    embed.add_field(name=f"{idx+1}. {user.name} :crown:", value=f"```cs\n${user.wallet:,d} Gold```", inline=False)
                else:
                    embed.add_field(name=f"{idx+1}. {user.name}", value=f"```cs\n${user.wallet:,d} Gold```", inline=False)
        elif board_type == 'bank':
            users = session.query(User).order_by(User.bank.desc()).limit(5).all()
            for idx, user in enumerate(users):
                if idx == 0:
                    embed.add_field(name=f"{idx+1}. {user.name} :crown:", value=f"```cs\n${user.bank:,d} Gold```", inline=False)
                else:
                    embed.add_field(name=f"{idx+1}. {user.name}", value=f"```cs\n${user.bank:,d} Gold```", inline=False)
        elif board_type == 'level':
            users = session.query(User).order_by(User.level.desc()).limit(5).all()
            for idx, user in enumerate(users):
                if idx == 0:
                    embed.add_field(name=f"{idx+1}. {user.name} :crown:", value=f"```cs\nLevel {user.level:,d}```", inline=False)
                else:
                    embed.add_field(name=f"{idx+1}. {user.name}", value=f"```cs\nLevel {user.level:,d}```", inline=False)
        await ctx.send(embed=embed)

@bot.command(name='cmd', aliases=["commands"], help='Bot Commands.')
async def commands(ctx):
    embed = discord.Embed(title=f"Bot Commands", color=discord.Color.green())
    embed.add_field(name="bal", value="Check your balance or create your account.", inline=False)
    embed.add_field(name="buy", value="Buy some stuff. Format: .buy ItemId", inline=False)
    embed.add_field(name="flip", value="Play a coin toss to double your money. Format: .flip Amount.", inline=False)
    embed.add_field(name="rps", value="Play Rock Paper Scissors. Format: .rps Amount r/p/s", inline=False)
    embed.add_field(name="dice", value="Play Dice. Format: .dice Amount 1-6", inline=False)
    embed.add_field(name="roll", value="Roll against the bot (1 to 100)", inline=False)
    embed.add_field(name="blackjack", value="Play Blackjack!", inline=False)
    embed.add_field(name="highlow", value="Play High Low! Required Level 4 and minimum bet 2M. Format: .hl 2m", inline=False)
    embed.add_field(name="roulette", value="Play Roulette!", inline=False)
    embed.add_field(name="give", value="Give money to a player. Format: .give @Player Amount.", inline=False)
    embed.add_field(name="rob", value="Rob the shit out of a player. Format: .rob @Player", inline=False)
    embed.add_field(name="steal", value="Steal the diamond from the diamond holder. Format: .steal @Player", inline=False)
    embed.add_field(name="challenge", value="Challenge a player to a roll. Format: .challenge @Player Amount", inline=False)
    embed.add_field(name="flowerpoker", value="Challenge a player to flower poker. Format: .challenge @Player Amount or .challenge Amount", inline=False)
    embed.add_field(name="work", value="Work for some money. Level up to get more money.", inline=False)
    embed.add_field(name="hourly", value="Make money every hour.", inline=False)
    embed.add_field(name="miner", value="Check the status of your miner.", inline=False)
    embed.add_field(name="collect", value="Collect money from your miner.", inline=False)
    embed.add_field(name="ticket", value="Check your tickets or roll a ticket. Format: .ticket roll", inline=False)
    embed.add_field(name="leaderboard", value="Check leaderboards by wallet, level, bank. Format: .leaderboard wallet", inline=False)
    await ctx.send(embed=embed)

# Helper Functions
def create_casino(user):
    casino = Casino(
        
        user_id=user.id,
        level=1,
        balance=0
    )
    session.add(casino)
    session.commit()

    return casino

def validate_bet(bet):
    bet = bet.replace('k', '000').replace('K','000').replace('m','000000').replace('M','000000').replace('b','000000000').replace('B','000000000')

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
        shields=0,
        diamond=False,
        last_work=datetime.datetime.min,
        last_hourly=datetime.datetime.min,
        last_daily=datetime.datetime.min,
        last_rob=datetime.datetime.min
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

    casino = Casino(
        user_id=user.id,
        level=1,
        balance=0
    )
    session.add(casino)
    session.commit()

    user.casino = casino.id
    session.commit()


    return user

rps_moves = {
    0: 'Rock',
    1: 'Paper',
    2: 'Scissors'
}

miner_level_urs = {
    1: 'https://i.pinimg.com/originals/75/61/5a/75615a37309f44c6f07353277429a4f2.png',
    2: 'https://static.wikia.nocookie.net/leagueoflegends/images/9/96/Season_2019_-_Gold_1.png',
    3: 'https://static.wikia.nocookie.net/leagueoflegends/images/7/74/Season_2019_-_Platinum_1.png',
    4: 'https://i.pinimg.com/originals/6a/10/c7/6a10c7e84c9f4e4aa9412582d28f3fd2.png',
    5: 'https://i.pinimg.com/originals/69/61/ab/6961ab1af799f02df28fa74278d78120.png',
    6: 'https://static.wikia.nocookie.net/leagueoflegends/images/5/58/Season_2019_-_Grandmaster_2.png',
    7: 'https://static.wikia.nocookie.net/leagueoflegends/images/5/5f/Season_2019_-_Challenger_1.png'
}

flowers = [
    '<:assorted_flowers:928494518658007110>',
    '<:blue_flowers:928494731489574923>',
    '<:orange_flowers:928494782127419394>',
    '<:mixed_flowers:928494829132980315>',
    '<:purple_flowers:928494904554975273>',
    '<:red_flowers:928494952642670673>',
    '<:yellow_flowers:928495038248402945>'
]

profession_badges = {
    1: 'Thief :moneybag:',
    2: 'Mechanic :pick:',
    3: 'Jewel Crafter :diamond_shape_with_a_dot_inside:',
    4: 'Terrorist :bomb:'
}

def get_tax(level):
    return 0# 0.02*(level)+0.05

osrs_gp_url = 'https://oldschool.runescape.wiki/images/Coins_detail.png?404bc'

bot.run(TOKEN)