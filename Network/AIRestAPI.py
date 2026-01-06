import os,sys,subprocess
import signal
import threading
import time
import inspect
import ctypes
import yaml
import json
import traceback
import multiprocessing
import requests
import logging
import ipaddress
import re
import base64

from bottle import request, response

from mininet.net                     import Containernet
from mininet.node                    import Controller
from mininet.cli                     import CLI
from mininet.link import TCLink


(__name__ == "__main__") and sys.path.append("../")
from Network.OriginalRestAPI         import MininetRest
from Network.Visualization.M2Editor  import MimicEditor


class AI_MininetRest(MininetRest):
    # ---------------------------------------------------------------------------------------------------

    '''self initialization and StartUp'''

    def __init__(
        self , topo_jsonpath="Platform-Data/topo.json" , topo_mnpath="Platform-Data/topo.mn" , server_url="http://127.0.0.1:8080" , 
        loginfo=False , 
    ) :
        self.ContainerNet = Containernet(controller=Controller)
        # self.ContainerNet.addController("c0")

        super().__init__(self.ContainerNet)
        self.BuildContainernet(topofile = topo_jsonpath)

        self.MNFile          = topo_mnpath
        self.server_url      = server_url
        self.LogInfo         = loginfo

        self.ThreadofRestAPI = threading.Thread(target = self.run)

        self.route('/hosts/<host_name>/add'        ,                callback=self.add_host    )
        self.route('/docker/<node_name>/add'       , method='POST', callback=self.add_docker  )
        self.route('/links/<link_name>/add'        , method='GET' , callback=self.add_link    )
        
        self.route('/hosts/<host_name>/del'        ,                callback=self.del_host    )
        self.route('/docker/<node_name>/del'       , method='POST', callback=self.del_docker  )
        self.route('/links/<link_name>/del'        , method='GET' , callback=self.del_link    )
        
        self.route('/nodes/<node_name>/<new_ip>/<new_netmask>'    , callback=self.ChangeHostIP)


    def BuildContainernet(self , topofile=None) : 
        topo = {}
        with open(topofile , 'r') as file:
            topo = json.load(file)

        Hosts    = {}
        Dockers  = {}
        Switches = {}
        Links    = {}

        HostsInTopo    = topo.get(  "hosts"  , [])
        DockersInTopo  = topo.get( "dockers" , [])
        SwitchesInTopo = topo.get("switches" , [])
        LinksInTopo    = topo.get(  "links"  , [])

        # Add Hosts
        for host_info in HostsInTopo:
            host_id   = host_info.get("id", None)
            host_name = host_info.get("name", None)
            host_ip   = host_info.get("ip_address", "127.0.0.1")

            if host_id and host_name:
                if host_ip != "127.0.0.1":
                    if "/" not in host_ip:
                        host_ip_cidr = host_ip + "/24"
                    else:
                        host_ip_cidr = host_ip

                    ip_base = host_ip.split(".")
                    gateway = f"{ip_base[0]}.{ip_base[1]}.{ip_base[2]}.1"

                    Hosts[host_id] = self.ContainerNet.addHost(
                        host_name,
                        ip=host_ip_cidr,
                        defaultRoute=f"via {gateway}"
                    )
                else:
                    Hosts[host_id] = self.ContainerNet.addHost(host_name, ip=host_ip)


        # Add Dockers
        for docker_info in DockersInTopo:
            docker_id   = docker_info.get( "id"  ,      None      )
            docker_name = docker_info.get("name" ,      None      )
            docker_ip   = docker_info.get( "ip"  ,   "127.0.0.1"  )
            docker_img  = docker_info.get( "img" , "ubuntu:trusty")
            if docker_id and docker_name :
                Dockers[docker_id] = self.ContainerNet.addDocker(docker_name, ip=docker_ip, dimage=docker_img)

        # Add Switches
        Switches = {}
        for sw_info in SwitchesInTopo:
            sw_id   = sw_info.get("id")
            sw_name = sw_info.get("name")

            if sw_id and sw_name:
                sw = self.ContainerNet.addSwitch(
                    sw_name,
                    failMode='standalone',
                    protocols='OpenFlow13',
                    controller=None
                )
                
                Switches[sw_id] = sw


        # Add Links
        for link_info in LinksInTopo:
            link_id   = link_info.get(    "id"    , None)
            endpoints = link_info.get("endpoints" ,  [] )

            params_dict = link_info.get("params", {})
            bw             = params_dict.get("bw", None)
            delay          = params_dict.get("delay", None)
            loss           = params_dict.get("loss", 0)
            jitter         = params_dict.get("jitter", None)
            max_queue_size = params_dict.get("max_queue_size", None)
            
            
            if len(endpoints) == 2:
                link_node1id , link_node2id = endpoints[:2]

                link_node1 = Hosts.get(link_node1id) or Switches.get(link_node1id) or Dockers.get(link_node1id) or Routers.get(link_node1id) or None
                link_node2 = Hosts.get(link_node2id) or Switches.get(link_node2id) or Dockers.get(link_node2id) or Routers.get(link_node2id) or None

                if link_node1 and link_node2:
                    Links[link_id] = self.ContainerNet.addLink(
                        link_node1, 
                        link_node2, 
                        cls=TCLink, 
                        bw=bw, 
                        delay=delay, 
                        loss=loss, 
                        jitter=jitter, 
                        max_queue_size=max_queue_size
                        )


    def StartUp(self , term_enable=False , visualize_enable=False) : 
        self.ContainerNet.start()
        self.ThreadofRestAPI.start()

        if term_enable : 
            self.ThreadofXterm = subprocess.Popen(["qterminal"] , stderr=subprocess.DEVNULL)
        else : 
            self.ThreadofXterm = None
    
        if visualize_enable : 
            self.NetworkVisualizer = MimicEditor(
                mn_file      = self.MNFile       , 
                containernet = self.ContainerNet , 
            )
            self.NetworkVisualizer.canvas.mainloop()


    def ShutDown(self , exctype=SystemExit) : 
        if self.ThreadofRestAPI != None : 
            tid = ctypes.c_long(self.ThreadofRestAPI.ident)
            if not inspect.isclass(exctype) : 
                exctype = type(exctype)
            res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
            if res == 0:
                raise ValueError("invalid thread id")
            elif res != 1:
                # """if it returns a number greater than one, you're in trouble,
                # and you should call it again with exc=NULL to revert the effect"""
                ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
                raise SystemError("PyThreadState_SetAsyncExc failed")

        if self.ThreadofXterm is not None : 
            self.ThreadofXterm.terminate()
            self.ThreadofXterm.wait     ()

        if hasattr(self , "NetworkVisualizer") : 
            del self.NetworkVisualizer

        cmd = 'sudo mn -c'
        os.system(cmd)
        
    # ---------------------------------------------------------------------------------------------------

    '''functions from self.route (basic operations : add/del operation)'''

    def add_host(self , host_name) :
        self.LogInfo and print(f"Now in add_host() , host_name={host_name}")

        if any(str(host_name) == str(host.name) for host in self.net.hosts) : 
            print("Host is already in the network")
            return
        
        if self.net.addHost(name=host_name) : 
            (self.NetworkVisualizer) and self.NetworkVisualizer.AddHost(host_name=host_name , location_x=1055 , location_y=224)
            print(f"{host_name} is added into the network")


    
    def add_docker(self , node_name) : 
        self.LogInfo and print("Now in add_host(), host_name=" ,       node_name         )
        self.LogInfo and print(   "request.json['params']="    , request.json['params']  )
        self.ContainerNet.addDocker    (       name=node_name           , **request.json['params'])



    def add_link(self , link_name) : 
        self.LogInfo and print("Now in add_link(), link_name=" , link_name)
        nodes = link_name.split("-")
        node1 , node2 = nodes  [ :2]

        if self.ContainerNet.addLink(node1=node1 , node2=node2) : 
            print(f"Add Link node1<{node1}>----node<{node2}> successfully")



    def del_host(self, host_name) : 
        self.LogInfo and print("Now in del_host() , host_name=", host_name)
        for host in self.net.hosts:
            if str(host_name) == str(host.name) : 
                self.net.removeHost(name = host_name) and print(host_name, "is deleted from the network")
                (self.NetworkVisualizer) and self.NetworkVisualizer.DelHost(host_name)
                return 
        print(host_name,"is not in the network")



    def del_docker(self, node_name):
        print("in del_docker(), host_name=", node_name)
        node = self.net[node_name]
        try:
            self.net.delNode(node)
            subprocess.run(['docker', 'rm', '-f', node_name])
            return {'status' : 'success', 'node' : node_name}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}



    def del_link(self, link_name) : 
        self.LogInfo and print("Now in del_link()" , "node1=", node1, "node2=", node2)
        nodes=link_name.split("-")
        node1 , node2 = nodes[ :2]

        print("in del_link()" , "node1=" , node1 , "node2=", node2)
        self.net.removeLink(node1=node1 , node2=node2)
        print("in del_link()" , "node1=" , node2 , "node2=", node1)  
        self.net.removeLink(node1=node2 , node2=node1)



    def del_docker(self, node_name):
        print("in del_docker(), host_name=", node_name)
        node = self.net[node_name]
        try : 
            self.net.delNode(node)
            subprocess.run(['docker', 'rm', '-f', node_name])
            return {'status': 'success', 'node': node_name}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}


    # ---------------------------------------------------------------------------------------------------


    def _get(self, url):
        print("in _get(), url=", url)
        try:
            res = requests.get(f'{self.server_url}{url}', verify=False)
            logging.debug(res.text)
            return res.json()
        except Exception as e:
            logging.error(f'GET PROBLEM <{self.server_url}{url}> : {e}')
            return None


    def _post(self, url, json_text):
        print("in _post(), url=", url, "json_text=", json_text)
        try:
            res = requests.post(
                f'{self.server_url}{url}',
                json=json.loads(json_text),
                verify=False)
            try:
                logging.info(res.text)
                return res.json()
            except:
                return res.text
        except Exception as e:
            logging.error(
                f'POST PROBLEM <{self.server_url}{url}> <{json_text}>: {e}')
            return None


    def list_nodes(self):        
        myurl = f"/nodes"
        return self._get(url=myurl)  
     

    def list_switches(self):
        myurl = f"/switches"
        return self._get(url=myurl)      
    

    def list_hosts(self):
        myurl = f"/hosts"
        return self._get(url=myurl)    
     

    def host_down(self, node_name):  
        json_text = '''
        {
          "status":"down"
        }
        '''
        myif=node_name+str("-eth0")
        myurl = f"/nodes" + "/" + node_name + "/" + myif
        return self._post(url=myurl, json_text=json_text)   
     
     
    def host_up(self, node_name):  
        json_text = '''
        {
          "status":"up"
        }
        '''
        myif=node_name+str("-eth0")
        myurl = f"/nodes" + "/" + node_name + "/" + myif
        return self._post(url=myurl, json_text=json_text)       


    def ChangeHostIP(self , node_name , new_ip , new_netmask='24'):
        node = self.net[node_name]

        node.setIP(new_ip , prefixLen=int(new_netmask))
        node.params['ip'] = new_ip

        print(f"{node_name} 's IP change to {new_ip}/{new_netmask}")

    # ---------------------------------------------------------------------------------------------------



if __name__ == "__main__" : 
    Network = AI_MininetRest(
        topo_jsonpath   = "../Platform-Data/topo.json" , 
        topo_mnpath     = "../Platform-Data/topo.mn"   , 
    )

    try : 
        Network.StartUp(
            term_enable=False , 
            visualize_enable=False , 
        )
    finally : 
        Network.ShutDown()