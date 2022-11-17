from Network import Network
from LoRaLOFT import LoRaLOFT
from Packet import DLPacket
import random

class NetworkWithLoRaLOFT(Network):
    def __init__(self, environment,detect_interval=30*60*1000):
        super(NetworkWithLoRaLOFT,self).__init__(environment)
        self.LoRaLOFT = LoRaLOFT(detect_interval)
        
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


    def process(self,packet_id,env):
        dl_packet = None
        packet = self.received_packet[packet_id]["packet"]
        senderId = packet.senderId
        if senderId not in self.LoRaLOFT.nodes.keys():
            self.LoRaLOFT.nodes[senderId] = {"received":0,"energy":0,"cumul_energy":0,"sf":packet.sf,"activate_time":env.now-packet.add_time}
        elif(packet.sf != self.LoRaLOFT.nodes[senderId]["sf"]):
            self.LoRaLOFT.nodes[senderId]["sf"] = packet.sf
            self.LoRaLOFT.nodes[senderId]["received"] = 0
            self.LoRaLOFT.nodes[senderId]["previous_energy"] += self.LoRaLOFT.nodes[senderId]["energy"]
            self.LoRaLOFT.nodes[senderId]["energy"] = 0
            self.LoRaLOFT.nodes[senderId]["activate_time"] = env.now-packet.add_time
        else:
            self.LoRaLOFT.nodes[senderId]["received"]+=1
            self.LoRaLOFT.nodes[senderId]["energy"]=self.nodes_list[senderId].statistic.energy-self.LoRaLOFT.nodes[senderId]["cumul_energy"]
        if(len(self.LoRaLOFT.black_list)>0):
            if(packet.senderId in self.LoRaLOFT.black_list.keys()):
                suspect_times = self.LoRaLOFT.black_list[packet.senderId]
                block_proba = self.LoRaLOFT.block_proba[suspect_times]
                x = random.uniform(0,1)
                if x < block_proba:
                    if(senderId in self.dl_buffer.keys()):
                        self.dl_buffer.pop(senderId)
                    return
        if(senderId in self.dl_buffer.keys()):
            dl_packet = self.dl_buffer.pop(senderId)            
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