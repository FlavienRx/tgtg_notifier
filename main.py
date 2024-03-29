#  -*- coding: utf-8 -*-

import os
import logging
from datetime import datetime, timedelta

import pytz
import sentry_sdk
from dotenv import load_dotenv
from tgtg import TgtgClient

from db import DbWrapper
from notifier import Notifier


load_dotenv()

logging.basicConfig(encoding="utf-8", level=logging.INFO)

if os.environ.get("SENTRY_SDK_URL"):
    sentry_sdk.init(
        os.environ.get("SENTRY_SDK_URL"),
        traces_sample_rate=1.0,
        environment=os.environ.get("SENTRY_SDK_ENVIRONMENT"),
    )

# Init and open database
db = DbWrapper()
users = db.get_users()

local_tz = pytz.timezone("Europe/Paris")
now = datetime.now(local_tz)

for user in users:
    if not user["access_token"]:
        # login with too good to go token
        logging.info("User {} new login".format(user["email"]))
        tgtg_client = TgtgClient(email=user["email"])

        credentials = tgtg_client.get_credentials()
        db.update_user(
            user["email"],
            credentials["user_id"],
            credentials["access_token"],
            credentials["refresh_token"],
        )

    else:
        tgtg_client = TgtgClient(
            access_token=user["access_token"],
            refresh_token=user["refresh_token"],
            user_id=user["user_id"],
        )

    logging.info("User {}".format(user["email"]))

    # Init user notifier
    notifier = Notifier(user)

    # You can then get items (as default it will get your favorites)
    stores = tgtg_client.get_items()

    # Get user favorite stores
    favorite_stores = db.user_favorite_stores(user["user_id"])

    for store in stores:
        if store["items_available"] > 0:
            for favorite_store in favorite_stores:
                if (
                    favorite_store["store_id"] == store["store"]["store_id"]
                    and favorite_store["nb_item"] == 0
                ):

                    # Get UTC pickup date
                    pickup_from_utc = datetime.strptime(
                        store["pickup_interval"]["start"], "%Y-%m-%dT%H:%M:00Z"
                    )
                    pickup_latest_utc = datetime.strptime(
                        store["pickup_interval"]["end"], "%Y-%m-%dT%H:%M:00Z"
                    )

                    # Translate pickup date in local datetime
                    pickup_from = pickup_from_utc.replace(tzinfo=pytz.utc).astimezone(
                        local_tz
                    )
                    pickup_latest = pickup_latest_utc.replace(
                        tzinfo=pytz.utc
                    ).astimezone(local_tz)

                    tomorrow_date = now.date() + timedelta(days=1)
                    day = None

                    # Convert pickup date
                    if (
                        pickup_from.date() == now.date()
                        and pickup_latest.date() == now.date()
                    ):
                        day = "today"

                    elif (
                        pickup_from.date() == tomorrow_date
                        and pickup_latest.date() == tomorrow_date
                    ):
                        day = "tomorrow"

                    elif pickup_from.date() == pickup_latest.date():
                        day = pickup_from.strftime("%d-%m-%Y")

                    # If same pickup day
                    if day:
                        text = (
                            "{} new item(s) in {}, pickup {} between {} and {}".format(
                                store["items_available"],
                                store["store"]["store_name"],
                                day,
                                pickup_from.strftime("%H:%M"),
                                pickup_latest.strftime("%H:%M"),
                            )
                        )

                    # Else different pickup day
                    else:
                        text = "{} new item(s) in {}, pickup between {} and {}".format(
                            store["items_available"],
                            store["store"]["store_name"],
                            pickup_from.strftime("%d-%m-%Y %H:%M"),
                            pickup_latest.strftime("%d-%m-%Y %H:%M"),
                        )

                    logging.info(text)
                    notifier.send_notification(text)

        # Update or create favorite store
        db.update_create_favorite_store(
            user["user_id"],
            store["store"]["store_id"],
            store["items_available"],
        )
