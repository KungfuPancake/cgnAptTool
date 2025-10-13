import logging
import re
from datetime import datetime, time, date, timedelta
from time import sleep
from typing import Optional
from urllib.parse import unquote, urlencode
from dateutil.parser import parse

import httpx
import yaml
from bs4 import BeautifulSoup

from app_types import DayRange, Appointment

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

config = yaml.safe_load(open('config.yml'))

base_url = 'https://termine.stadt-koeln.de/m/kundenzentren/extern/calendar'
calendar_uid = 'b5a5a394-ec33-4130-9af3-490f99517071'

salutation = config['salutation']
first_name = config['first_name']
last_name = config['last_name']
mail = config['mail']
phone = config['phone']

valid_ranges = []
for day in config['ranges']:
    valid_ranges.append(
        DayRange(day['weekday'],
                 time(hour=int(day['begin'][0:2]), minute=int(day['begin'][3:5])),
                 time(hour=int(day['end'][0:2]), minute=int(day['end'][3:5])))
    )
max_days_ahead = config['max_days_ahead']
min_days_ahead = config['min_days_ahead']

locations = config['locations']
services = config['services']


def find_appointment() -> Optional[Appointment]:
    request = httpx.get(base_url + '?' + urlencode({'uid': calendar_uid}), follow_redirects=True)
    ws_id = request.url.params.get('wsid')

    request_data = {
        'action_type': '',
        'steps': 'serviceslocationssearch_resultsbookingfinish',
        'step_current': 'services',
        'step_current_index': 0,
        'step_goto': '+1',
        'services': []
    }
    for service in services:
        request_data['services'].append(service['type'])
        request_data[f"service_{service['type']}_amount"] = service['amount']

    request = httpx.post(base_url + '?' + urlencode({'uid': calendar_uid, 'wsid': ws_id}), data=request_data)

    soup = BeautifulSoup(request.text, 'html.parser')
    token_element = soup.find(attrs={'name': '__RequestVerificationToken'})

    request = httpx.post(base_url + '?' + urlencode({'uid': calendar_uid, 'wsid': ws_id}), data={
        '__RequestVerificationToken': token_element['value'],
        'action_type': 'search',
        'steps': 'serviceslocationssearch_resultsbookingfinish',
        'step_current': 'locations',
        'step_current_index': 1,
        'step_goto': '+1',
        'locations': locations
    })

    soup = BeautifulSoup(request.text, 'html.parser')
    appointment_elements = soup.find_all('button', {'class': 'card'})
    appointments = extract_appointments(appointment_elements, ws_id)

    valid_appointments = []
    for appointment in appointments:
        for valid_range in valid_ranges:
            if appointment.date.date() > (date.today() + timedelta(days=max_days_ahead)):
                # appointment is too far in the future
                continue

            if appointment.date.date() > (date.today() + timedelta(days=min_days_ahead)):
                # appointment is too soon
                continue

            if appointment.date.weekday() is not valid_range.weekday:
                # appointment is on a non-whitelisted day
                continue

            if valid_range.start_time < appointment.date.time() < valid_range.end_time:
                logger.info(f"Fitting appointment at {appointment.date} in {appointment.location}")
                valid_appointments.append(appointment)

    logger.info(f"Found {len(appointments)} possible appointments, {len(valid_appointments)} do fit")

    if len(valid_appointments) > 0:
        return valid_appointments[0]

    return None


def book_appointment(appointment: Appointment):
    # this appointment fits
    httpx.get(base_url + '/booking' + '?' + urlencode(
        {'uid': calendar_uid, 'wsid': appointment.ws_id, 'rev': 'ZM3uj', 'appointment_datetime': appointment.date_raw,
         'appointment_duration': appointment.duration, 'location': appointment.location,
         'resources': appointment.resources}))

    request = httpx.post(base_url + '/booking' + '?' + urlencode(
        {'uid': calendar_uid, 'wsid': appointment.ws_id, 'rev': 'ZM3uj', 'appointment_datetime': appointment.date_raw,
         'appointment_duration': appointment.duration, 'location': appointment.location,
         'resources': appointment.resources}), data={
        'action_type': 'booking',
        'salutation': salutation,
        'first_name': first_name,
        'last_name': last_name,
        'mail': mail,
        'phone': phone,
        'accept_data_privacy': 1
    }, follow_redirects=True)

    logger.info(f"Booked an appointment for {appointment.date}, please check your mails!")


def extract_appointments(elements: list, ws_id: str) -> list[Appointment]:
    appointments = []
    for card_appointment_element in elements:
        if not str(card_appointment_element['id']).startswith('slot_'):
            continue

        date_raw = card_appointment_element.strong['data-slot-from']
        actual_date = parse(date_raw)

        parts = re.match(r".*appointment_reserve\('([^']+)'[^']+'([^']+)'[^']+'([^']+)'[^']+'([^']+)'",
                         card_appointment_element['onclick'])

        appointments.append(Appointment(actual_date, date_raw, int(parts[2]), parts[3], parts[4], ws_id))

    return appointments


while True:
    try:
        a = find_appointment()
        if a:
            book_appointment(a)
            exit(0)
    except httpx.RequestError:
        logger.error("An error occured, discarding session")

    sleep(30)
