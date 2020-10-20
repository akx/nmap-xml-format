import argparse
import xml.etree.ElementTree as ET
from typing import Iterable


def get_port_info(host: ET.Element) -> Iterable[dict]:
    for pel in host.find("ports").findall("port"):
        port_dict = dict(pel.items())
        port_dict.update(pel.find("state").items())
        sel = pel.find("service")
        if sel is not None:
            port_dict.update({f"service_{key}": value for (key, value) in sel.items()})
        yield port_dict


def get_host_info(root: ET.Element) -> Iterable[dict]:
    for host in root.findall("host"):
        addr = host.find("address").get("addr")
        names = [
            (h.get("type"), h.get("name"))
            for h in host.find("hostnames").findall("hostname")
        ]
        yield {
            "addr": addr,
            "names": names,
            "ports": list(get_port_info(host)),
            "_orig": host,
        }


def format_port(port: dict) -> str:
    header = "{protocol}/{portid}".format_map(port)
    service_name = port.get("service_product") or port.get("service_name")
    service_tunnel = port.get("service_tunnel")
    if service_name:
        if service_tunnel:
            serv = f"{service_name} (over {service_tunnel})"
        else:
            serv = f"{service_name}"
    else:
        serv = "open"
    return f"{header}: {serv}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    args = ap.parse_args()
    tree = ET.parse(args.file)
    print("| host | ptr | ip | open ports |")
    print("| - | - | - | - |")
    for hi in get_host_info(tree.getroot()):
        user_host = next((n for (t, n) in hi["names"] if t == "user"), "-")
        ptr_host = next((n for (t, n) in hi["names"] if t == "PTR"), "-")
        ip = hi["addr"]
        port_desc = [
            format_port(port) for port in hi["ports"] if port["state"] == "open"
        ]
        port_desc_join = ", ".join(port_desc) or "(no open ports probed?)"
        print(f"| {user_host} | {ptr_host} | {ip} | {port_desc_join} |")


if __name__ == "__main__":
    main()
