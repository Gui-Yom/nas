import json

def main():
    print("Crawling through project configs")
    with open("GNS3/project.gns3") as file:
        project = json.loads(file.read())
    name = project["name"]
    print(f"Project: {name}")
    nodes = {}
    for node in project["topology"]["nodes"]:
        name = node["name"]
        id = node["node_id"]
        print(f"{name}: {id}")
        nodes[id] = name
    for link in project["topology"]["links"]:
        node0 = link["nodes"][0]["node_id"]
        node1 = link["nodes"][1]["node_id"]
        print(f"{nodes[node0]} -- {nodes[node1]}")


if __name__ == "__main__":
    main()