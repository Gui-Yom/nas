from gns3fy import Gns3Connector, Link, Node, Project
from pprint import pprint
import json


def main():
    gns3 = Gns3Connector("http://127.0.0.1:3080")
    project = None
    for p in gns3.get_projects():
        if p["name"] == "GeneratedTest":
            gns3.delete_project(project_id=p["project_id"])
            break

    project = Project(name="GeneratedTest", connector=gns3)
    project.create()

    template = "a86d5cb7-0203-4330-b519-f720edf62635"

    with open("generated/physical_mapping.json", "r") as f:
        mapping = json.load(f)

    nodes = {k: Node(name=k, project_id=project.project_id,
                     template_id=template, connector=gns3) for k in mapping.keys()}
    for n in nodes.values():
        n.create()

    links = {}
    for src, v in mapping.items():
        if src not in links:
            links[src] = {}
        for dst, phy in v.items():
            if dst not in links[src] and (dst in links and src not in links[dst]):
                link = Link(link_type="ethernet", project_id=project.project_id,
                            connector=gns3, nodes=[{"adapter_number": phy, "node_id": nodes[src].node_id, "port_number": 0}, {"adapter_number": mapping[dst][src], "node_id": nodes[dst].node_id, "port_number": 0}])
                link.create()
                links[src][dst] = link

    # print(gns3.create_project(name="GeneratedTest"))


if __name__ == "__main__":
    main()
