import requests
import json
import datetime
import pytz
from config import (MAILGUN_BASE_URL, MAILGUN_KEY, FROM_ADDRESS, TO_ADDRESS,
                    STORE_ID, STORE_TIMEZONE)

tz = pytz.timezone(STORE_TIMEZONE)

cookie = open('cookie.txt').read()

try:
    known_appts = set(json.load(open('known_appts.json')))
except Exception as e:
    known_appts = set()


rv = requests.post(
    'https://getsupport.apple.com/web/v2/takein/timeslots',
    headers={
        'Cookie': cookie,
        'Content-Type': 'application/json; charset=UTF-8'
    },
    data=json.dumps({'store': STORE_ID}))


new_slots = set()

for day in rv.json()['data']['timeslots']['days']:
    timeslots = day.get('timeSlots')
    if timeslots:
        for ts in timeslots:
            new_slots.add(ts['epochTime'])

# New appts are ones that don't exist in the known_appts
notify_about = new_slots - known_appts


def format_for_email(time):
    start, end = time.split('-')
    start = datetime.datetime.fromtimestamp(float(start), pytz.UTC)
    end = datetime.datetime.fromtimestamp(float(end), pytz.UTC)
    start = start.astimezone(tz)
    end = end.astimezone(tz)
    return '* {} - {} ({})'.format(start, end, time)


notify_about = list(map(format_for_email, notify_about))
if len(notify_about) > 0:
    body = '''It looks as though the following appointments have become available:

    {}

    Cheers
    '''.format('\n'.join(notify_about))

    requests.post(
        MAILGUN_BASE_URL + '/messages',
        auth=("api", MAILGUN_KEY),
        data={
            'from': FROM_ADDRESS,
            'to': TO_ADDRESS,
            'subject': 'Genius Bar Alert',
            'text': body
        })

    # We can just throw out the current known and store the
    # new slots
json.dump(list(new_slots), open('known_appts.json', 'w+'))
