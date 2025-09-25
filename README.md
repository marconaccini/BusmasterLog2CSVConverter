# CANBus Logs to CSV Converter 

Multi-Format CAN Log to CSV Converter

Converts CAN bus log files from various tools (BusMaster, PCAN-View, CL2000)
to CSV format using DBC files for signal decoding.

Supported formats:
- BusMaster Ver 3.2.2: "09:25:06:1260 Rx 1 0x136 x 8 13 24 C2 A1 00 00 90 FF"
- PCAN-View v4.2.1.533: "36    92.943 DT     00E3 Rx 8  FF 64 04 28 C6 58 49 08"
- CL2000: "Timestamp;Type;ID;Data"

Author: Naccini Marco
Version: 2.0.0


## Usage 

With Python 3 use: 

	python busmaster_converter.py logfile.log database.dbc




