
import math
from Nodes import Node

class PriorKnowledgeNode(Node):
    def __init__(self,nodeid, period,channel_list,plsize,Ptx=14,CodingRate=1,Bandwidth=125,random_transmit = False,adr_enabled=False):
       super(PriorKnowledgeNode,self).__init__(nodeid, period,channel_list,plsize,Ptx,CodingRate,Bandwidth,random_transmit,adr_enabled) 
    
    def Initialize_sf(self,distance,network,thres=0.75):
        Lpl = network.environment.Lpld0 + 10*network.environment.gamma*math.log10(distance/network.environment.d0)
        Prx = self.packet.ptx - network.environment.GL - Lpl
        
        possibility_of_sf = [0]*6
        for i in range(0,6):  # SFs
            sensi_sf = network.environment.sensi[i, [125,250,500].index(self.packet.bw) + 1]
            z = sensi_sf - Prx    
            possibility_of_sf[i] = 1 - 0.5*(1+math.erf(z/(network.environment.var*math.sqrt(2))))
        result_sf = 12
        for i in range(5,-1,-1):
            if possibility_of_sf[i] > thres:
                result_sf = i+7
        
        self.set_sf(result_sf)
        self.set_downlink_sf(result_sf)