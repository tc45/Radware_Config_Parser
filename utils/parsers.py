# Parser file
from utils.helpers import drop_host_bits, combine_gslb_data, is_in_same_subnet


def parse_firewall_config(config_text):
    original_dict = {
        "Line": "",
        "Name": "",
        "Enabled": "",
        "Action": "",
        "IP Version": "",
        "Source CIDR": "",
        "Destination CIDR": "",
        "Group": "",
        "Protocol": "",
        "Destination Port": "",
        "Remote Port": "",
        "VLAN": "",
        "Address ID": "",
        "Return Source MAC": "",
        "Allow Return": "",
    }
    filter_data = {}
    filter_list = []
    filter_id = 0
    sip = ""
    sip_cidr = ""
    dip = ""
    dip_cidr = ""
    x = 0

    for line in config_text:
        stripped_line = line.strip()

        if stripped_line.startswith('/c/slb/filt'):
            filter_id = stripped_line.split()[-1]
            if not filter_id.isnumeric():
                # print("Not a number")
                filter_id = int(filter_id.split('/')[0])
                if len(filter_data) == 0:
                    filter_data = original_dict.copy()
                    filter_data["Line"] = filter_id
                elif filter_id != filter_data["Line"]:
                    print(filter_data)
                    filter_list.append(filter_data)
                    filter_data = original_dict.copy()
                    filter_data["Line"] = filter_id
            else:
                filter_id = int(filter_id)
                if int(filter_id) == 1:
                    x = 1
                    filter_data = original_dict.copy()
                    filter_data["Line"] = filter_id
                else:
                    print(filter_data)
                    filter_list.append(filter_data)
                    filter_data = original_dict.copy()
                    filter_data["Line"] = filter_id
            # if filter_id != filter_item["Line"]:
            #     filter_item = original_dict.copy()
            #     filter_item["Line"] = filter_id

        elif x == 1 and stripped_line.startswith('/') and not stripped_line.startswith('/c/slb/filt'):
            break

        elif filter_data and stripped_line:
            key_value = stripped_line.split(maxsplit=1)
            if key_value[0] == "ena" or key_value[0] == "dis":
                value = key_value[0]
                key_value[0] = "Enabled"
                if value == "ena":
                    key_value.append("Yes")
                else:
                    key_value.append("No")
            elif key_value[0] == "name":
                key_value[0] = "Name"
                key_value[1] = key_value[1].strip('"')
            elif key_value[0] == "action":
                key_value[0] = "Action"
            elif key_value[0] == "ipver":
                key_value[0] = "IP Version"
            elif key_value[0] == "group":
                key_value[0] = "Group"
            elif key_value[0] == "sip":
                if key_value[1] == "any":
                    key_value[1] = "0.0.0.0"
                sip = key_value[1]
                continue
            elif key_value[0] == "smask":
                print(sip, " ", dip)
                if key_value[0] == "0.0.0.0":
                    print("Stop")
                key_value[0] = "Source CIDR"
                mask = key_value[1]
                key_value[1] = drop_host_bits(sip, mask)
            elif key_value[0] == "dip":
                if key_value[1] == "any":
                    key_value[1] = "0.0.0.0"
                dip = key_value[1]
                continue
            elif key_value[0] == "dmask":
                key_value[0] = "Destination CIDR"
                mask = key_value[1]
                key_value[1] = drop_host_bits(dip, mask)
            elif key_value[0] == "rport":
                key_value[0] = "Remote Port"
            elif key_value[0] == "proto":
                key_value[0] = "Protocol"
            elif key_value[0] == "dport":
                key_value[0] = "Destination Port"
            elif key_value[0] == "vlan":
                key_value[0] = "VLAN"
            elif key_value[0] == "add":
                key_value[0] = "Address ID"
            elif key_value[0] == "rtsrcmac":
                key_value[0] = "Return Source MAC"
                key_value[1] = "yes"
            elif key_value[0] == "reverse":
                key_value[0] = "Allow Return"
                key_value[1] = "yes"

            if len(key_value) == 2:
                key, value = key_value
                filter_data[key] = value

    # Add the last NAT configuration if it exists
    if filter_data:
        filter_list.append(filter_data)

    return filter_list


def parse_nat_config(config_text):

    nat_list = []
    original_dict = {
        "Line": "",
        "Rule": "",
        "IP Version": "",
        "Wan Link": "",
        "Local Address": "",
        "NAT Address": "",
        "Type": "",
        "No NAT": "",
        "Name": "",
    }
    nat_data = {}
    line_number = 1

    for line in config_text:
        stripped_line = line.strip()

        # Check for the beginning of a NAT or NO_NAT configuration
        if stripped_line.startswith('/c/slb/lp/nat'):

            # If we're already capturing a NAT configuration, add it to the list
            if nat_data:
                nat_list.append(nat_data)
                line_number += 1


            # Start capturing a new NAT configuration
            nat_data = original_dict.copy()
            # Write the line number
            nat_data["Line"] = line_number
            # Write the 2nd half of the line to the Name key
            nat_data["Rule"] = stripped_line.split()[-1]

        # Check for the end of a NAT configuration
        elif stripped_line.startswith('/') and not stripped_line.startswith('/c/slb/lp/nat'):
            if nat_data:
                nat_list.append(nat_data)
                nat_data = None

        # If we're within a NAT configuration, capture the relevant information
        elif nat_data and stripped_line:
            key_value = stripped_line.split(maxsplit=2)
            if key_value[0] == "ipver":
                key_value[0] = "IP Version"
            elif key_value[0] == "name":
                key_value[0] = "Name"
                key_value[1] = key_value[1].strip('"')
            elif key_value[0] == "wanlink":
                key_value[0] = "Wan Link"
            elif key_value[0] == "locladd":
                key_value[0] = "Local Address"
            elif key_value[0] == "natadd":
                key_value[0] = "NAT Address"
            elif key_value[0] == "type":
                key_value[0] = "Type"

            if len(key_value) == 2:
                key, value = key_value
                nat_data[key] = value
            elif key_value[0] == "Local Address" or key_value[0] == "NAT Address":
                key, address, mask = key_value
                cidr = drop_host_bits(address, mask)
                nat_data[key] = cidr

    # Add the last NAT configuration if it exists
    if nat_data:
        nat_list.append(nat_data)

    return nat_list


def parse_gslb_network_config(config_text, search_string, gslb_rules_list):


    original_dict = {
        "Network": "",
        "Enabled": "",
        "Server Type": "",
        "Server IP": "",
        "WAN Group": "",
    }
    gslb_network_id = ""
    gslb_network_data = {}
    gslb_network_list = []
    x = 0

    for line in config_text:
        stripped_line = line.strip()
        if stripped_line.startswith(search_string):
            rule_start = stripped_line.split()
            gslb_network_id = rule_start[1]
            gslb_network_id = int(gslb_network_id)
            if x == 0:
                x += 1
                gslb_network_data = original_dict.copy()
                gslb_network_data["Network"] = gslb_network_id
            else:
                print(gslb_network_data)
                gslb_network_list.append(gslb_network_data)
                gslb_network_data = original_dict.copy()
                gslb_network_data["Network"] = gslb_network_id


        elif x == 1 and stripped_line.startswith('/') and not stripped_line.startswith(search_string):
            break

        elif gslb_network_data and stripped_line:
            key_value = stripped_line.split(maxsplit=1)
            if key_value[0] == "ena" or key_value[0] == "dis":
                value = key_value[0]
                key_value[0] = "Enabled"
                if value == "ena":
                    key_value.append("Yes")
                else:
                    key_value.append("No")
            elif key_value[0] == "servtyp":
                key_value[0] = "Server Type"
            elif key_value[0] == "servip":
                key_value[0] = "Server IP"
            elif key_value[0] == "wangrp":
                key_value[0] = "WAN Group"

            if len(key_value) == 2:
                key, value = key_value
                gslb_network_data[key] = value

    # Add the last NAT configuration if it exists
    if gslb_network_data:
        gslb_network_list.append(gslb_network_data)

    return gslb_network_list


def parse_gslb_rules_config(config_text, search_string):
    original_dict = {
        "Rule": "",
        "Name": "",
        "Enabled": "",
        "Type": "",
        "TTL": "",
        "RR": "",
        "DNS Name": "",
        "Fallback": "",
        "Metric 1 gmetric": "",
        "Metric 1 addnet": "",
        "Metric 3 gmetric": "",
        "Metric 3 addnet": "",
    }
    gslb_rule_data = {}
    gslb_rule_list = []
    x = 0
    metric = ""

    for line in config_text:
        stripped_line = line.strip()

        if stripped_line.startswith(search_string):
            rule_start = stripped_line.split()
            gslb_rule_id = ""
            metric = ""
            if len(rule_start) == 2:
                gslb_rule_id = rule_start[1]
            elif len(rule_start) == 3:
                metric = rule_start[2]
                key = rule_start[1].split("/")[1]
                stripped_line = [key, metric]
                continue
            if not gslb_rule_id.isnumeric():
                print("Not a number")
                gslb_rule_id = int(gslb_rule_id.split('/')[0])
                if len(gslb_rule_data) == 0:
                    gslb_rule_data = original_dict.copy()
                    gslb_rule_data["Rule"] = gslb_rule_id
                elif gslb_rule_id != gslb_rule_data["Rule"]:
                    x += 1
                    print(gslb_rule_data)
                    gslb_rule_list.append(gslb_rule_data)
                    gslb_rule_data = original_dict.copy()
                    gslb_rule_data["Rule"] = gslb_rule_id
            else:
                gslb_rule_id = int(gslb_rule_id)
                if x == 0:
                    x += 1
                    gslb_rule_data = original_dict.copy()
                    gslb_rule_data["Rule"] = gslb_rule_id
                else:
                    print(gslb_rule_data)
                    gslb_rule_list.append(gslb_rule_data)
                    gslb_rule_data = original_dict.copy()
                    gslb_rule_data["Rule"] = gslb_rule_id

        elif x == 1 and stripped_line.startswith('/') and not stripped_line.startswith(search_string):
            break

        elif gslb_rule_data and stripped_line:
            key_value = stripped_line.split(maxsplit=1)
            if key_value[0] == "ena" or key_value[0] == "dis":
                value = key_value[0]
                key_value[0] = "Enabled"
                if value == "ena":
                    key_value.append("Yes")
                else:
                    key_value.append("No")
            elif key_value[0] == "name":
                key_value[0] = "Name"
                key_value[1] = key_value[1].strip('"')
            elif key_value[0] == "type":
                key_value[0] = "Type"
            elif key_value[0] == "ttl":
                key_value[0] = "TTL"
            elif key_value[0] == "rr":
                key_value[0] = "RR"
            elif key_value[0] == "dname":
                key_value[0] = "DNS Name"
                key_value[1] = key_value[1].replace('"', '')
            elif key_value[0] == "fallback":
                if key_value[1] == "ena":
                    key_value[1] = "Yes"
                else:
                    key_value[1] = "No"
                key_value[0] = "Fallback"
            elif key_value[0] == "gmetric":
                key_value[0] = "Metric " + str(metric) + " gmetric"
            elif key_value[0] == "addnet":
                key_value[0] = "Metric " + str(metric) + " addnet"

            if len(key_value) == 2:
                key, value = key_value
                gslb_rule_data[key] = value

    # Add the last NAT configuration if it exists
    if gslb_rule_data:
        gslb_rule_list.append(gslb_rule_data)

    # Run parser for the network configuration to add to the dataset
    gslb_networks = parse_gslb_network_config(config_text, "/c/slb/gslb/network", gslb_rule_list)
    # Combine data into the gslb_rules
    combined_list = combine_gslb_data(gslb_rule_list, gslb_networks)

    return combined_list


def parse_l3_data(lines):
    l3_data = []
    original_dict = {
        "Interface": None,
        "Enabled": "",
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
        "Enabled": "",
        "SNMP_Enabled": "",
        "SYSLOG_Enabled": "",
        "RADIUS_Enabled": "",
        }

    # Track Interface Configuration Sections
    x = 0
    # Track Management Interface Configuration Sections
    y = 0

    for line in lines:
        line = line.strip()
        if y != 2:
            if line.startswith("/c/sys/mmgmt"):
                y = 1
            elif y == 1 and "addr" in line:
                mgmt_if["Address"] = line.split()[-1]
            elif y == 1 and "mask" in line:
                mgmt_if["Mask"] = line.split()[-1]
            elif y == 1 and "broad" in line:
                mgmt_if["Broadcast"] = line.split()[-1]
            elif y == 1 and "gw" in line:
                mgmt_if["Gateway"] = line.split()[-1]
            elif y == 1 and "ena" in line:
                mgmt_if["Enabled"] = "yes"
            elif y == 1 and "snmp" in line:
                mgmt_if["SNMP_Enabled"] = line.split()[-1]
            elif y == 1 and "syslog" in line:
                mgmt_if["SYSLOG_Enabled"] = line.split()[-1]
            elif y == 1 and "radius" in line:
                mgmt_if["RADIUS_Enabled"] = line.split()[-1]
            elif y == 1 and line.startswith("/"):
                y = 2
                if mgmt_if["Enabled"] == "":
                    mgmt_if["Enabled"] = "no"
                mgmt_if["CIDR"] = drop_host_bits(mgmt_if["Address"], mgmt_if["Mask"])
                continue

        if x == 1 and line.startswith("/") and "/c/l3/if" not in line:
            x = 2
            l3_data.append(interface_data)
            interface_data = original_dict.copy()  # Reset interface data
            continue
        elif "/c/l3/if" in line and x != 2:
            if interface_data["Interface"] is not None:  # If there's existing data, append it to the list
                l3_data.append(interface_data)
                interface_data = original_dict.copy()  # Reset for the next interface
            interface_data["Interface"] = line.split()[-1]
            x = 1
        elif x == 2:
            continue
        elif "ena" in line and x == 1:
            # interface_data["enabled"] = line.split()[-1]
            interface_data["Enabled"] = "yes"
        elif "ipver" in line and x == 1:
            interface_data["IP Version"] = line.split()[-1]
        elif "addr" in line and x == 1:
            interface_data["IPv4 Address"] = line.split()[-1]
            # Copy values from mgmt_if if IP address matches
            if is_in_same_subnet(interface_data["IPv4 Address"], mgmt_if["CIDR"]):
                print(f'Interface is currently: {interface_data["IPv4 Address"]} \nMgmt CIDR: {mgmt_if["CIDR"]}')
                interface_data["CIDR"] = mgmt_if["CIDR"]
                interface_data["Broadcast"] = mgmt_if["Broadcast"]
                interface_data["Mask"] = mgmt_if["Mask"]
        elif "mask" in line and x == 1:
            interface_data["Mask"] = line.split()[-1]
            interface_data["CIDR"] = drop_host_bits(interface_data["IPv4 Address"], interface_data["Mask"])
        elif "broad" in line and x == 1:
            interface_data["Broadcast"] = line.split()[-1]
        elif "vlan" in line and x == 1:
            interface_data["VLAN"] = line.split()[-1]
        elif "peer" in line and x == 1:
            interface_data["Peer"] = line.split()[-1]
        elif "descr" in line and x == 1:
            interface_data["Description"] = line.split('"')[1]

    if interface_data and interface_data["Interface"] is not None:  # Append the last interface's data
        l3_data.append(interface_data)

    return l3_data
