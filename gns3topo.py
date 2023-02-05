from gns3fy import Gns3Connector, Link, Node, Project
from pprint import pprint
import json
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("phy", type=argparse.FileType("r"),
                        help="Physical mapping")
    parser.add_argument("--server", default="http://127.0.0.1:3080",
                        nargs="?", required=False, help="GNS3 server url")
    parser.add_argument("--name", default="GeneratedTest",
                        nargs="?", required=False, help="GNS3 project name")
    parser.add_argument("--router", default="a86d5cb7-0203-4330-b519-f720edf62635",
                        nargs="?", required=False, help="Router template id")
    args = parser.parse_args()

    gns3 = Gns3Connector(args.server)
    project = None
    for p in gns3.get_projects():
        if p["name"] == args.name:
            gns3.delete_project(project_id=p["project_id"])
            break

    project = Project(name=args.name, connector=gns3)
    project.create()

    mapping = json.load(args.phy)

    nodes = {k: Node(name=k, project_id=project.project_id,
                     template_id=args.router, connector=gns3) for k in mapping.keys()}
    for n in nodes.values():
        n.create()

    links = {}
    for src, v in mapping.items():
        if src not in links:
            links[src] = {}
        for dst, phy in v.items():
            if dst not in links[src] and (dst in links and src not in links[dst]):
                link = Link(link_type="ethernet", project_id=project.project_id, connector=gns3,
                            nodes=[{"adapter_number": phy, "node_id": nodes[src].node_id, "port_number": 0},
                                   {"adapter_number": mapping[dst][src], "node_id": nodes[dst].node_id, "port_number": 0}])
                link.create()
                links[src][dst] = link

    for k, n in nodes.items():
        print(f"{k}: {n.node_directory}")


if __name__ == "__main__":
    main()
