# Parcel Locker System

IMPORTANT: this is a prototype to fulfill school project requirements.

This is a parcel locker system (planned to be full stack). Planned features include:

- no contact parcel deposit
- no contact parcel withdrawal
- parcel dimension screening


**web application** is hosted on cloud, multiple **locker bases** can connect to the webserver through http, multiple **locker units** can connect to a locker base via mqtt. locker base scans the qr code, verifies the identity of the parcel (to see if it has arrived at the correct location), scans the dimension of the parcel, determines the locker that has a size most suitable to the parcel. the base then sends a record of admission to the web server, which notifies the recipient to withdraw.

the web application is powered by django, the locker units a collection of python scripts, and locker units ESPHome.

the recipient uses the web application to generate a one-time qr code that will expire, and lets the locker base scan the qr as a form of verification. the locker base sends the instruction to unlock, then lock the locker unit after the parcel has been collected.
