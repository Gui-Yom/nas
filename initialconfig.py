import json
from pprint import pprint
import sys


def main():
    with open(sys.argv[1], "r") as f:
        mapping = json.load(f)
        # pprint(mapping)
    gviz = f"""
graph G {{
    subgraph cluster_provider {{
        label = "provider"
        ip_range="1.1.1.0/24"
        node [asn=100, mpls=true, ospf_pid=1, ospf_area=0]

        {make_links(mapping)}
    }}
}}
    """
    print(gviz)


def make_links(mapping):
    config = ""
    links = {}
    for src, v in mapping.items():
        if src not in links:
            links[src] = {}
        for dst, _ in v.items():
            if dst not in links[src] and (dst in links and src not in links[dst]):
                config += f"{src} -- {dst}\n        "
                links[src][dst] = True
    return config


if __name__ == "__main__":
    main()
