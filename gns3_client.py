from pprint import pprint
from gns3fy import Gns3Connector, Project


gns3 = Gns3Connector("http://127.0.0.1:3080")
project = gns3.get_project(name="GeneratedTest")
pprint(gns3.get_links(project_id=project["project_id"]))
