# Locker Base

## Table of Contents

- [Locker Base](#locker-base)
  - [Table of Contents](#table-of-contents)
  - [description](#description)
    - [deposit](#deposit)
    - [withdrawal](#withdrawal)

## description

the locker base:

### deposit

- scans qr code of parcel,
- verifies parcel identity with server,
- scans parcel dimensions,
- gives open command to the locker unit,
- gives close command to the locker unit,
- updates internal database,
- updates server of new locker info

### withdrawal

- scans one-time qr code of receiver,
- verifies receiver identity with server,
- gives open command to the locker unit,
- gives close command to the locker unit,
- updates internal database,
- updates server of new locker info
