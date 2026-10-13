import requests
import time
import schedule
import json
import re
from bs4 import BeautifulSoup
from datetime import datetime
import random

# Your Discord webhook URL
WEBHOOK_URL = "https://discord.com/api/webhooks/1559596988977123360/-qNIwnMBLKGgXnBuDqQNb_Lo6t3c5CqdChwR2lBBJm2qn9eKT_ha9ebtdHbPnJ3SkgIu"

# Multiple account sources - rotating to avoid detection
SOURCES = [
    {
        'url': 'https://auradroppers.com/',
        'type': 'html',
        'selectors': [r'[\w.+-]+@[\w-]+\.[\w.-]+:[^\s]+', r'[A-Za-z0-9_]+:[A-Za-z0-9!@#$%^&*()_+-=]+'],
        'fallback_path': '/api/accounts'
    },
    {
        'url': 'https://accountdrops.com/',
        'type': 'html',
        'selectors': [r'[\w.+-]+@[\w-]+\.[\w.-]+:[^\s]+'],
        'fallback_path': '/drops'
    },
    {
        'url': 'https://freeaccs.net/',
        'type': 'html',
        'selectors': [r'[\w.+-]+@[\w-]+\.[\w.-]+:[^\s]+'],
        'fallback_path': '/free'
    },
    {
        'url': 'https://accountgiveaway.com/',
        'type': 'html',
        'selectors': [r'[\w.+-]+@[\w-]+\.[\w.-]+:[^\s]+'],
        'fallback_path': '/giveaway'
    },
    {
        'url': 'https://genaccounts.com/',
        'type': 'html',
        'selectors': [r'[\w.+-]+@[\w-]+\.[\w.-]+:[^\s]+'],
        'fallback_path': '/generator'
    }
]

def scrape_source(source):
    """Scrape accounts from a single source"""
    accounts = []
    headers = {
        'User-Agent': random.choice([
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'
        ]),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': source['url'],
        'DNT': '1'
    }
    
    try:
        # Try main page first
        response = requests.get(source['url'], headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        page_text = soup.get_text()
        
        # Try each regex pattern
        for pattern in source['selectors']:
            matches = re.findall(pattern, page_text)
            accounts.extend(matches)
        
        # If no accounts found, try API endpoints
        if not accounts and 'fallback_path' in source:
            try:
                api_url = source['url'].rstrip('/') + source['fallback_path']
                api_response = requests.get(api_url, headers=headers, timeout=10)
                if api_response.status_code == 200:
                    # Try JSON
                    try:
                        data = api_response.json()
                        if isinstance(data, list):
                            for item in data:
                                if isinstance(item, str) and ':' in item:
                                    accounts.append(item)
                                elif isinstance(item, dict):
                                    user = item.get('username', item.get('email', item.get('user', '')))
                                    pwd = item.get('password', item.get('pass', ''))
                                    if user and pwd:
                                        accounts.append(f"{user}:{pwd}")
                    except:
                        # Try text
                        text_matches = re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+:[^\s]+', api_response.text)
                        accounts.extend(text_matches)
            except:
                pass
        
        # Try to find hidden JSON data in scripts
        if not accounts:
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    # Look for account arrays or objects
                    json_matches = re.findall(r'\{[^}]*"account[^}]*\}', script.string, re.IGNORECASE)
                    for match in json_matches:
                        try:
                            data = json.loads(match)
                            if isinstance(data, dict):
                                user = data.get('username', data.get('email', data.get('user', '')))
                pwd = data.get('password', data.get('pass', ''))
                if user and pwd:
                    accounts.append(f"{user}:{pwd}")
        except:
            pass

except:
    pass

return accounts[:8]  # Max 8 per source

except Exception as e:
print(f"Source error ({source['url']}): {str(e)[:50]}")
return []

def scrape_all_accounts():
"""Scrape from all sources and combine"""
all_accounts = []
used_sources = random.sample(SOURCES, min(3, len(SOURCES)))  # Use 3 random sources each time

for source in used_sources:
    print(f"Scraping: {source['url']}")
    accounts = scrape_source(source)
    if accounts:
        print(f"  Found {len(accounts)} accounts")
        all_accounts.extend(accounts)
    time.sleep(1)  # Delay between sources

# Shuffle to mix sources
random.shuffle(all_accounts)

# Remove duplicates while preserving order
seen = set()
unique_accounts = []
for acc in all_accounts:
    if acc not in seen:
        seen.add(acc)
        unique_accounts.append(acc)

return unique_accounts[:12]  # Return up to 12 unique accounts

def send_discord_webhook(accounts):
"""Send accounts via Discord webhook with clean embed (no source attribution)"""
# Create embed without any source info
embed = {
    "title": "🎉 ACCOUNT DROP 🎉",
    "description": "Fresh accounts available now!",
    "color": 0x00ff00,
    "fields": [],
    "footer": {
        "text": f"Drop • {datetime.now().strftime('%H:%M:%S')}",
        "icon_url": "https://cdn.discordapp.com/embed/avatars/0.png"
    },
    "timestamp": datetime.utcnow().isoformat()
}

# Add accounts to embed
for i, account in enumerate(accounts[:10]):
    if ':' in account:
        parts = account.split(':', 1)
        embed["fields"].append({
            "name": f"Account #{i+1}",
            "value": f"**User:** `{parts[0]}`\n**Pass:** `{parts[1]}`",
            "inline": True
        })
    else:
        embed["fields"].append({
            "name": f"Account #{i+1}",
            "value": f"`{account}`",
            "inline": True
        })

# If more accounts exist
if len(accounts) > 10:
    embed["fields"].append({
        "name": "More available",
        "value": "Check back next drop for more!",
        "inline": False
    })

payload = {
    "embeds": [embed],
    "username": "Account Drop",
    "avatar_url": "https://cdn.discordapp.com/embed/avatars/0.png"
}

headers = {'Content-Type': 'application/json'}

# Add random delay to look natural
time.sleep(random.uniform(0.5, 2.0))

response = requests.post(WEBHOOK_URL, json=payload, headers=headers)

if response.status_code == 204:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Drop sent successfully!")
else:
    print(f"Webhook error: {response.status_code}")

def account_drop_job():
"""Main job - no source info printed"""
print(f"[{datetime.now().strftime('%H:%M:%S')}] Collecting accounts...")
accounts = scrape_all_accounts()
if accounts:
    print(f"Collected {len(accounts)} accounts")
    send_discord_webhook(accounts)
else:
    print("No accounts found, trying again next cycle")

# Schedule every 10 minutes
schedule.every(10).minutes.do(account_drop_job)

# Run immediately
account_drop_job()

print("Account drop bot running. Dropping every 10 minutes.")
print("Press Ctrl+C to stop.")

try:
    while True:
        schedule.run_pending()
        time.sleep(1)
except KeyboardInterrupt:
    print("\nStopped.")
