# M2-Editor = Mininet & Mimic Edit software

import json
import time
import threading
import multiprocessing

from Network.Visualization.miniedit   import MiniEdit
from Network.Visualization.miniedit   import *

class MimicEditor(MiniEdit) : 
    def __init__(
        self , parent=None , containernet=None , mn_file=None , 
        cheight=600 , cwidth=1000
    ) : 
        super().__init__(parent , cheight , cwidth)

        self.TopoFile   = mn_file

        self.net = containernet

        self.hostPopup.add_separator()
        self.hostPopup.add_command(label='Terminal', font=self.font, command=self.xterm )

        self.NewestItemID = 0
        self.TopoItemID = {
            "Controller" : {} , 
            "Docker"     : {} , 
            "Host"       : {} , 
            "Switch"     : {} , 
            "Link"       : {}
        }

        self.loadTopology (mn_file = mn_file)
        self.ContainerNet = containernet

    # -----------------------------------------------------------------------------------------------------

    '''Topo Loading'''

    def loadTopology(self , mn_file="Platform-Data/topo.mn") : 
        c = self.canvas

        if not mn_file : 
            myFormats = [
                ('Mininet Topology','*.mn'),
                ('All Files','*'),
            ]
            f = tkFileDialog.askopenfile(filetypes=myFormats, mode='rb')
            if f is None:
                return
            self.newTopology()
            loadedTopology = json.load(f)

        else : 
            with open(mn_file, 'r') as f:
                loadedTopology = json.load(f) 

        # Load application preferences
        if 'application' in loadedTopology:
            self.appPrefs.update(loadedTopology['application'])
            if "ovsOf10" not in self.appPrefs["openFlowVersions"] : 
                self.appPrefs["openFlowVersions"]["ovsOf10"] = '0'
            if "ovsOf11" not in self.appPrefs["openFlowVersions"] : 
                self.appPrefs["openFlowVersions"]["ovsOf11"] = '0'
            if "ovsOf12" not in self.appPrefs["openFlowVersions"] : 
                self.appPrefs["openFlowVersions"]["ovsOf12"] = '0'
            if "ovsOf13" not in self.appPrefs["openFlowVersions"] : 
                self.appPrefs["openFlowVersions"]["ovsOf13"] = '0'
            if "sflow" not in self.appPrefs   :
                self.appPrefs["sflow"]   = self.sflowDefaults
            if "netflow" not in self.appPrefs :
                self.appPrefs["netflow"] = self.nflowDefaults

        '''Load Components in load computer'''
        self.LoadControllers(loadedTopology , c) # Load  controllers
        self.LoadHosts      (loadedTopology , c) # Load  hosts
        self.LoadSwitches   (loadedTopology , c) # Load  switches
        self.LoadLinks      (loadedTopology , c) # Load  links

        f.close()



    def LoadControllers(self , loadedTopology , c) : 
        if 'controllers' in loadedTopology : 
            if loadedTopology['version'] == '1' : 
                # This is old location of controller info
                hostname                               = 'c0'
                self.controllers                       = {}
                self.controllers[hostname]             = loadedTopology['controllers']['c0']
                self.controllers[hostname]['hostname'] = hostname
                self.addNode('Controller', 0, float(30), float(30), name=hostname)
                icon = self.findWidgetByName(hostname)
                icon.bind('<Button-3>', self.do_controllerPopup )
                
                self.TopoItemID["Controller"][hostname] = self.NewestItemID = self.NewestItemID + 1

            else:
                controllers  = loadedTopology ['controllers']
                for controller in controllers : 
                    hostname = controller['opts']['hostname']
                    x        = controller[ 'x'  ]
                    y        = controller[ 'y'  ]
                    self.addNode('Controller' , 0 , float(x) , float(y) , name=hostname)
                    self.controllers[hostname] = controller['opts']
                    icon = self.findWidgetByName(hostname)
                    icon.bind('<Button-3>' , self.do_controllerPopup)

                    self.TopoItemID["Controller"][hostname] = self.NewestItemID = self.NewestItemID + 1



    def LoadHosts(self , loadedTopology , c) : 
        hosts = loadedTopology['hosts']
        for host in hosts:
            nodeNum  = host['number']
            hostname = 'h' + nodeNum
            if 'hostname' in host['opts'] : 
                hostname = host  ['opts']['hostname']
            else : 
                host['opts']['hostname'] = hostname
            if 'nodeNum' not in host['opts'] : 
                host['opts']['nodeNum'] = int(nodeNum)
            x = host[ 'x' ]
            y = host[ 'y' ]
            if host['opts'].get('nodeType') == 'Docker' : 
                self.addNode('Docker' , nodeNum , float(x) , float(y) , name=hostname)
            else:
                self.addNode( 'Host'  , nodeNum , float(x) , float(y) , name=hostname)

            # Fix JSON converting tuple to list when saving
            if 'privateDirectory' in host['opts'] : 
                newDirList = []
                for privateDir in host['opts']['privateDirectory'] : 
                    if isinstance( privateDir , list ) : 
                        newDirList.append((privateDir[0] , privateDir[1]))
                    else:
                        newDirList.append(privateDir)
                host['opts']['privateDirectory'] = newDirList
            self.hostOpts[hostname] = host['opts']
            icon = self.findWidgetByName(hostname)
            if host['opts'].get('nodeType') == 'Docker':
                icon.bind('<Button-3>' , self.do_dockerPopup )
            else:
                icon.bind('<Button-3>' ,  self.do_hostPopup  )

            self.TopoItemID["Host"][hostname] = self.NewestItemID = self.NewestItemID + 1



    def LoadSwitches(self , loadedTopology , c) : 
        switches = loadedTopology['switches']
        for switch in switches : 
            nodeNum  = switch['number']
            hostname = 's'  +  nodeNum
            if 'controllers' not in switch['opts'] : 
                switch['opts']['controllers'] =    []
            if 'switchType'  not in switch['opts'] : 
                switch['opts']['switchType' ] = 'default'
            if    'hostname'     in switch['opts'] : 
                hostname = switch['opts']['hostname']
            else:
                switch['opts']['hostname'] = hostname
            if 'nodeNum' not in switch['opts'] : 
                switch['opts']['nodeNum'] = int(nodeNum)
            x = switch['x']
            y = switch['y']
            if switch['opts']['switchType'] == "legacyRouter" : 
                self.addNode('LegacyRouter' , nodeNum , float(x) , float(y) , name=hostname)
                icon = self.findWidgetByName(hostname)
                icon.bind('<Button-3>', self.do_legacyRouterPopup )
            elif switch['opts']['switchType'] == "legacySwitch" : 
                self.addNode('LegacySwitch' , nodeNum , float(x) , float(y) , name=hostname)
                icon = self.findWidgetByName(hostname)
                icon.bind('<Button-3>' , self.do_legacySwitchPopup )
            else:
                self.addNode('Switch' , nodeNum , float(x) , float(y) , name=hostname)
                icon = self.findWidgetByName(hostname)
                icon.bind('<Button-3>', self.do_switchPopup )
            self.switchOpts[hostname] = switch['opts']

            self.TopoItemID["Switch"][hostname] = self.NewestItemID = self.NewestItemID + 1

            # create links to controllers
            if int(loadedTopology['version']) > 1:
                controllers = self.switchOpts[hostname]['controllers']
                for controller in controllers:
                    dest    = self.findWidgetByName(controller)
                    if dest is None or dest not in self.widgetToItem:
                        print(f"Warning: Controller '{controller}' not found, skipping")
                        continue
                    dx , dy = self.canvas.coords   ( self.widgetToItem[ dest ] )
                    self.link = self.canvas.create_line(
                        float(x)       ,
                        float(y)       ,
                        dx             ,
                        dy             ,
                        width =   4    ,
                        fill  = 'red'  ,
                        dash  = (6 , 4 , 2 , 4) ,
                        tag   = 'link' 
                    )
                    c.itemconfig(self.link, tags=c.gettags(self.link)+('control',))
                    self.addLink( icon, dest, linktype='control' )
                    self.createControlLinkBindings()
                    self.link = self.linkWidget = None
            else:
                dest    = self.findWidgetByName('c0')
                if dest is None or dest not in self.widgetToItem:
                    print(f"Warning: Default controller 'c0' not found, skipping")
                    continue
                dx , dy = self.canvas.coords   ( self.widgetToItem[ dest ] )
                self.link = self.canvas.create_line(
                    float(x)       ,
                    float(y)       ,
                    dx             ,
                    dy             ,
                    width =   4    ,
                    fill  = 'red'  ,
                    dash  = (6 , 4 , 2 , 4) , 
                    tag   = 'link' 
                )
                c.itemconfig(self.link, tags=c.gettags(self.link)+('control',))
                self.addLink( icon, dest, linktype='control' )
                self.createControlLinkBindings()
                self.link = self.linkWidget = None



    def LoadLinks(self , loadedTopology , c) : 
        links = loadedTopology['links']
        for link in links:
            srcNode = link['src']
            src     = self.findWidgetByName(srcNode)
            if src is None:
                print(f"Warning: Source node '{srcNode}' not found, skipping link")
                continue
            if src not in self.widgetToItem:
                print(f"Warning: Source widget '{srcNode}' not in widgetToItem, skipping link")
                continue
            sx , sy = self.canvas.coords   ( self.widgetToItem[ src ] )

            destNode = link['dest']
            dest     = self.findWidgetByName(destNode)
            if dest is None:
                print(f"Warning: Destination node '{destNode}' not found, skipping link")
                continue
            if dest not in self.widgetToItem:
                print(f"Warning: Destination widget '{destNode}' not in widgetToItem, skipping link")
                continue
            dx , dy  = self.canvas.coords   ( self.widgetToItem[ dest]  )

            self.link = self.canvas.create_line( 
                sx , sy , dx , dy , width=4 ,
                fill = 'blue'  , tag = 'link' 
            )
            c.itemconfig(self.link, tags=c.gettags(self.link)+('data',))
            self.addLink( src, dest, linkopts=link['opts'] )
            self.createDataLinkBindings()
            self.link = self.linkWidget = None

            self.TopoItemID["Link"][f"{link['src']}-{link['dest']}"] = self.NewestItemID = self.NewestItemID + 1


    # -------------------------------------------------------------------------------------------------------------------

    '''Make sure icon can show details and run cmd'''

    def do_hostPopup(self, event):
        # display the popup menu
        if self.net is not None:
            try:
                self.hostPopup.tk_popup(event.x_root, event.y_root, 0)
            finally:
                # make sure to release the grab (Tk 8.0a1 only)
                self.hostPopup.grab_release()
        else:
            try:
                self.hostRunPopup.tk_popup(event.x_root, event.y_root, 0)
            finally:
                # make sure to release the grab (Tk 8.0a1 only)
                self.hostRunPopup.grab_release()



    def hostDetails( self, _ignore=None ):
        if ( self.selection is None or self.selection not in self.itemToWidget ) : 
            return
        widget = self.itemToWidget  [ self.selection ]
        name   = widget             [     'text'     ]
        tags   = self.canvas.gettags( self.selection )
        if 'Host' not in tags:
            return

        prefDefaults = self.hostOpts[name]
        hostBox      = HostDialog   (self, title='Host Details', prefDefaults=prefDefaults)
        self.master.wait_window(hostBox.top)

        if hostBox.result : 
            newHostOpts = {'nodeNum' : self.hostOpts[name]['nodeNum']}
            newHostOpts   ['nodeType'] = "Host"
            newHostOpts   [  'sched' ] = hostBox.result['sched']

            fields = [
                "startCommand" , "stopCommand" , "cpu" , "cores" ,     "hostname"   , 
                "defaultRoute" ,  "ip" , "externalInterfaces"    , "vlanInterfaces" , 
                "privateDirectory"
            ]

            for field in fields : 
                if len(hostBox.result[field]) > 0 : 
                    if field ==    "cpu"   : 
                        newHostOpts[field] = float(hostBox.result[field]) 
                        continue
                    if field == "hostname" : 
                        newHostOpts[field]  = hostBox.result[  field   ]
                        name                = hostBox.result['hostname']
                        widget     ['text'] = name
                        continue

                    newHostOpts[field] = hostBox.result[field]

            self.hostOpts[name] = newHostOpts
            info( 'New host details for ' + name + ' = ' + str(newHostOpts), '\n' )

    # -------------------------------------------------------------------------------------------------------------------

    '''Bind Container CLI interface while click run button in M2Editor GUI interface'''

    def start( self ) : # reference code : miniedit -> Class MiniEdit.start( self )
        "Start network."

        if self.net is None:
            print("<-Warning Visualization/M2Editor:301->  Containernet CLI is not bind with M2Editor")
            return

        else : 
            from mininet.cli import CLI
            print("\n\n~~~~~~~~~~~~~~~eXe CLI~~~~~~~~~~~~~~~~~~")
            CLI(self.net)

    # -------------------------------------------------------------------------------------------------------------------

    '''Topo Host Operator'''

    def AddHost(self , host_name , host_ip="127.0.0.1" , location_x=None , location_y=None) : 
        with open(self.TopoFile , 'r') as file : 
            MNInfo = json.load(file)

        node_number = (max(int(host["number"]) for host in MNInfo["hosts"])+1) 

        NewHost = {
            "number" : str(node_number)     ,
            "opts"   : {
                "hostname" :   host_name    ,
                "nodeNum"  :  node_number   ,
                "ip"       :    host_ip     ,
                "nodeType" :    "Host"      ,
                "sched"    :    "host"
            } , 
            "x" : str(location_x) ,
            "y" : str(location_y)
        }

        MNInfo["hosts"].append(NewHost)

        with open(self.TopoFile , 'w') as file:
            json.dump(MNInfo, file, indent=4)

        # self.loadTopology(mn_file=self.TopoFile)
        self.addNode("Host" , str(node_number) , location_x , location_y , host_name)
        self.hostOpts[host_name] = NewHost['opts']
        icon = self.findWidgetByName(host_name)
        icon.bind("<Button-3>" , self.do_hostPopup)
        self.TopoItemID["Host"][host_name] = self.NewestItemID = self.NewestItemID + 1



    def DelHost(self , host_name) : 
        self.selection = self.TopoItemID["Host"][host_name]
        self.deleteSelection(_event=None)
        del self.TopoItemID["Host"][host_name]
        # print(self.TopoItemID)