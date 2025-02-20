import os
import time
import json  # ✅ Make sure this is here
import requests
import telebot

# Load environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# API URLs
DEX_API_URL = "https://api.dexscreener.com/latest/dex/pairs/base/0x6d6391b9bd02eefa00fa711fb1cb828a6471d283"
CMC_API_URL = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
CMC_HEADERS = {"X-CMC_PRO_API_KEY": os.getenv("CMC_API_KEY")}
CMC_PARAMS = {"symbol": "WETH", "convert": "USDC"}

# Initialize Telegram bot
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Price alert levels
alert_levels = [0.1050, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 1.00]
alert_triggered = {level: False for level in alert_levels}

def get_ski_price():
    """Fetches SKI/WETH price from DEX Screener API."""
    try:
        response = requests.get(DEX_API_URL)
        data = response.json()
        print("🚀 DEX Screener API Response:", json.dumps(data, indent=4))  # Debugging
        ski_weth_price = float(data["pair"]["priceNative"])  # ✅ Corrected SKI/WETH price
        return ski_weth_price
    except Exception as e:
        print(f"❌ Error fetching SKI price: {e}")
        return None

def get_weth_usdc_price():
    """Fetches WETH/USDC price from CoinMarketCap API."""
    try:
        response = requests.get(CMC_API_URL, params=CMC_PARAMS, headers=CMC_HEADERS)
        data = response.json()
        print("🌍 CoinMarketCap API Response:", json.dumps(data, indent=4))  # Debugging
        if "data" in data and "WETH" in data["data"]:
            weth_usdc_price = float(data["data"]["WETH"]["quote"]["USDC"]["price"])  # ✅ Corrected
            return weth_usdc_price
        else:
            print("❌ Error: Invalid response structure from CoinMarketCap API")
            return None
    except Exception as e:
        print(f"❌ Error fetching WETH/USDC price: {e}")
        return None

def send_telegram_alert(price):

    """Send Telegram notification when SKI hits target price"""
    if isinstance(price, (int, float)):  
    	message = f"🚨 SKI Price Alert! SKI has reached ${price:.2f} USDC 🚀"
    else:
    	message = price  # Keep the full message if it's already formatted
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

# Track the last recorded SKI price
last_price = None
percentage_alerts_triggered = set()
price_alerts_triggered = set()
last_hourly_update = time.time()  # Track last hourly update

def main():
    global last_price, last_hourly_update

    while True:
        ski_weth = get_ski_price()
        weth_usdc = get_weth_usdc_price()

        if ski_weth is not None and weth_usdc is not None:
            ski_usdc = ski_weth * weth_usdc  # Convert SKI/WETH to SKI/USDC
            print(f"📢 Current SKI price: ${ski_usdc:.4f} USDC")

            if last_price is None:
                last_price = ski_usdc  # Set initial price
                continue  # Skip first iteration

            # ✅ Check for 5% Up/Down moves
            percentage_change = ((ski_usdc - last_price) / last_price) * 100
            percentage_level = round(percentage_change / 5) * 5
            if abs(percentage_change) >= 5 and percentage_level not in percentage_alerts_triggered:
                send_telegram_alert(f"🚀 SKI price is {percentage_level}% {'up' if percentage_change > 0 else 'down'}! Current price: ${ski_usdc:.4f} USDC")
                percentage_alerts_triggered.add(percentage_level)

            # ✅ Check for every $0.05 movement
            price_level = round(ski_usdc / 0.05) * 0.05
            if price_level not in price_alerts_triggered:
                send_telegram_alert(f"📊 SKI price moved to ${ski_usdc:.4f} USDC")
                price_alerts_triggered.add(price_level)

            # ✅ Send hourly update (even if no price change)
            if time.time() - last_hourly_update >= 3600:  # 3600 seconds = 1 hour
                send_telegram_alert(f"🕒 Hourly Update: SKI price is ${ski_usdc:.4f} USDC")
                last_hourly_update = time.time()  # Reset hourly timer

            last_price = ski_usdc  # Update last known price

        time.sleep(30)  # Check price every 30 seconds

if __name__ == "__main__":
    main()
