import numpy as np
import math
import random
from Packet import DLPacket

class Network():
    def __init__(self,environment):
        self.GW_list = {}
        self.nodes_list = {}
        self.received_packet = {}
        self.dl_buffer = {}
        self.adr_log = {}
        self.environment = environment

    def random_placement(self,maxDist):
        i = 0
        for gw in self.GW_list.values():
            if i == 0:
                gw.x = 0
                gw.y = 0
                i+=1
            else:
                found = 0              
                while (found == 0):
                    a = random.random()
                    b = random.random()
                    posx = (1-a)*maxDist*math.cos(2*math.pi*b)
                    posy = (1-a)*maxDist*math.sin(2*math.pi*b)
                    found = 1
                    for others in self.GW_list.values():
                        if(others.gatewayId==gw.gatewayId):
                            continue
                        dist = np.sqrt(((others.x-posx)**2)+((others.y-posy)**2))
                        if dist < 3:
                            found = 0
                            break
                    if(found == 1):    
                        gw.x = posx
                        gw.y = posy          
                i += 1
        for node in self.nodes_list.values():
            found = 0
            while (found == 0):
                a = random.random()
                b = random.random()
                posx = (1-a)*maxDist*math.cos(2*math.pi*b)
                posy = (1-a)*maxDist*math.sin(2*math.pi*b)
                found = 1
                for others in self.GW_list.values():
                    dist = np.sqrt(((others.x-posx)**2)+((others.y-posy)**2))
                    if dist < 10:
                        found = 0
                        break
                if(found==0):
                    continue
                for others in self.nodes_list.values():
                    dist = np.sqrt(((others.x-posx)**2)+((others.y-posy)**2))
                    if dist < 10:
                        found = 0
                        break
            if(found == 1):    
                node.x = posx
                node.y = posy                                                 
    
    def get_rssi(self,ptx,dist):
        return ptx - self.environment.Lpld0 - 10*self.environment.gamma*math.log10(dist/self.environment.d0) + np.random.normal(0, self.environment.var)               
    
    def UL(self,ulpacket,env):
        sender = self.nodes_list[ulpacket.senderId]
        sensitivity = self.environment.sensi[ulpacket.sf - 7, [125,250,500].index(ulpacket.bw) + 1]
        lost = True
        for gateway in self.GW_list.values():
            # if (gateway.state != 1):
            if (gateway.state>=0):
                dist = math.sqrt((gateway.x-sender.x)**2+(gateway.y-sender.y)**2+(gateway.z-sender.z)**2)
                rssi = self.get_rssi(ulpacket.ptx,dist)
                if(rssi>sensitivity):
                    lost = False
                    gateway.onReceive(ulpacket,rssi,sender,env)
        if(lost):
            sender.statistic.lost += 1
        return

    def DL(self,dlpacket,env):
        sender =  self.GW_list[dlpacket.senderId]
        sensitivity = self.environment.sensi[dlpacket.sf - 7, [125,250,500].index(dlpacket.bw) + 1]
        lost = True
        receiver = self.nodes_list[dlpacket.receiverId]
        if(receiver.state!=1):
            return
        dist = math.sqrt((receiver.x-sender.x)**2+(receiver.y-sender.y)**2+(receiver.z-sender.z)**2)
        rssi = self.get_rssi(dlpacket.ptx,dist)
        if(rssi>sensitivity):
            lost = False
            # receiver.statistic.acked += 1
            # if(dlpacket.freq == 868700000):
            #     print(f"send ACK to {dlpacket.receiverId} in RX2 at {env.now}")
            # else:
            #     print(f"send ACK to {dlpacket.receiverId} in RX1 at {env.now}")
            env.process(receiver.onReceive(dlpacket,self.environment.RX,self.environment.V,env))
            
        if(lost):
            receiver.statistic.ack_lost += 1

    def cal_adr(self,packet,rssi):
        senderId = packet.senderId
        ptx = packet.ptx
        sf = packet.sf
        if(senderId not in self.adr_log.keys()):
            self.adr_log[senderId] = [rssi]
            return ptx,sf
        if(len(self.adr_log[senderId])<20):
            self.adr_log[senderId].append(rssi)
            return ptx,sf
        self.adr_log[senderId].pop(0)
        self.adr_log[senderId].append(rssi)
        max_snr = max(self.adr_log[senderId])+174 - 10*math.log10(packet.bw*1000) - 6
        SNRmargin = max_snr-self.environment.adr_thres[packet.sf]-5
        NStep = int(SNRmargin/3)
        while(NStep!=0):
            if(NStep<0):
                if(ptx<self.environment.max_ptx):
                    ptx = min(self.environment.max_ptx,ptx+3)
                    NStep+=1
                else:
                    return ptx,sf
            if(NStep<0):
                if(sf>7):
                    sf -= 1
                    NStep -= 1
                else:
                    ptx = max(ptx-3,0)
                    NStep -= 1
                    if(ptx == 0):
                        return ptx,sf
        return ptx,sf                   
        
    def process(self,packet_id,env):
        dl_packet = None
        packet = self.received_packet[packet_id]["packet"]
        senderId = packet.senderId
        if(senderId in self.dl_buffer.keys()):
            dl_packet = self.dl_buffer[senderId]
        if(packet.confirmed):
            if(dl_packet is None):
                dl_packet = DLPacket(senderId,self.environment.lora_header,packet.downlink_sf,packet.bw,packet.cr,packet.ptx,packet.freq)
            dl_packet.ack = 1
        yield env.timeout(1000)
        # print(packet.confirmed)
        if(packet.adr_enabled):
            max_rssi = max(self.received_packet[packet_id]["gateway_info"].values())
            ptx,sf = self.cal_adr(packet,max_rssi)
            if(ptx!=packet.ptx or sf!=packet.sf or packet.adr_req):
                if(dl_packet is None):
                    dl_packet = DLPacket(senderId,self.environment.lora_header,packet.downlink_sf,packet.bw,packet.cr,packet.ptx,packet.freq,mac_command=True)
                dl_packet.adr_ack = 1
                dl_packet.adr_sf = sf
                dl_packet.adr_ptx = ptx
        if(dl_packet is None):
            return
        dl_gateway = None
        max_rssi = None
        for gateway_id in self.received_packet[packet_id]["gateway_info"].keys():
            gateway = self.GW_list[gateway_id]
            if(gateway.RX1[packet.freq]["tx"]==0):
                rssi = self.received_packet[packet_id]["gateway_info"][gateway_id]
                if(max_rssi is None or max_rssi<rssi):
                    dl_gateway = gateway
                    max_rssi = rssi
        if(dl_gateway is not None):
            dl_packet.DLwindow=1
            dl_packet.set_sf(packet.downlink_sf)
            dl_packet.senderId = dl_gateway.gatewayId
            self.DL(dl_packet,env)
            env.process(dl_gateway.transmit(dl_packet,dlwindow=1,env=env))
            return
        # print(f"GW RX1 busy for node {dl_packet.receiverId} at freq {dl_packet.freq} ")
        yield env.timeout(1000)
        for gateway_id in self.received_packet[packet_id]["gateway_info"].keys():
            gateway = self.GW_list[gateway_id]
            if(gateway.RX2["tx"]==0):
                dl_gateway = gateway
                break
        if(dl_gateway is not None):
            dl_packet.DLwindow=2
            dl_packet.set_sf(12)
            dl_packet.senderId = dl_gateway.gatewayId
            dl_packet.freq = self.environment.second_channel.freq
            self.DL(dl_packet,env)
            env.process(dl_gateway.transmit(dl_packet,dlwindow=2,env=env))
            return
        # print(f"GW RX2 busy for node {dl_packet.receiverId} at freq {dl_packet.freq} ")
        if(dl_packet.mac_command):
            self.dl_buffer[senderId] = dl_packet
    
    def onReceive(self,packet_info,env):
        packet = packet_info["packet"]
        packet_id = packet.packetId
        rssi = packet_info["rssi"]
        gateway = packet_info["gateway"]
        if(packet_id not in self.received_packet.keys()):
            self.received_packet[packet_id] = {"packet":packet,"gateway_info":{gateway:rssi}}
            env.process(self.process(packet_id,env))
        else:
            self.received_packet[packet_id]["gateway_info"][gateway]=rssi