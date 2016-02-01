#!/usr/bin/env python
"""
xml2bom.py
Copyright 2015 Adam Greig

Convert Farnell BOM XMLs to a useful text report, including sanity checking,
and outputting quickpaste formats for Farnell, RS and DigiKey.
"""

from __future__ import print_function, division
import sys
import os.path
import datetime
import xml.etree.ElementTree as ET

if len(sys.argv) == 1:
    print("Usage: {} <input filename> [output filename]".format(sys.argv[0]))
    sys.exit()

tree = ET.parse(sys.argv[1])
parts = {}
missing_order_code = []
missing_footprint = []
inconsistent_order_code = {}
filter_parts = False

if len(sys.argv) > 3:
    included_parts = sys.argv[3].split(",")
    filter_parts = True

for comp in tree.getroot().iter('comp'):
    ref = comp.get('ref')
    if filter_parts and ref not in included_parts:
        continue
    val = comp.findtext('value')
    foot = comp.findtext('footprint')
    fields = {}
    part = {"ref": ref, "value": val, "footprint": foot, "fields": fields}

    for field in comp.iter('field'):
        name = field.get('name')
        number = field.text
        fields[name] = number

        if name not in parts:
            parts[name] = {}
        if number not in parts[name]:
            parts[name][number] = []
        elif (parts[name][number][0]['value'] != val or
              parts[name][number][0]['footprint'] != foot):
            if name not in inconsistent_order_code:
                inconsistent_order_code[name] = {}
            if number not in inconsistent_order_code[name]:
                inconsistent_order_code[name][number] = [
                    parts[name][number][0]]
            inconsistent_order_code[name][number].append(part)
        parts[name][number].append(part)

    # Store parts missing order codes or footprints
    if not fields:
        missing_order_code.append(part)
    if not foot:
        missing_footprint.append(part)

missing_footprint_report = "\n".join(
    "{:6} {:15}".format(p['ref'], p['value']) for p in missing_footprint)

missing_order_code_report = "\n".join(
    "{:6} {:15} {}".format(p['ref'], p['value'], p['footprint'])
    for p in missing_order_code)

inconsistent_order_code_report = "\n".join(
    "  {}\n".format(name) + "  " + "~"*len(name) + "\n" + "\n".join(
        "    {}: ".format(number) + "\n" + "\n".join(
            "      " +
            "{:6} {:15} {}".format(p['ref'], p['value'], p['footprint'])
            for p in inconsistent_order_code[name][number]
        ) for number in inconsistent_order_code[name]
    ) for name in inconsistent_order_code)


def farnell_formatter(number, parts):
    qty = len(parts)
    footprints = " ".join(set(
        str(p['footprint']).split(":")[-1] for p in parts))
    values = " ".join(set(p['value'] for p in parts))
    note = "{}x {} {}".format(qty, values, footprints)
    return "{},{},{}\n".format(number, qty, note[:30])


def rs_formatter(number, parts):
    qty = len(parts)
    refs = "".join(p['ref'] for p in parts)
    footprints = "-".join(set(
        str(p['footprint']).split(":")[-1] for p in parts))
    values = "-".join(set(p['value'] for p in parts))
    return "{},{},,{}x--{}--{}--{}\n".format(
        number, qty, qty, values, footprints, refs)


def digikey_formatter(number, parts):
    qty = len(parts)
    refs = " ".join(p['ref'] for p in parts)
    footprints = " ".join(set(
        str(p['footprint']).split(":")[-1] for p in parts))
    values = " ".join(set(p['value'] for p in parts))
    return "{},{},{}x {} {} {}\n".format(
        qty, number, qty, values, footprints, refs)


vendor_bom_formatters = {
    "farnell": farnell_formatter,
    "rs": rs_formatter,
    "digikey": digikey_formatter,
}

vendor_boms = []
for name in parts:
    bom_text = "  {}\n".format(name) + "  " + "~"*len(name) + "\n"
    for number in parts[name]:
        if name.lower() in vendor_bom_formatters:
            bom_text += vendor_bom_formatters[name.lower()](
                number, parts[name][number])
        else:
            qty = len(parts[name][number])
            bom_text += "{},{},{}x {} {}\n".format(
                number, qty, qty,
                " ".join(p['ref'] for p in parts[name][number]),
                ",".join(set(
                    str(p['footprint']).split(":")[-1]
                    for p in parts[name][number])))

    vendor_boms.append(bom_text)
vendor_boms = "\n\n".join(vendor_boms)

assembly_bom = "\n".join("\n".join(
    "{:20} {:<3} {:15} {:<15} {:<}".format(
        number, len(parts[name][number]),
        ",".join(set(str(p['value']) for p in parts[name][number])),
        ",".join(set(str(p['footprint']).split(":")[-1]
                     for p in parts[name][number])),
        " ".join(sorted(p['ref'] for p in parts[name][number])))
    for number in parts[name])
    for name in parts)

report = """Bill Of Materials
=================

Source file: {source}
Date: {date}

Parts Missing Footprints
------------------------
{missing_footprint}

Parts Missing Order Codes
-------------------------
{missing_code}

Inconsistent Order Codes
------------------------
{inconsistent_code}

Vendor Specific BOMs
--------------------
{vendor_boms}

Assembly BOM
------------
{assembly_bom}

""".format(
    source=os.path.basename(sys.argv[1]),
    date=datetime.datetime.now().isoformat(),
    missing_footprint=missing_footprint_report,
    missing_code=missing_order_code_report,
    inconsistent_code=inconsistent_order_code_report,
    vendor_boms=vendor_boms,
    assembly_bom=assembly_bom)

print(report)
if len(sys.argv) == 3:
    with open(sys.argv[2], 'w') as f:
        f.write(report)
