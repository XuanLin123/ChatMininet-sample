from mcp.server.fastmcp import FastMCP
import subprocess, os, json

mcp = FastMCP("mcp_adk_Network")


@mcp.tool("showip")
def showip(node: str) -> str:
    """Show the ip address of node."""
    result="not exist"
    node_if=node+"-eth0" 
    r = subprocess.run(['mx', node, 'ifconfig', node_if], capture_output=True, text=True)
    f = open("/tmp/myfile", "w")
    f.write(r.stdout)
    f.close()
    os.system("cat /tmp/myfile | grep inet | grep -v inet6 | awk '{print $2}' > /tmp/myip")
    f = open("/tmp/myip", "r")
    tmp_result=f.read()
    f.close()
    if tmp_result:
      return tmp_result
    return result


@mcp.tool("is_node_in_topology")
def is_node_in_topology(x: str) -> bool:
    """Determine the node x is in topology or not. If node x is in topology, return True. If not, return False"""
    response = subprocess.run(
        ["curl", "-s", "http://127.0.0.1:8080/nodes"],
        capture_output=True,
        text=True
    )
    output = response.stdout.strip()
    try:
        data = json.loads(output)
        if x in data['nodes']:
            data = json.loads(output)
            return x in data['nodes']

    except json.JSONDecodeError:
        print("Raw Response:", output)
        return False


@mcp.tool("pingtest")
def pingtest(node1: str, node2: str) -> str:
    """Try to answer whether node1 can ping node2 or not."""
    node2_ip=showip(node2)
    print("The IP address of " + node2 + "=" + node2_ip)
    if len(node2_ip)==0:
       return "Fail: The ip address of " + str(node2)+ " does not exist"
    r = subprocess.run(['mx', node1, "ping -c 4 ", node2_ip], capture_output=True, text=True)
    f = open("/tmp/myfile2", "w")
    f.write(r.stdout)
    f.close()
    f = open("/tmp/myfile2", "r")
    print(f.read())
    f.close()
    os.system("cat /tmp/myfile2 | grep received | awk '{print $4}' > /tmp/num_received")
    f = open("/tmp/num_received", "r")
    num_received=f.read()
    f.close() 
    print("num_received=", num_received)
    if len(num_received)!=0 and num_received!="0":
      return "ping scuccess"
    else:
      return "ping failure"


@mcp.tool("ChangeIP")
def ChangeIP(host_name: str, change_ip: str):
    """Change the node's IP. If there are other actions that haven't been completed, finish them first before executing this function at the end."""
    print(f"{host_name}\n{change_ip}")
    subprocess.run(
        ["curl", "-X", "GET", f"http://127.0.0.1:8080/nodes/{host_name}/{change_ip}/24"],
        capture_output=True, text=True
    )


@mcp.tool("AddLink")
def AddLink(node1: str, node2: str):
    """Establish a connection between two nodes."""
    subprocess.run(
        ["curl", "-X", "GET", f"http://127.0.0.1:8080/links/{node1}-{node2}/add"],
        capture_output=True, text=True
    )


@mcp.tool("AddHost")
def AddHost(host_name : str, add_host_ip: str = "") : 
    """Create a new host in the topology. If user input have ip, ip must not be null"""
    print(add_host_ip, "\n")
    subprocess.run(
        [
            "curl", "-X", "POST",
            f"http://127.0.0.1:8080/hosts/{host_name}/add",
            "-H", "Content-Type: application/json",
            "-d", f'{{"add_host_ip": "{add_host_ip}"}}'
            ],
        capture_output=True, text=True
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")