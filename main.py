from operator import xor
from ipaddress import ip_network
import pygraphviz as gv
import config_generator
from pprint import pprint
import json
import argparse
import os


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=argparse.FileType(
        "r"), help="Config file to read")
    parser.add_argument("--out", default="generated",
                        nargs="?", required=False, help="Output folder")
    parser.add_argument("--phy", type=argparse.FileType("r"),
                        nargs="?", required=False, help="Physical mapping")
    args = parser.parse_args()

    physical_mapping = json.load(args.phy) if args.phy is not None else None

    #pprint(config_generator.physical_mapping)

    G = gv.AGraph(args.config.read())

    # cluster_provider est l'équivalent du main dans un programme
    cluster_provider = G.get_subgraph("cluster_provider")
    if cluster_provider is None:
        print("Your graph must have a cluster_provider subgraph")
        return

    # Détection des routeurs de bordure du réseau provider
    border = set()
    for a, b in G.edges():
        if xor(a in cluster_provider, b in cluster_provider):
            border.add(a if a in cluster_provider else b)
    print(f"Provider network border : {border}")

    # Espace d'adresses IP alloué aux interfaces du provider
    ip_range = ip_network(cluster_provider.graph_attr["ip_range"])
    if ip_range.num_addresses < len(cluster_provider.nodes()) * 2:
        print(
            f"Not enough ip in range '{ip_range}' (actual: {len(cluster_provider.nodes())}, max: {ip_range.num_addresses})")
        return

    print(f"Allocating ip addresses in range : '{ip_range}'")
    ip = ip_range.subnets(new_prefix=30)

    interfaces = {k: {} for k in G.nodes_iter()}
    for a, b in cluster_provider.in_edges_iter():
        subnet = next(ip)
        #print(f"Allocating link in subnet '{subnet}'")
        subnet_hosts = subnet.hosts()
        interfaces[a][b] = {"addr": next(
            subnet_hosts), "subnet": subnet, "mpls": cluster_provider.node_attr["mpls"] == "true"}
        interfaces[b][a] = {"addr": next(
            subnet_hosts), "subnet": subnet, "mpls": cluster_provider.node_attr["mpls"] == "true"}

    # Allocation des ip loopback pour les routeurs de bordure
    private_subnet = ip_network("192.168.0.0/24")
    loopback_addresses = private_subnet.hosts()
    for node in border:
        #subnet = next(loopback_addresses)
        interfaces[node][node] = {"addr": next(
            loopback_addresses), "subnet": ip_network("192.168.0.0/32"), "mpls": False}

    # Détection et allocation des interfaces provider-client
    # C'est aussi ici que l'on détecte les noeuds connectés en vpn
    vpn = {k: [] for k in border}
    for client in G.subgraphs_iter():
        if client != cluster_provider:
            for n in client.nodes_iter():
                vpn[n] = {}
            for e in G.edges_iter(client):
                a, b = e
                # Both nodes are in the same client
                if a in client and b in client:
                    if e.attr.get("vpn") != "":
                        print(f"{a} and {b} will be linked via vpn")
                        vpn[a].update(
                            {"virtual": b, "vpnid": e.attr.get("vpn")})
                        vpn[b].update(
                            {"virtual": a, "vpnid": e.attr.get("vpn")})
                    else:
                        # TODO client topologies
                        pass
                else:
                    ip_range = ip_network(e.attr.get("ip_range"))
                    hosts = ip_range.hosts()
                    interfaces[a][b] = {"addr": next(
                        hosts), "subnet": ip_range, "mpls": False}
                    interfaces[b][a] = {"addr": next(
                        hosts), "subnet": ip_range, "mpls": False}
                    print(
                        f"Found link between client and provider : {a} -- {b}")
                    if a in client:
                        vpn[b].append({"client": a})
                        vpn[a].update({"phys": b})
                    else:
                        vpn[a].append({"client": b})
                        vpn[b].update({"phys": a})

    #pprint(vpn)

    for n in border:
        for client in vpn[n]:
            peer = vpn[vpn[client["client"]]["virtual"]]["phys"]
            client["client_asn"] = client["client"].attr["asn"]
            client["peer"] = peer
            client["vpnid"] = vpn[client["client"]]["vpnid"]
            for k in interfaces[n].keys():
                if k != n and k != client["client"]:
                    client["core_addr"] = interfaces[n][k]["addr"]

    print("Allocated interfaces : ")
    pprint(interfaces)
    print("VPN config :")
    pprint(vpn)

    os.makedirs(args.out, exist_ok=True)

    for node in cluster_provider.nodes_iter():
        config = config_generator.make_config(node,
                                              interfaces,
                                              physical_mapping,
                                              border,
                                              cluster_provider.node_attr["ospf_pid"],
                                              cluster_provider.node_attr["ospf_area"],
                                              cluster_provider.node_attr["asn"],
                                              vpn if node in border else None)
        with open(f"{args.out}/router_{node}.cfg", "w") as file:
            file.write(config)

    # pprint.pprint(config_generator.physical_mapping)
    with open(f"{args.out}/physical_mapping.json", "w") as f:
        json.dump(physical_mapping, f, ensure_ascii=False)

    G.draw("rendered_cluster.svg", prog="dot")
    G.draw("rendered_neato.svg", prog="neato")


if __name__ == "__main__":
    main()
