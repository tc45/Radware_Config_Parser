import openpyxl
import argparse
import sys
import os
import datetime
from tabulate import tabulate
from utils.parsers import parse_nat_config, parse_firewall_config, parse_gslb_rules_config, parse_l3_data
from utils.helpers import create_and_style_table

def populate_sheet(dataset, sheet):
    # Add headers to the L3 sheet
    # Write headers to the first row
    headers = dataset[0].keys()
    for col_num, header in enumerate(headers, 1):
        col_letter = sheet.cell(row=1, column=col_num).column_letter
        sheet[f"{col_letter}1"] = header

    # Write data for each dictionary entry
    for row_num, line in enumerate(dataset, 2):
        for col_num, data in enumerate(line.values(), 1):

            col_letter = sheet.cell(row=row_num, column=col_num).column_letter
            sheet[f"{col_letter}{row_num}"] = data



def parse_l3_data_2(lines):
    l3_data = []
    original_dict = {
        "Interface": None,
        "Enabled": "no",
        "IP Version": "",
        "IPv4 Address": "",
        "Mask": "",
        "CIDR": "",
        "Broadcast": "",
        "Peer": "",
        "VLAN": "",
        "Description": ""
    }
    interface_data = original_dict.copy()
    mgmt_if = {
        "Address": "",
        "Mask": "",
        "Broadcast": "",
        "Gateway": "",
        "CIDR": "",
        "Enabled": "no",
        "SNMP_Enabled": "",
        "SYSLOG_Enabled": "",
        "RADIUS_Enabled": "",
    }

    mgmt_mapping = {
        "addr": "Address",
        "mask": "Mask",
        "broad": "Broadcast",
        "gw": "Gateway",
        "ena": "Enabled",
        "snmp": "SNMP_Enabled",
        "syslog": "SYSLOG_Enabled",
        "radius": "RADIUS_Enabled"
    }

    l3_mapping = {
        "ena": "Enabled",
        "ipver": "IP Version",
        "addr": "IPv4 Address",
        "mask": "Mask",
        "broad": "Broadcast",
        "vlan": "VLAN",
        "peer": "Peer",
        "descr": "Description"
    }

    for line in lines:
        line = line.strip()

        if line.startswith("/c/sys/mmgmt"):
            for line in lines:
                line = line.strip()
                key = line.split()[0]
                if key in mgmt_mapping:
                    mgmt_if[mgmt_mapping[key]] = line.split()[-1]
                elif line.startswith("/"):
                    break

        elif line.startswith("/c/l3/if"):
            if interface_data["Interface"] is not None:
                l3_data.append(interface_data)
                interface_data = original_dict.copy()
            interface_data["Interface"] = line.split()[-1]
            for line in lines:
                line = line.strip()
                key = line.split()[0]
                if key in l3_mapping:
                    if key == "descr":
                        interface_data[l3_mapping[key]] = line.split('"')[1]
                    else:
                        interface_data[l3_mapping[key]] = line.split()[-1]
                elif line.startswith("/"):
                    break

    if interface_data["Interface"] is not None:
        l3_data.append(interface_data)

    return l3_data


def create_parse_populate_style(workbook, payload, sheet_name, parse_string="", table_style="TableStyleMedium9"):
    sheet = workbook.create_sheet(sheet_name)
    populate_sheet(payload, sheet)
    table_name = sheet_name.replace(" ", "_")
    create_and_style_table(workbook, sheet_name, table_name=table_name, table_style=table_style)


def create_excel_output(lines, output_path):
    wb = openpyxl.Workbook()
    summary_sheet = wb.active
    summary_sheet.title = "Summary"
    l3_sheet_name = "Layer 3"
    nat_sheet_name = "NAT"
    firewall_sheet_name = "Firewall"
    gslb_network_sheet_name = "GSLB Network"
    gslb_rules_sheet_name = "GSLB Rules"

    l2_sheet = wb.create_sheet("Layer 2")
    # gslb_network_sheet = wb.create_sheet(gslb_network_sheet_name)
    # gslb_rule_sheet = wb.create_sheet(gslb_rules_sheet_name)
    # nat_sheet = wb.create_sheet(nat_sheet_name)
    # firewall_sheet = wb.create_sheet(firewall_sheet_name)


    # Parse config for L3 data and create Excel tab formatted with output
    l3_dataset = parse_l3_data(lines)
    create_parse_populate_style(wb, l3_dataset, l3_sheet_name, table_style="TableStyleMedium11")
    # Parse config for L3 data and create Excel tab formatted with output
    nat_dataset = parse_nat_config(lines)
    create_parse_populate_style(wb, nat_dataset, nat_sheet_name, table_style="TableStyleMedium9")
    # Parse config for L3 data and create Excel tab formatted with output
    firewall_dataset = parse_firewall_config(lines)
    create_parse_populate_style(wb, firewall_dataset, firewall_sheet_name, table_style="TableStyleMedium10")
    # Parse config for GSLB Rules and create Excel tab formatted with output
    gslb_rules_dataset = parse_gslb_rules_config(lines, "/c/slb/gslb/rule")
    tabulate(gslb_rules_dataset)
    create_parse_populate_style(wb, gslb_rules_dataset, gslb_rules_sheet_name, table_style="TableStyleMedium8")
    # Generic Sheets
    # populate_sheet_basic(l2_sheet, lines, "/c/l2/")
    # populate_sheet_basic(summary_sheet, lines, "/c/sys/")
    # populate_sheet_basic(gslb_network_sheet_name, lines, "/c/slb/gslb/network")
    # populate_sheet_basic(gslb_rules_sheet_name, lines, "/c/slb/gslb/rule")
    # nat_dataset = parse_nat_config(lines)
    # populate_sheet(nat_dataset, nat_sheet)
    # create_and_style_table(wb, nat_sheet_name, table_name="NAT_Data", table_style="TableStyleMedium9")
    # firewall_dataset = parse_filter_config(lines)
    # populate_sheet(firewall_dataset, firewall_sheet)
    # create_and_style_table(wb, firewall_sheet_name, table_name="Firewall_Data", table_style="TableStyleMedium9")

    wb.save(output_path)


def populate_sheet_basic(sheet, lines, keyword):
    for line in lines:
        if keyword in line:
            sheet.append([line.strip()])


def parse_file(file_path):
    # Check for argument or environment variable for the file path
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    elif 'CONFIG_FILE_PATH' in os.environ:
        file_path = os.environ['CONFIG_FILE_PATH']
    else:
        print("Please provide the file path as an argument or set the CONFIG_FILE_PATH environment variable.")
        sys.exit(1)

    # Read the file
    with open(file_path, 'r') as f:
        data = f.read()

    # Split the data into lines
    lines = data.strip().split("\n")

    # Return the output of the lines
    return lines


def get_args():
    parser = argparse.ArgumentParser(description="Parse a text file and output to Excel using OpenPyXL.")
    parser.add_argument("file_path", type=str, help="Path to the input text file.")
    parser.add_argument("--output", type=str, default="output.xlsx",
                        help="Path to save the output Excel file. Default is 'output.xlsx'.")

    args = parser.parse_args()

    if not os.path.exists(args.file_path):
        print(f"Error: File '{args.file_path}' does not exist.")
        exit(1)

    return args


def get_standard_filename(input_args):
    # Generate a timestamp
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    dest_filename = args.output
    if dest_filename.endswith(".xlsx"):
        stripped_filename = dest_filename[:-5]
        dest_filename = f"{stripped_filename}_{timestamp}.xlsx"
    elif dest_filename.endswith(".xls"):
        stripped_filename = dest_filename[:-4]
        dest_filename = f"{stripped_filename}_{timestamp}.xlsx"
    else:
        dest_filename = f"{dest_filename}_{timestamp}.xlsx"

    return dest_filename


if __name__ == "__main__":
    # Get arguments from the command line
    args = get_args()

    # Standardize filename output with timestamp
    output_filename = get_standard_filename(args)

    # Parse input file for Summary, L2, L3, GLB and other data
    input_file = parse_file(args.file_path)
    create_excel_output(input_file, output_filename)
    parsed_data = parse_nat_config(input_file)
    # Using tabulate to print the parsed data
    print(tabulate(parsed_data, headers="keys", tablefmt="grid"))
    filter_data = parse_firewall_config(input_file)
    # Using tabulate to print the parsed data
    print(tabulate(filter_data, headers="keys", tablefmt="grid"))
