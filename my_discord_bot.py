import os
import time
import asyncio
import aiohttp
import discord
from discord.ext import tasks, commands

# Set up your bot with intents (necessary for future Discord features)
intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)

# List of standard coins and meme coins
coins = [
    "bitcoin", "ethereum", "ripple", "cardano", "dogecoin", "solana", "litecoin",
    "pepe", "shiba-inu", "stellar", "avalanche-2", "sui", "polkadot", "chainlink",
    "wrapped-bitcoin", "bitcoin-cash", "near", "uniswap", "aptos", "arbitrum",
    "render-token", "tia", "internet-computer", "ethereum-classic", 
    "dai", "wrapped-fantom", "bonk", "filecoin", "optimism", "floki", "immutable-x",
    "grt", "axs", "ldo", "eos", "strk", "mana", "mkr", "ondo", "jasmy", "flow", 
    "xtz", "ens", "ape", "glm", "chz", "crv", "mina", "eigen", "corechain", "qnt", 
    "egld", "blur", "zk", "hnt", "flr", "rose", "snx", "zro", "matic", "aero", 
    "zrx", "akt", "msol", "gmt", "aioz", "waxl", "axl", "kava", "1inch", "lpt"
]

# Function to get prices from CoinGecko asynchronously with retry logic
async def get_prices():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        'ids': ','.join(coins), 
        'vs_currencies': 'usd',
        'include_24hr_vol': 'true'
    }

    async with aiohttp.ClientSession() as session:
        retries = 5
        for attempt in range(retries):
            try:
                async with session.get(url, params=params) as response:
                    response.raise_for_status()  # Will raise exception for HTTP error
                    data = await response.json()
                    return data
            except aiohttp.ClientError as e:
                print(f"Error fetching data (Attempt {attempt+1}/{retries}): {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    return {}  # Return empty dictionary if all attempts fail

# Helper functions for calculations
def calculate_percentage_change(old_price, new_price):
    if old_price == 0 or new_price == 0:
        return 0
    return ((new_price - old_price) / old_price) * 100

# Helper function to get coin details (now includes profit per $100)
async def get_coin_details(coin_list, new_prices, old_prices):
    coin_details = []
    for coin in coin_list:
        if coin in new_prices and coin in old_prices:
            new_price = new_prices[coin]['usd']
            old_price = old_prices[coin]['usd']
            percentage_change = calculate_percentage_change(old_price, new_price)
            profit_per_100_invested = (100 / new_price) * (new_price - old_price)

            support = new_price * 0.95
            resistance = new_price * 1.05
            fibonacci_levels = [new_price * 0.236, new_price * 0.382, new_price * 0.618]
            volume = new_prices[coin].get('usd_24h_vol', 0)

            coin_details.append({
                'coin': coin.capitalize(),
                'new_price': new_price,
                'old_price': old_price,
                'percentage_change': percentage_change,
                'profit_per_100_invested': profit_per_100_invested,
                'support': support,
                'resistance': resistance,
                'fibonacci_levels': fibonacci_levels,
                'volume': volume
            })

    return coin_details

# Helper function to format the coin detail message
def format_coin_detail(coin_detail):
    change = f"{coin_detail['percentage_change']:.2f}%" if coin_detail['percentage_change'] != 0 else "No Change"
    profit = f"${coin_detail['profit_per_100_invested']:.2f}" if coin_detail['profit_per_100_invested'] != 0 else "$0.00"

    return (f"{coin_detail['coin']}:\n"
            f"Price: ${coin_detail['new_price']:.2f}\n"
            f"Change: {change}\n"
            f"Profit per $100 Invested: {profit}\n"
            f"Support: ${coin_detail['support']:.2f}\n"
            f"Resistance: ${coin_detail['resistance']:.2f}\n"
            f"Fibonacci Levels: {coin_detail['fibonacci_levels']}\n"
            f"24h Volume: ${coin_detail['volume']:.2f}\n\n")

# Task to track price changes every 25 minutes
@tasks.loop(minutes=25)
async def track_price_changes():
    old_prices = await get_prices()
    if not old_prices:
        print("Failed to fetch initial prices.")
        return

    print(f"Old prices: {old_prices}")  # Debug print

    await asyncio.sleep(1500)  # 45 minutes in seconds

    new_prices = await get_prices()
    if not new_prices:
        print("Failed to fetch new prices.")
        return

    print(f"New prices: {new_prices}")  # Debug print

    channel = bot.get_channel(1311536640447090769)  # Replace with your Discord channel ID
    if channel is None:
        print("Could not find channel.")
        return

    coin_details = await get_coin_details(coins, new_prices, old_prices)

    # Debug print the coin details before sorting
    print(f"Coin details before sorting: {coin_details}")  # Debug print

    coin_details.sort(key=lambda x: x['percentage_change'], reverse=True)

    top_3_coins_message = "**Top 3 Coins with the Highest Positive Percentage Change**:\n"
    for coin_detail in coin_details[:3]:
        top_3_coins_message += format_coin_detail(coin_detail)

    bottom_3_coins_message = "\n**Top 3 Coins with the Highest Negative Percentage Change**:\n"
    for coin_detail in coin_details[-3:]:
        bottom_3_coins_message += format_coin_detail(coin_detail)

    await send_message_in_chunks(channel, top_3_coins_message)
    await send_message_in_chunks(channel, bottom_3_coins_message)

# Function to send messages in chunks if they exceed Discord's message limit (2000 characters)
async def send_message_in_chunks(channel, message, chunk_size=2000):
    if len(message) > chunk_size:
        for i in range(0, len(message), chunk_size):
            await channel.send(message[i:i + chunk_size])
    else:
        await channel.send(message)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    # Start the task when the bot is ready
    track_price_changes.start()
#python D:\fetch\my_bot_v2.py
