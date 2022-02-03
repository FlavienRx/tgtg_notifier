import requests
import slack
import telegram
from emoji import emojize


class Notifier:
    def __init__(self, user):
        # Init notifier
        self.send_notif_on = user["send_notif_on"]

        if self.send_notif_on == "slack":
            try:
                self.slack_user_id = user["slack_user_id"]
                self.slack_client = slack.WebClient(token=user["slack_token"])

            except IndexError:
                raise Exception(
                    "Slack user id or token is missing for user {}".format(
                        user["email"]
                    )
                )

        elif self.send_notif_on == "telegram":
            try:
                self.telegram_chan_id = user["telegram_chan_id"]
                self.telegram_bot = telegram.Bot(token=user["telegram_token"])

            except IndexError:
                raise Exception(
                    "Telegram chan id or token is missing for user {}".format(
                        user["email"]
                    )
                )

        elif self.send_notif_on == "discord":
            try:
                self.discord_webhook_url = user["discord_webhook_url"]

            except IndexError:
                raise Exception(
                    "Discord webhook is missing for user {}".format(user["email"])
                )

        else:
            raise Exception("No notifier set for user {}".format(user["email"]))

    def send_notification(self, text):
        # Send notif on Slack
        if self.send_notif_on == "slack":
            self.slack_client.chat_postMessage(
                channel=self.slack_user_id,
                text=":sandwich: {}".format(text),
            )

        # Send notif on Telegram
        elif self.send_notif_on == "telegram":
            self.telegram_bot.send_message(
                chat_id=self.telegram_chan_id,
                text=emojize(":hamburger: {}".format(text)),
            )

        # Send notif on Discord
        elif self.send_notif_on == "discord":
            data = {"content": ":sandwich: {}".format(text)}
            requests.post(self.discord_webhook_url, data=data)
