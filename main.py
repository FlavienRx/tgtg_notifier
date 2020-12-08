#  -*- coding: utf-8 -*-

import os
import sqlite3
from datetime import datetime, timedelta

import pytz
import requests
import sentry_sdk
import slack
import telegram
from dotenv import load_dotenv
from emoji import emojize
from tgtg import TgtgClient
from tgtg.exceptions import TgtgAPIError

from user import USERS


load_dotenv()

if os.environ.get('SENTRY_SDK_URL'):
    sentry_sdk.init(
        os.environ.get('SENTRY_SDK_URL'),
        traces_sample_rate=1.0
    )

base_path = os.path.dirname(os.path.realpath(__file__))
db = sqlite3.connect(os.path.join(base_path, "database.db"))
db.row_factory = sqlite3.Row
cursor = db.cursor()

# Create favorite_stores table if not exists
cursor.execute(
    "CREATE TABLE IF NOT EXISTS favorite_stores (user_id int, store_name text, nb_item int)"
)

local_tz = pytz.timezone('Europe/Paris')
now = datetime.now(local_tz)

for USER in USERS:
    # login with too good to go token
    tgtg_client = TgtgClient(
        access_token=USER['tgtg_token'],
        user_id=USER['tgtg_user_id']
    )

    # You can then get items (as default it will get your favorites)
    stores = tgtg_client.get_items()

    if USER['send_notif_on'] == 'slack':
        slack_client = slack.WebClient(token=USER['slack_token'])

    elif USER['send_notif_on'] == 'telegram':
        telegram_bot = telegram.Bot(token=USER['telegram_token'])

    elif USER['send_notif_on'] == 'discord':
        pass

    # Get user favorite stores
    cursor.execute(
        "SELECT * FROM favorite_stores WHERE user_id=?",
        (USER['tgtg_user_id'],)
    )
    favorite_stores = cursor.fetchall()

    for store in stores:
        if store['items_available'] > 0:
            for favorite_store in favorite_stores:
                if (
                    favorite_store['store_name'] == store['store']['store_name']
                    and favorite_store['nb_item'] == 0
                ):

                    # Get UTC pickup date
                    pickup_from_utc = datetime.strptime(
                        store['pickup_interval']['start'],
                        '%Y-%m-%dT%H:%M:00Z'
                    )
                    pickup_latest_utc = datetime.strptime(
                        store['pickup_interval']['end'],
                        '%Y-%m-%dT%H:%M:00Z'
                    )

                    # Translate pickup date in local datetime
                    pickup_from = pickup_from_utc.replace(
                        tzinfo=pytz.utc
                    ).astimezone(local_tz)
                    pickup_latest = pickup_latest_utc.replace(
                        tzinfo=pytz.utc
                    ).astimezone(local_tz)

                    tomorrow_date = now.date() + timedelta(days=1)
                    day = None

                    # Convert pickup date
                    if pickup_from.date() == now.date() and pickup_latest.date() == now.date():
                        day = 'today'

                    elif pickup_from.date() == tomorrow_date and pickup_latest.date() == tomorrow_date:
                        day = 'tomorrow'

                    elif pickup_from.date() == pickup_latest.date():
                        day = pickup_from.strftime("%d-%m-%Y")

                    # If same pickup day
                    if day:
                        text = '{} new item(s) in {}, pickup {} between {} and {}'.format(
                                store['items_available'],
                                store['store']['store_name'],
                                day,
                                pickup_from.strftime("%H:%M"),
                                pickup_latest.strftime("%H:%M"),
                            )

                    # Else different pickup day
                    else:
                        text = '{} new item(s) in {}, pickup between {} and {}'.format(
                                store['items_available'],
                                store['store']['store_name'],
                                pickup_from.strftime("%d-%m-%Y %H:%M"),
                                pickup_latest.strftime("%d-%m-%Y %H:%M"),
                            )

                    # Send notif on Slack
                    if USER['send_notif_on'] == 'slack':
                        slack_client.chat_postMessage(
                            channel=USER['slack_user_id'],
                            text= ':sandwich: {}'.format(text)
                        )

                    # Send notif on Telegram
                    elif USER['send_notif_on'] == 'telegram':
                        telegram_bot.send_message(
                            chat_id=USER['telegram_chan_id'],
                            text=emojize(':hamburger: {}'.format(text))
                        )

                    # Send notif on Discord
                    elif USER['send_notif_on'] == 'discord':
                        data = {'content': ':sandwich: {}'.format(text)}
                        requests.post(USER['discord_webhook_url'], data=data)

        # Update or create favorite store
        cursor.execute(
            """INSERT OR REPLACE
            INTO favorite_stores(user_id, store_name, nb_item)
            VALUES(?, ?, ?)""", (
                USER['tgtg_user_id'],
                store['store']['store_name'],
                store['items_available']
            )
        )
        # Save (commit) the changes
        db.commit()
