# Unmanned Parcel Locker System

IMPORTANT: this is a prototype to fulfill school project requirements.

- [Parcel Locker System](#parcel-locker-system)
  - [stuff i need to get for the next time i power the locker base on](#stuff-i-need-to-get-for-the-next-time-i-power-the-locker-base-on)

## Understanding the system

This is a parcel locker system designed for no-contact parcel deposit and withdrawal actions, and serves to transfer some of the responsibilities of the last mile delivery process from the logistics company to the recipient.

Last mile delivery is often the chokehold of the logistics lifecycle in terms of time and financial resources. Imagine being a delivery employee spending 5 minutes outside a recipients' door only to discover that they aren't at home. Now you finish less work and have less time to complete the rest of the work. By introducing a checkpoint where employees can make less stops and deploy more parcels, recipients are also able to benefit by being able to withdraw anytime that suits their schedule.

There are three components to the sytem.

1. The web application lives on the cloud, and is powered by PostgreSQL and Django. Recipients use it:
   - to register parcels into the system (telling the system to expect parcels to be delivered to the location); and
   - to initiate the withdraw parcel process.
2. The locker base is deployed into the field and lives on a Raspberry Pi. An ultrasonic sensor and a camera component is mounted. Multiple locker bases can be deployed and they connect to the webserver through HTTP powered by Python.
   - Delivery employees use it to initiate the deposit parcel process.
   - Recipients use it as part of the withdraw parcel process.
3. The locker unit is deployed close to the locker base. Multiple locker units can be assigned to a locker base. These are powered by ESPHome based ESP microcontrollers, and communicate to the base via MQTT. They simply listen to the base and lock/unlock when required.

***

## Notable features

- Dimension scanning
  - A unique algorithm was developed to scan the length, width, and height of parcels using only image processing magic. This feature allows locker bases to assign parcels to locker units that has the capacity to hold it.
- Fully modular
  - Locker units are not tied to locker bases, so they can be manufactured individually and assigned to locations that need them more very easily.
- Minimal interaction
  - Scan, put, and go. Scan, take, and go. The system is designed to perform workflow while requiring minimal interaction from the user, reducing the need for training, time and financial resources, as well as risk of disease transmission.
  - Depositing is just a matter of placing the parcel on the scanning platform and wait till a suitable locker opens.
  - Withdrawing is just a matter of clicking on a button and holding it for the camera to scan until the correct locker opens.
- Low requirements
  - The front end of the system is literally a web app. As long as the user has a mobile device that can browse the Internet, it can be used.

