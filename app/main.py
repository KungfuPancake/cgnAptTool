import re
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from urllib.parse import unquote, urlparse, urlencode
from datetime import datetime, time, date, timedelta
from app_types import DayRange, Appointment
from time import sleep
from os import environ

# Service Request Types
# UUID                                  Name                                                                    Max Amount
# Ausweiswesen
# e1d5bacf-1498-44c6-9489-2dbc7e322dec  Befreiung - Ausweispflicht                                              2
# 44db93c7-379d-41b1-a06d-11820b1b71eb  Kinderreisepass - Antrag                                                5
# d29a92ab-4112-40c5-b772-427ce186cc35  Personalausweis - Antrag                                                5
# d1c1e4d7-44a6-434d-884c-6aa1fe43d7a1  Reisepass - Antrag                                                      5

# Meldewesen
# 58f5b5d5-4400-4d21-86bb-ae57bb6dc78a  Abmeldung                                                               10
# 0d2f4ea5-74f2-4699-b954-8907a1ca5f80  Anmeldung                                                               10
# d528518e-95c3-4dd8-850f-2db689fe0551  Erklärung zum Nebenwohnsitz                                             5
# 2307dc91-2bca-4b30-a8ac-eb1a03b4b3a2  Konfessionsänderung                                                     2
# b9028f0e-2b37-41c1-9176-966da3823e88  Ummeldung Wohnsitz                                                      10

# Sonstiges
# 24194702-ab60-4ea0-9c64-647797f5267b  Anschrift in Fahrzeugpapieren ändern (nur bei Umzug innerhalb Kölns).   10
# 638de2ae-20e3-4902-be70-aacd9e314fd1  Anwohnerschutzkonzept (nur in Lindenthal)                               5
# 179c690a-ef74-46c8-a6a3-d65269729601  Bewohnerparkausweis                                                     5
# e9e6d2eb-67ae-4e09-aa06-56b37d1b3467  Hausauskünfte für Vermieter                                             2
# 057d9cf7-3d7b-4d40-a578-f4ed2e2432b2  Kfz stilllegen                                                          2
# 631bf247-a668-48b0-9f05-015322f379bb  Personenstandsänderung                                                  5


# Locations
# UUID                                  Name
# 3557740d-2fb2-4e56-b93b-47023d416c97  Kundenzentrum Chorweiler
# 119cd015-75ca-4c77-a3f9-b2e183ce0ccd  Kundenzentrum Ehrenfeld
# adef3f58-20bc-465d-9879-608ac5894295  Kundenzentrum Innenstadt
# 12889773-9d8b-4be5-997d-931def4e0319  Kundenzentrum Kalk
# d34bc259-3430-4ebe-8293-f488376bc5f1  Kundenzentrum Lindenthal
# 393a5db2-d4c3-4e22-9065-df9b453ba46a  Kundenzentrum Mülheim
# 94494140-f83a-46c8-ab29-26589a9f597c  Kundenzentrum Nippes
# 853106c1-0bf8-4e08-b308-eaae6f669a9f  Kundenzentrum Porz
# b3e10f8d-3c54-44d5-b06e-21b8699ea52b  Kundenzentrum Rodenkirchen
# dae8f2d2-f54a-4313-bd37-136c6836cb14  Temporäre Ausweis- und Meldestelle Kalk

base_url = 'https://termine.stadt-koeln.de/m/kundenzentren/extern/calendar'
calendar_uid = 'b5a5a394-ec33-4130-9af3-490f99517071'

salutation = environ.get('APT_SALUTATION')
first_name = environ.get('APT_FIRST_NAME')
last_name = environ.get('APT_LAST_NAME')
mail = environ.get('APT_MAIL')
phone = environ.get('APT_PHONE')

valid_ranges = []
for day in range(7):
    valid_ranges.append(DayRange(day, time(hour=8, minute=00), time(hour=20, minute=00)))
max_days_ahead = int(environ.get('APT_MAX_DAYS_AHEAD'))

if not salutation or not first_name or not last_name or not mail or not phone:
    print("Check your env")
    exit(1)


def find_appointment() -> Optional[Appointment]:
    request = httpx.get(base_url + '?' + urlencode({'uid': calendar_uid}), follow_redirects=True)
    ws_id = request.url.params.get('wsid')

    request = httpx.post(base_url + '?' + urlencode({'uid': calendar_uid, 'wsid': ws_id}), data={
        'action_type': '',
        'steps': 'serviceslocationssearch_resultsbookingfinish',
        'step_current': 'services',
        'step_current_index': 0,
        'step_goto': '+1',
        'services': ['d29a92ab-4112-40c5-b772-427ce186cc35'],
        'service_d29a92ab-4112-40c5-b772-427ce186cc35_amount': 1
    })

    soup = BeautifulSoup(request.text, 'html.parser')
    token_element = soup.find(attrs={'name': 'request_verification_token'})

    request = httpx.post(base_url + '?' + urlencode({'uid': calendar_uid, 'wsid': ws_id}), data={
        'request_verification_token': token_element['value'],
        'action_type': 'search',
        'steps': 'serviceslocationssearch_resultsbookingfinish',
        'step_current': 'locations',
        'step_current_index': 1,
        'step_goto': '+1',
        'locations': ['3557740d-2fb2-4e56-b93b-47023d416c97', '119cd015-75ca-4c77-a3f9-b2e183ce0ccd', 'adef3f58-20bc-465d-9879-608ac5894295',
                      '12889773-9d8b-4be5-997d-931def4e0319',
                      'd34bc259-3430-4ebe-8293-f488376bc5f1', '393a5db2-d4c3-4e22-9065-df9b453ba46a', '94494140-f83a-46c8-ab29-26589a9f597c',
                      '853106c1-0bf8-4e08-b308-eaae6f669a9f',
                      'b3e10f8d-3c54-44d5-b06e-21b8699ea52b', 'dae8f2d2-f54a-4313-bd37-136c6836cb14']
    })

    soup = BeautifulSoup(request.text, 'html.parser')
    appointment_elements = soup.findAll('button', {'class': 'card'})
    appointments = extract_appointments(appointment_elements, ws_id)

    valid_appointments = []
    for appointment in appointments:
        for valid_range in valid_ranges:
            if appointment.date.date() > (date.today() + timedelta(days=max_days_ahead)):
                continue

            if appointment.date.weekday() is not valid_range.weekday:
                continue

            if valid_range.start_time < appointment.date.time() < valid_range.end_time:
                valid_appointments.append(appointment)

    print('{0}: Found {1} free slots, {2} do fit'.format(datetime.now(), len(appointments), len(valid_appointments)))

    if len(valid_appointments) > 0:
        return valid_appointments[0]

    return None


def book_appointment(appointment: Appointment):
    # this appointment fits
    httpx.get(base_url + '/booking' + '?' + urlencode({'uid': calendar_uid, 'wsid': appointment.ws_id, 'rev': 'J6A0g', 'appointment_datetime': appointment.date_raw,
                                                       'appointment_duration': appointment.duration, 'location': appointment.location, 'resources': appointment.resources}))

    request = httpx.post(base_url + '/booking' + '?' + urlencode({'uid': calendar_uid, 'wsid': appointment.ws_id, 'rev': 'J6A0g', 'appointment_datetime': appointment.date_raw,
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

    print('{0}: Booked an appointment for {1}, please check your mails!'.format(datetime.now(), appointment.date))
    while True:
        pass


def extract_appointments(elements: list, ws_id: str) -> list[Appointment]:
    appointments = []
    for appointment_element in elements:
        if 'appointment_reserve' not in appointment_element['onclick']:
            continue

        parts = re.match(r"appointment_reserve\('([^']+)'[^']+'([^']+)'[^']+'([^']+)'[^']+'([^']+)'", appointment_element['onclick'])
        date_raw = unquote(parts[1])
        appointments.append(Appointment(datetime.strptime(date_raw[0:19], '%Y-%m-%dT%H:%M:%S'), date_raw, int(parts[2]), parts[3], parts[4], ws_id))

    return appointments


while True:
    a = find_appointment()
    if a:
        book_appointment(a)
        exit(0)

    sleep(30)
