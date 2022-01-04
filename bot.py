# bot.py
import asyncio
import os
import random
import datetime

import discord
from discord import client
from discord.ext import commands
from dotenv import load_dotenv

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import false

from models import Hourly, Miner, Rob, Ticket, Timestamp, User
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

@bot.command(name='flip', aliases=["f"], help='Do a 50-50 to double your money.')
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

        # Roll for the change at a ticket
        if bet > int(0.5* 10**(user.level+2)):
            embed = roll_ticket()
            if embed:
                await ctx.send(embed=embed)

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

        # Roll for the change at a ticket
        if bet > int(0.5* 10**(user.level+2)):
            embed = roll_ticket()
            if embed:
                await ctx.send(embed=embed)

        bot_bet = random.randint(1,6)
        win = False
        if bot_bet == dice_bet:
            win = True

        if win:
            user.wallet += 5*bet
            embed = discord.Embed(title='Dice', color=discord.Color.green())
            embed.add_field(name=f'{ctx.author.display_name}', value="Holy shit You Won ^.^! :thumbsup:", inline=False)
            embed.add_field(name="Winnings",
                            value=f"```cs\n${5*bet:,d} Gold```", inline=False)
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
        if bet > int(0.5* 10**(user.level+2)):
            embed = roll_ticket()
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
            user.wallet += 35*bet
            embed = discord.Embed(title='Roulette BIG WIN', color=discord.Color.green())
            embed.add_field(name=f'{ctx.author.display_name}', value="Holy shit You Won the major Prize!! ^.^! :thumbsup:", inline=False)
            embed.add_field(name="Roulette Table", value=f"{number} :green_circle:", inline=True)
            embed.add_field(name="Earning",
                            value=f"```cs\n${35*bet:,d} Gold```", inline=False)
            embed.add_field(name="Wallet",
                            value=f"```cs\n${user.wallet:,d} Gold```", inline=False)
            embed.set_thumbnail(url='https://previews.123rf.com/images/hobbitfoot/hobbitfoot1709/hobbitfoot170900484/85929770-big-win-roulette-signboard-game-banner-design-.jpg')
            await ctx.send(embed=embed)
        elif win:
            user.wallet += bet
            embed = discord.Embed(title='Roulette Win!', color=discord.Color.green())
            embed.add_field(name=f'{ctx.author.display_name}', value="You win! :thumbsup:", inline=False)
            embed.add_field(name="Roulette Table", value=f"{number} {table_color}", inline=True)
            embed.add_field(name="Earning",
                            value=f"```cs\n${bet:,d} Gold```", inline=False)
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
        
        if reply.content in ['yes', 'y']:
            
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

    bet = validate_bet(bet)

    if not bet:
        await ctx.send("Invalid bet. Format's Available: 1, 1k, 1K, 1m, 1M")
        return
    
    if bet > user.wallet:
        await ctx.send('Insufficient Funds.')
    else:

        # Roll for the change at a ticket
        if bet > int(0.5* 10**(user.level+2)):
            embed = roll_ticket()
            if embed:
                await ctx.send(embed=embed)

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

def author_check(author):
    return lambda message: message.author == author

def roll_ticket(user: User):
    roll = random.randint(100)
    ticket = session.query(Ticket).filter_by(user_id=user.id).first()

    if not ticket:
        ticket = Ticket(
            user_id=id,
            tickets=0
        )
        session.commit()

    if roll == 100:
        ticket.tickets += 1
        session.commit()
        embed = discord.Embed(title='Ticket Winner!', color=discord.Color.green())
        embed.add_field(name=f'You just won a Ticket!', value=f"Congrats! $_$", inline=False)
        embed.add_field(name="Tickets",
            value=f"```cs\n${ticket.tickets:,d} Tickets```", inline=False)
        embed.set_thumbnail(url='https://upload.wikimedia.org/wikipedia/commons/a/a9/Scratch_game.jpg')
        return embed

    return False

@bot.command(name='ticket', help='Check your tickets. Or do .ticket roll to Roll a ticket.')
async def ticket(ctx, roll=None):
    # Query if User exists
    user = session.query(User).filter_by(name=ctx.author.name).first()
    ticket = session.query(Ticket).filter_by(user_id=user.id).first()

    if not user:
        await ctx.send('User does not exist. Type .bal to create an account.')
        return

    if not ticket:
        ticket = Ticket(
            user_id=user.id,
            tickets=0
        )
        session.add(ticket)
        session.commit()

    if not roll:
        embed = discord.Embed(title=f'Tickets', color=discord.Color.green())
        embed.add_field(name="Tickets",
            value=f"```cs\n{ticket.tickets:,d} Tickets```", inline=False)
        await ctx.send(embed=embed)
    else:
        if roll == 'roll' and ticket.tickets > 0:
            ticket.tickets -= 1
            session.commit()
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
                user.wallet += int(10**(user.level + 3))
                session.commit()
                embed = discord.Embed(title='Big Win!', color=discord.Color.green())
                embed.add_field(name=f'You won a BIG prize!', value=f"EZ MONEY", inline=False)
                embed.add_field(name="Earnings",
                    value=f"```cs\n${int(10**(user.level + 3)):,d} Gold```", inline=False)
                embed.add_field(name="Wallet",
                    value=f"```cs\n${user.wallet:,d} Gold```", inline=False)
                embed.set_thumbnail(url='https://www.reviewjournal.com/wp-content/uploads/2015/10/thinkstockphotos-492226002_1.jpg')
                await ctx.send(embed=embed)
            elif dice > 40:
                user.wallet += int(0.5 * 10**(user.level + 3))
                session.commit()
                embed = discord.Embed(title='Big Win!', color=discord.Color.green())
                embed.add_field(name=f'You won a Common prize!', value=f"EZ MONEY", inline=False)
                embed.add_field(name="Earnings",
                    value=f"```cs\n${int(0.5 * 10**(user.level + 3)):,d} Gold```", inline=False)
                embed.add_field(name="Wallet",
                    value=f"```cs\n${user.wallet:,d} Gold```", inline=False)
                embed.set_thumbnail(url='https://www.reviewjournal.com/wp-content/uploads/2015/10/thinkstockphotos-492226002_1.jpg')
                await ctx.send(embed=embed)
            else:
                user.wallet += int(2 * 10**(user.level + 2))
                session.commit()
                embed = discord.Embed(title='Minor Win!', color=discord.Color.green())
                embed.add_field(name=f'You won a Minor prize!', value=f"Fair enough", inline=False)
                embed.add_field(name="Earnings",
                    value=f"```cs\n${int(2 * 10**(user.level + 2)):,d} Gold```", inline=False)
                embed.add_field(name="Wallet",
                    value=f"```cs\n${user.wallet:,d} Gold```", inline=False)
                embed.set_thumbnail(url='https://www.reviewjournal.com/wp-content/uploads/2015/10/thinkstockphotos-492226002_1.jpg')
                await ctx.send(embed=embed)
        if roll == 'roll' and ticket.tickets == 0:
            await ctx.send('Not enough tickets buddy.')     
        else:
            await ctx.send("Invalid Command.")


@bot.command(name='blackjack', aliases=["bj"], help='Roll against the bot.')
async def blackjack(ctx, bet: str):
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

        # Roll for the change at a ticket
        if bet > int(0.5* 10**(user.level+2)):
            embed = roll_ticket()
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
            user.wallet += int(2.5*bet)
            new_embed = discord.Embed(title='Blackjack - Win!', color=discord.Color.green())
            new_embed.add_field(name=f'Your Hand', value=f"{player_cards_display}", inline=False)
            new_embed.add_field(name=f'Total', value=f"```cs\n{player_score}```", inline=False)
            new_embed.add_field(name=f"Bot's Hand", value=f"{dealer_cards_display}", inline=False)
            new_embed.add_field(name=f'Total', value=f"```cs\n{dealer_score}```", inline=False)
            new_embed.add_field(name="Result",
                value=f"BLACKJACK! ^.^", inline=False)
            new_embed.add_field(name="Earnings",
                value=f"```cs\n${int(2.5*bet):,d} Gold```", inline=False)
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
            user.wallet += 2*bet
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

        # Roll for the change at a ticket
        if bet > int(0.5* 10**(user.level+2)):
            embed = roll_ticket()
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
            user.wallet -= bet
            embed = discord.Embed(title='Rock Paper Scissors', color=discord.Color.red())
            embed.add_field(name=f'{ctx.author.display_name}', value="Draw!", inline=False)
            embed.add_field(name="Your Move", value=f"```{rps}```", inline=True)
            embed.add_field(name="Bot's Move", value=f"```{bot_move}```", inline=True)
            embed.add_field(name="Wallet",
                            value=f"```cs\n${user.wallet:,d} Gold```", inline=False)
            await ctx.send(embed=embed)

        elif win:
            user.wallet += 2*bet
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

@bot.command(name='hourly', aliases=["h"], help='Make some money every hour.')
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

@bot.command(name='buy', aliases=["shop"], help='Buy some stuff.')
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
            else:
                user.wallet -= level_up_cost
                user.level += 1
                embed = discord.Embed(title=f"{ctx.author.display_name} has leveled up!", color=discord.Color.green())
                embed.add_field(name="Level",
                                value=f"```cs\n{str(user.level)}```", inline=True)
                await ctx.send(embed=embed)

        elif item == '3':
            miner_upgrade_cost = 2 * 10 ** (miner.level + 4)
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
        user.wallet -= amount
        recipient.wallet += amount
        embed = discord.Embed(title=f"Money Sent!", color=discord.Color.green())
        embed.add_field(name=f"{recipient.name}'s' Wallet",
                        value=f"```cs\n${recipient.wallet:,d} Gold```", inline=True)
        embed.add_field(name=f"Your Wallet",
                        value=f"```cs\n${user.wallet:,d} Gold```", inline=True)
        await ctx.send(embed=embed)

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
        ticket = session.query(Ticket).filter_by(user_id=recipient.id).first()
        if not ticket:
            ticket = Ticket(
                user_id=recipient.id,
                tickets=0
            )
            session.add(ticket)
            session.commit()

        ticket.tickets += 1
        session.commit()

        embed = discord.Embed(title=f"Ticket Sent!", color=discord.Color.green())
        embed.add_field(name=f"{recipient.name}'s' Tickets",
                        value=f"```cs\n{ticket.tickets:,d} Tickets```", inline=True)
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
    embed.add_field(name="roulette", value="Play Roulette!", inline=False)
    embed.add_field(name="give", value="Give money to a player. Format: .give @Player Amount.", inline=False)
    embed.add_field(name="rob", value="Rob the shit out of a player. Format: .rob @Player", inline=False)
    embed.add_field(name="challenge", value="Challenge a player to a roll. Format: .challenge @Player Amount", inline=False)
    embed.add_field(name="work", value="Work for some money. Level up to get more money.", inline=False)
    embed.add_field(name="hourly", value="Make $5000 every hour.", inline=False)
    embed.add_field(name="miner", value="Check the status of your miner.", inline=False)
    embed.add_field(name="collect", value="Collect money from your miner.", inline=False)
    embed.add_field(name="ticket", value="Check your tickets or roll a ticket. Format: .ticket roll", inline=False)
    embed.add_field(name="leaderboard", value="Check leaderboards by wallet, level, bank. Format: .leaderboard wallet", inline=False)
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