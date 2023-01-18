from operator import xor
from ipaddress import ip_network
import pygraphviz as gv
import config_generator


def main():
    G = gv.AGraph("""graph G {
    
    // BGP en bordure avec les clients
    // AS différentes
    // OSPF + MPLS dans le provider
    
    subgraph cluster_provider {
        label="provider"
        ip_range="1.1.1.0/24"
        node [asn=100, mpls=true, ospf_pid=1, ospf_area=0]
        R1 -- R2
        R2 -- R3
        R3 -- R4
        R4 -- R1
        PE1 -- R1
        PE2 -- R2
        PE3 -- R3
        PE4 -- R4
    }
    
    // Client 0
    subgraph cluster_client_0 {
        label="client0"
        ip_range="10.0.0.0/24"
        C0_1 -- C0_2 [color=red, virtual=true]
    }
    
    C0_1 [asn=111]
    C0_2 [asn=112]
    
    // BGP
    C0_1 -- PE1 [color=blue]
    C0_2 -- PE4 [color=blue]
    
    // Client 1
    subgraph cluster_client_1 {
        label="client1"
        ip_range="10.0.1.0/24"
        C1_1 -- C1_2 [color=red, virtual=true]
    }
    
    C1_1 [asn=113]
    C1_2 [asn=114]
    
    // BGP
    C1_1 -- PE2 [color=blue]
    C1_2 -- PE3 [color=blue]
}""")

    cluster_provider = G.get_subgraph("cluster_provider")
    if cluster_provider is None:
        print("Your graph must have a cluster_provider subgraph (Madge)")
        return

    # Routeurs de bordure du réseau provider
    border = set()
    for (a, b) in G.edges():
        if xor(a in cluster_provider, b in cluster_provider):
            border.add(a if a in cluster_provider else b)
    print(f"Provider network border : {border}")

    ip_range = ip_network(cluster_provider.graph_attr["ip_range"])
    if ip_range.num_addresses < len(cluster_provider.nodes()) * 2:
        print(
            f"Not enough ip in range '{ip_range}' (actual: {len(cluster_provider.nodes())}, max: {ip_range.num_addresses})")
        return

    print(f"Allocating ip addresses in range : '{ip_range}'")
    ip = ip_range.subnets(new_prefix=30)

    interfaces = {}
    for (a, b) in cluster_provider.in_edges_iter():
        subnet = next(ip)
        #print(f"Allocating link in subnet '{subnet}'")
        subnet_hosts = subnet.hosts()
        if interfaces.get(a) is None:
            interfaces[a] = {}
        if interfaces.get(b) is None:
            interfaces[b] = {}
        interfaces[a][b] = (next(subnet_hosts), subnet)
        interfaces[b][a] = (next(subnet_hosts), subnet)

    print(f"Allocated provider interfaces : {interfaces}")

    for node in cluster_provider.nodes_iter():
        if node in border:
            # routeur de bordure
            #print(f"Router '{node}' interfaces : {interfaces}")
            config = config_generator.make_config(node,
                                                  interfaces[node],
                                                  cluster_provider.node_attr["mpls"],
                                                  cluster_provider.node_attr["ospf_pid"],
                                                  cluster_provider.node_attr["ospf_area"],
                                                  cluster_provider.node_attr["asn"],
                                                  None)
            with open(f"generated/router_{node}.cfg", "w") as file:
                file.write(config)
        else:
            # routeur de coeur
            #print(f"Router '{node}' interfaces : {interfaces}")
            config = config_generator.make_config(node,
                                                  interfaces[node],
                                                  cluster_provider.node_attr["mpls"],
                                                  cluster_provider.node_attr["ospf_pid"],
                                                  cluster_provider.node_attr["ospf_area"],
                                                  cluster_provider.node_attr["asn"],
                                                  None)
            with open(f"generated/router_{node}.cfg", "w") as file:
                file.write(config)

    G.draw("rendered.svg", prog="dot")


if __name__ == "__main__":
    main()