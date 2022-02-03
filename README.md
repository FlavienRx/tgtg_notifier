# Too Good To Go Notifier

Based on [tgtg-python](https://github.com/ahivert/tgtg-python) project.

## Instalation

This project use Pipenv as a virtual environement. You can install Pipenv by following this [link](https://pipenv.pypa.io/en/latest/install/)

Once Pipenv is installed, create a virtual env with Python 3 with this command
> pipenv --three

To install third package, run this command
> pipenv install

## Project set up
Run once the project to create the database
> pipenv run python main.py

In database, set your users email address, notification method and credentials

Notification can be sended on Slack, Telegram or Discord

### Slak example

required completed fields example:

* `email`: my-email@mail.com
* `send_notif_on`: slack
* `slack_token`: xoxb-124672357-12794653824453-bfD?HGJnbgjgn
* `slack_user_id`: 1A2B3C4DE5F6


### Telegram example

required completed fields example:

* `email`: my-email@mail.com
* `send_notif_on`: telegram
* `telegram_token`: 123456:fghMO522fdsfgbn24GN2SlRv7F
* `telegram_chan_id`: 123456

### Discord example

required completed fields example:

* `email`: my-email@mail.com
* `send_notif_on`: discord
* `discord_webhook_url`: https://discord.com/api/webhooks/...


## Sentry

You can set a sentry sdk url in `.env` beside `main.py` file.

```
SENTRY_SDK_URL=...
SENTRY_SDK_ENVIRONMENT=...
```

## Run

To run the notifier

> pipenv run python main.py

or by cron

> */5 7-22 * * * cd your/path && pipenv run python main.py
