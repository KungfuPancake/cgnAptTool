# Booking tool for administrative services in Cologne*
**and possibly other districts in Germany that use the same software*
## Why?
Booking an appointment to get a new ID or some other work done at the administrative services offices in Cologne is not easy. There is a backlog of about two months, new appointments are unlocked every night and are gone very fast. Sometimes you may get lucky, as cancelled appointments will be made available again and you check the site at the exact moment. But who has time for that?

## How?
This tool will check the unwieldy calendar tool Cologne uses to automatically check for and make appointments. You just set the possible weekdays, the timespan for each day, your personal info and the desired amount of days to check ahead and the tool will check for appointments and book the first available that fits your criteria.

## Usage
Run the docker container with the appropiate environment variables, e.g.

`docker run --rm -it -e APT_SALUTATION=m -e APT_FIRST_NAME=John -e APT_LAST_NAME=Doe -e APT_MAIL="dummy@mail.com" -e APT_PHONE=1337 -e APT_MAX_DAYS_AHEAD=14 cgn_apt_tool`

## Known bugs & limitations
This is a work and progress and some features do not work yet. Most importantly:
- You can not set the desired days/timespans yet, they are hardcoded to every day between 8am and 8pm
- You can not configure the desired locations yet, they are hardcoded to every location
- You can not configure the required services yet, they are hardcoded to "Personalausweis"
- Errors are not handled yet

All hardcoded values can be changed in the code. Check the comments for the relevant UUIDs