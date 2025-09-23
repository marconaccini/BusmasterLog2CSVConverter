Busmaster Log to CSV converter
==============================

# Introduction

Started from [Log-CANverter](https://github.com/mitchdetailed/Log-CANverter).

Converts Busmaster .log file (BUSMASTER Ver 3.2.2) to .csv format using DBC symbol decoding files.

The converter looks in to log file and collect all and only signals decriptable by DBC file and create CSV table.


# Usage 

With Python 3 use: 

	python busmaster_converter.py logfile.log database.dbc -o output.csv

or 
	
	py busmaster_converter.py logfile.log database.dbc -o output.csv

# Installation  

Clone the reposiotiry   

	git clone https://github.com/tuousername/busmaster-converter.git
	cd busmaster-converter

# How to run it

	python busmaster_converter.py <file_log> <file_dbc> [file_dbc2 ...] -o <output.csv>


