#!/usr/bin/env python3
"""
Convertitore BusMaster Log to CSV
Converte file .log di BusMaster in CSV utilizzando file .dbc per decodificare i messaggi CAN.

Formato log input: "09:25:06:1260 Rx 1 0x136 x 8 13 24 C2 A1 00 00 90 FF"
Formato: <Time><Tx/Rx><Channel><CAN ID><Type><DLC><DataBytes>
"""

import re
import csv
import argparse
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import struct


@dataclass
class CANMessage:
    """Rappresenta un messaggio CAN parsato dal log"""
    timestamp: str
    direction: str  # Tx/Rx
    channel: int
    can_id: int
    dlc: int
    data: bytes


@dataclass
class DBCSignal:
    """Rappresenta un segnale DBC"""
    name: str
    start_bit: int
    size: int
    is_little_endian: bool
    is_signed: bool
    factor: float
    offset: float
    minimum: float
    maximum: float
    unit: str


@dataclass
class DBCMessage:
    """Rappresenta un messaggio DBC"""
    can_id: int
    name: str
    dlc: int
    signals: Dict[str, DBCSignal]


class DBCParser:
    """Parser per file DBC"""

    def __init__(self):
        self.messages: Dict[int, DBCMessage] = {}

    def parse_files(self, dbc_files: List[str]):
        """Parsa uno o più file DBC"""
        for dbc_file in dbc_files:
            self.parse_file(dbc_file)

    def parse_file(self, dbc_file: str):
        """Parsa un singolo file DBC"""
        print(f"Parsing DBC file: {dbc_file}")

        try:
            with open(dbc_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Prova con encoding latin-1 se utf-8 fallisce
            with open(dbc_file, 'r', encoding='latin-1') as f:
                content = f.read()

        # Pattern per messaggi: BO_ <ID> <MessageName>: <DLC> <Sender>
        message_pattern = r'BO_\s+(\d+)\s+(\w+)\s*:\s*(\d+)\s+(\w+)'

        # Pattern per segnali: SG_ <SignalName> : <StartBit>|<Size>@<Endianness><Sign> (<Factor>,<Offset>) [<Min>|<Max>] "<Unit>" <Receivers>
        signal_pattern = r'SG_\s+(\w+)\s*:\s*(\d+)\|(\d+)@([01])([+-])\s*\(\s*([-+]?\d*\.?\d*)\s*,\s*([-+]?\d*\.?\d*)\s*\)\s*\[\s*([-+]?\d*\.?\d*)\s*\|\s*([-+]?\d*\.?\d*)\s*\]\s*"([^"]*)"\s*(.*)'

        lines = content.split('\n')
        current_message = None

        for line in lines:
            line = line.strip()

            # Parse message
            message_match = re.match(message_pattern, line)
            if message_match:
                can_id = int(message_match.group(1))
                name = message_match.group(2)
                dlc = int(message_match.group(3))

                current_message = DBCMessage(can_id, name, dlc, {})
                self.messages[can_id] = current_message
                continue

            # Parse signal
            signal_match = re.match(signal_pattern, line)
            if signal_match and current_message:
                signal_name = signal_match.group(1)
                start_bit = int(signal_match.group(2))
                size = int(signal_match.group(3))
                is_little_endian = signal_match.group(4) == '1'
                is_signed = signal_match.group(5) == '-'

                try:
                    factor = float(signal_match.group(6)) if signal_match.group(6) else 1.0
                    offset = float(signal_match.group(7)) if signal_match.group(7) else 0.0
                    minimum = float(signal_match.group(8)) if signal_match.group(8) else 0.0
                    maximum = float(signal_match.group(9)) if signal_match.group(9) else 0.0
                except ValueError:
                    factor, offset, minimum, maximum = 1.0, 0.0, 0.0, 0.0

                unit = signal_match.group(10)

                signal = DBCSignal(
                    signal_name, start_bit, size, is_little_endian,
                    is_signed, factor, offset, minimum, maximum, unit
                )

                current_message.signals[signal_name] = signal

        print(f"Parsed {len(self.messages)} messages from {dbc_file}")


class BusMasterLogParser:
    """Parser per file log di BusMaster"""

    def __init__(self):
        # Pattern per parsare le righe del log
        # Formato: "09:25:06:1260 Rx 1 0x136 x 8 13 24 C2 A1 00 00 90 FF"
        ## self.log_pattern = r'(\d{2}:\d{2}:\d{2}:\d{3,4})\s+(Tx|Rx)\s+(\d+)\s+(0x[0-9A-Fa-f]+)\s+x\s+(\d+)\s+((?:[0-9A-Fa-f]{2}\s*)*)'
        self.log_pattern = (r'(\d{2}:\d{2}:\d{2}:\d{3,4})\s+'
                            r'(Tx|Rx)\s+'
                            r'(\d+)\s+'
                            r'(0x[0-9A-Fa-f]+)\s+'
                            r'.\s+'
                            r'(\d+)\s+'
                            r'((?:[0-9A-Fa-f]{2}\s*)*)')

    def parse_file(self, log_file: str) -> List[CANMessage]:
        """Parsa il file log e restituisce una lista di messaggi CAN"""
        messages = []

        print(f"Parsing log file: {log_file}")

        with open(log_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                match = re.match(self.log_pattern, line)
                if match:
                    timestamp = match.group(1)
                    direction = match.group(2)
                    channel = int(match.group(3))
                    can_id = int(match.group(4), 16)  # Converte da hex
                    dlc = int(match.group(5))
                    data_str = match.group(6).strip()


                    # Converte i dati hex in bytes
                    if data_str:
                        data_bytes = bytes.fromhex(data_str.replace(' ', ''))
                    else:
                        data_bytes = b''

                    # Verifica che DLC corrisponda alla lunghezza dei dati
                    if len(data_bytes) != dlc:
                        print(f"Warning: DLC mismatch at line {line_num}: expected {dlc}, got {len(data_bytes)}")

                    message = CANMessage(timestamp, direction, channel, can_id, dlc, data_bytes)
                    messages.append(message)
                else:
                    print(f"Warning: Could not parse line {line_num}: {line}")

        print(f"Parsed {len(messages)} CAN messages")
        return messages


class SignalDecoder:
    """Decodificatore per segnali CAN utilizzando definizioni DBC"""

    @staticmethod
    def extract_signal_value(data: bytes, signal: DBCSignal) -> Optional[float]:
        """Estrae il valore di un segnale dai dati CAN"""
        if len(data) == 0:
            return None

        try:
            # Converte i dati in un intero a 64 bit
            data_padded = data + b'\x00' * (8 - len(data))  # Pad a 8 byte
            data_int = int.from_bytes(data_padded, byteorder='little')

            # Calcola la posizione del bit considerando l'endianness
            if signal.is_little_endian:
                # Intel format (little endian)
                start_bit = signal.start_bit
            else:
                # Motorola format (big endian)
                # Converte la posizione del bit da Motorola a Intel
                byte_pos = signal.start_bit // 8
                bit_pos = signal.start_bit % 8
                start_bit = byte_pos * 8 + (7 - bit_pos) - signal.size + 1

            # Estrae i bit
            mask = (1 << signal.size) - 1
            raw_value = (data_int >> start_bit) & mask

            # Gestisce il segno se necessario
            if signal.is_signed and raw_value & (1 << (signal.size - 1)):
                raw_value -= (1 << signal.size)

            # Applica fattore di scala e offset
            physical_value = raw_value * signal.factor + signal.offset

            return physical_value

        except Exception as e:
            print(f"Error decoding signal {signal.name}: {e}")
            return None


def convert_log_to_csv(log_file: str, dbc_files: List[str], output_file: str):
    """Converte un file log BusMaster in CSV utilizzando file DBC"""

    # Parse DBC files
    dbc_parser = DBCParser()
    dbc_parser.parse_files(dbc_files)

    if not dbc_parser.messages:
        print("Error: No messages found in DBC files")
        return

    # Parse log file
    log_parser = BusMasterLogParser()
    can_messages = log_parser.parse_file(log_file)

    if not can_messages:
        print("Error: No CAN messages found in log file")
        return

    # Raccoglie tutti i nomi dei segnali unici
    all_signals = set()
    for dbc_message in dbc_parser.messages.values():
        for signal_name in dbc_message.signals.keys():
            all_signals.add(signal_name)

    all_signals = sorted(list(all_signals))
    print(f"Found {len(all_signals)} unique signals")

    # Prepara l'header CSV
    csv_header = ['time'] + all_signals

    # Processo i messaggi e scrivi CSV
    decoder = SignalDecoder()

    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        writer.writerow(csv_header)
        rrow = 0

        for can_message in can_messages:
            # Inizializza la riga con timestamp e valori vuoti
            if rrow == 0:
                row = [can_message.timestamp] + [None] * len(all_signals)

            # Se il messaggio CAN ha una definizione DBC corrispondente
            if can_message.can_id in dbc_parser.messages:
                dbc_message = dbc_parser.messages[can_message.can_id]

                # Decodifica tutti i segnali del messaggio
                for signal_name, signal in dbc_message.signals.items():
                    if signal_name in all_signals:
                        signal_index = all_signals.index(signal_name) + 1  # +1 per il timestamp
                        value = decoder.extract_signal_value(can_message.data, signal)
                        if value is not None:
                            row[signal_index] = value
                            rrow += 1


            writer.writerow(row)

    print(f"CSV file created: {output_file}")


def main():
    if False:
        """Funzione principale"""
        parser = argparse.ArgumentParser(description='Converte file log BusMaster in CSV usando file DBC')
        parser.add_argument('log_file', help='File log BusMaster di input')
        parser.add_argument('dbc_files', nargs='+', help='Uno o più file DBC')
        parser.add_argument('-o', '--output', default='output.csv', help='File CSV di output (default: output.csv)')
        parser.add_argument('-d', '--delimiter', default=';', help='Separatore CSV (default: ;)')

        args = parser.parse_args()

        # Verifica che i file esistano
        if not Path(args.log_file).exists():
            print(f"Error: Log file {args.log_file} not found")
            return

        for dbc_file in args.dbc_files:
            if not Path(dbc_file).exists():
                print(f"Error: DBC file {dbc_file} not found")
                return


        # Esegui la conversione
        convert_log_to_csv(args.log_file, args.dbc_files_list, args.output_csv)

    else:

        log_file = "Veh.049_BMLogs.log"  # Il tuo file di log Busmaster
        dbc_files_list = [ "MCU_TM4.dbc", "TRK_CAN1.dbc"]  # La tua lista di file DBC
        output_csv = "out2.csv"  # Il nome del file CSV di output

        # Esegui la conversione
        convert_log_to_csv(log_file, dbc_files_list, output_csv)


if __name__ == '__main__':
    main()