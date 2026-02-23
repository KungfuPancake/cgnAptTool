# Booking tool for administrative services in Cologne*
**and possibly other districts in Germany that use the same software*
## Why?
Booking an appointment to get a new ID or some other work done at the administrative services offices in Cologne is not easy. There is a backlog of about two months, new appointments are unlocked every night and are gone very fast. Sometimes you may get lucky, as cancelled appointments will be made available again and you check the site at the exact moment. But who has time for that?

## How?
This tool will check the unwieldy calendar tool Cologne uses to automatically check for and make appointments. You just set the possible weekdays, the timespan for each day, your personal info and the desired amount of days to check ahead and the tool will check for appointments and book the first available that fits your criteria.

## Usage
Create your own config file by duplicating the example. Please check everything, as there is no validation right now.
If using Docker:

`docker run -d --rm -v /root/config.yml:/app/config.yml cgn_apt_tool`

You can also run the script directly. Your config.yml needs to be in the current directory. Please make sure that all dependencies are available by running
`pip install -r requirements.txt`

After that you can run the script with
`python3 app/main.py`

## Known bugs & limitations
As of February 2026, the city of Cologne has implemented request limits, most likely due to commercial scalpers. If you send too many requests, your IP address will be blocked from accessing ANY of the administrative services systems for two weeks. The request interval has been changed to one request per minute, which seems to be under the limit. To be on the safe side, use a disposable VPS or a VPN service to not shut yourself out.

This is a work in progress and some features do not work yet. Most importantly:
- Errors are not handled yet
