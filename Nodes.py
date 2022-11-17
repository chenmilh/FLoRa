import random
from LoRaUtils import *
from Statistic import Statistic
from Packet import ULPacket

class Node():
    def __init__(self, nodeid, period,channel_list,plsize,Ptx=14,CodingRate=1,Bandwidth=125,random_transmit = False,adr_enabled=False):
        self.nodeid = nodeid
        self.gwId = -1
        self.x = 0
        self.y = 0
        self.z = 0
        sf = random.randint(7,12)
        self.downlink_sf = sf
        channel = random.choice(channel_list)
        self.duty_cycle = channel.duty_cycle

        self.packet = ULPacket(nodeid,plsize,sf,sf,Bandwidth,CodingRate,Ptx,channel.freq,adr_enabled)
        self.period = period
        self.random_transmit = random_transmit
        self.state = 0 #0:idle, 1:listen, 2:receiving
    
        self.first_window_period = (8 + 4.25)*(2**self.downlink_sf)/(self.packet.bw)
        self.second_window_period = (8 + 4.25)*(2**12)/(self.packet.bw)
        
        self.statistic = Statistic()

        self.received_end = None
    def set_sf(self,sf):
        self.packet.sf = sf
        self.packet.get_air_time()

    def set_downlink_sf(self,sf):
        self.packet.downlink_sf = sf
        self.first_window_period = (8 + 4.25)*(2**self.downlink_sf)/(self.packet.bw)
    
    def set_plsize(self,plsize):
        self.packet.plsize = plsize
        self.packet.rectime = self.packet.get_air_time()
            
    def set_packet(self,sf=None,downlink_sf=None,adr_enabled=None,confirmed=None,plsize=None,freq=None):
        # self.packet.ACKed=False
        if(sf is None):
            sf = self.packet.sf
        if(downlink_sf is None):
            downlink_sf = self.packet.downlink_sf
            
        # set adr    
        if(adr_enabled is None):
            adr_enabled = self.packet.adr_enabled
        elif(adr_enabled != self.packet.adr_enabled):
            self.packet.adr_enabled = adr_enabled
        
        #set plsize
        if(plsize is None):
            plsize = self.packet.plsize
        elif(plsize != self.packet.plsize):
            self.set_plsize(plsize)
            
        # set condirmed
        if(confirmed is None):
            confirmed = self.packet.confirmed
        elif(confirmed != self.packet.confirmed):
            self.packet.confirmed = confirmed       

        # set frequence
        if(freq is None):
            freq = self.packet.freq
        elif(freq != self.packet.freq):
            self.packet.freq = freq

        if(not self.packet.adr_enabled):
            self.packet.adr_cnt = 0
            self.packet.adr_req = 0
        else:
            if(self.packet.adr_cnt < 20):
                self.packet.adr_cnt += 1
            else:
                if(self.packet.adr_req < 5):
                    self.packet.adr_req += 1
                else:
                    sf = min(self.packet.sf + 1,12)
                    downlink_sf = sf
                    self.packet.adr_req = 0
                    
        if(sf != self.packet.sf):
            self.set_sf(sf)
        if(downlink_sf != self.packet.downlink_sf):
            self.set_downlink_sf(downlink_sf)
        
    def transmit(self,env,network):
        yield env.timeout(random.expovariate(1.0/float(60*1000)))
        last_airtime = 0
        spent_time = 0
        # while not self.packet.ACKed:
        while True:
            self.set_packet()
            # print(f"{self.nodeid} finished packet at {env.now}, ACKED {self.packet.ACKed}")
            if(self.packet.confirmed):
                if (not self.packet.ACKed and self.packet.trans_cnt<8):
                    yield env.timeout(max(0,float(last_airtime*((1-self.duty_cycle)/self.duty_cycle))-spent_time)+random.expovariate(1.0/float(2000)))
                    self.packet.trans_cnt += 1
                    self.statistic.retransmissions += 1
                    self.statistic.total_send += 1
                else:
                    if(self.packet.trans_cnt>=8):
                        self.statistic.abandoned += 1
                        self.statistic.packet_cnt += 1
                        self.packet.packet_cnt += 1
                        self.packet.trans_cnt = 0
                    yield env.timeout(max(0,self.period-spent_time,float(last_airtime*((1-self.duty_cycle)/self.duty_cycle))-spent_time))
                    self.statistic.total_send += 1
                    self.packet.trans_cnt += 1
                     
            else:
                yield env.timeout(max(0,self.period-spent_time,float(last_airtime*((1-self.duty_cycle)/self.duty_cycle))-spent_time))
                self.statistic.total_send += 1
                self.statistic.packet_cnt += 1
                self.packet.packet_cnt += 1
                self.packet.trans_cnt = 1
            self.packet.received = False
            self.packet.ACKed = False
            self.packet.packetId = str(self.nodeid)+"_"+str(self.packet.packet_cnt)+"_"+str(self.packet.trans_cnt)
            self.packet.add_time = env.now
            # print(f"{self.nodeid}, send")
            network.UL(self.packet,env)
            # print(f"{self.nodeid} send at {env.now},freq {self.packet.freq}")
            yield env.timeout(self.packet.rectime+1000)
            spent_time = 1000
            # print(f"{self.nodeid} open the first window at {env.now}")
            last_airtime = self.packet.rectime
            self.statistic.energy += self.packet.rectime * network.environment.TX[int(self.packet.ptx)+2] * network.environment.V/1e6
            self.state = 1
            yield env.timeout(self.first_window_period)
            spent_time += self.first_window_period
            if(self.state==2):
                # print(f"get ACK {self.nodeid} in RX1 at {env.now}")
                start_time = env.now
                yield self.received_end
                recv_time = env.now-start_time
                spent_time += recv_time
                continue
            self.state = 1
            self.statistic.energy +=self.first_window_period * network.environment.RX * network.environment.V/1e6
            yield env.timeout(1000-self.first_window_period)
            spent_time += 1000-self.first_window_period
            # print(f"{self.nodeid} open the second window at {env.now}")
            # self.state = 1
            yield env.timeout(self.second_window_period)
            spent_time += self.second_window_period
            if(self.state==2):
                # print(f"get ACK {self.nodeid} in RX2 at {env.now}")
                start_time = env.now
                yield self.received_end
                recv_time = env.now-start_time
                spent_time += recv_time
                continue
            else:
                # print(f"{self.nodeid} No ACK in RX2 at {env.now}")
                self.statistic.energy +=self.second_window_period * network.environment.RX * network.environment.V/1e6
                self.state = 0
                continue
   
    def onReceive(self,packet,RX,V,env):
        # if(packet.freq ==868700000):
            # print(f"{self.nodeid} start ACK RX2 at {env.now}")
        self.state = 2
        self.received_end = env.event()
        self.statistic.energy +=packet.rectime * RX * V/1e6
        yield env.timeout(packet.rectime)
        if(self.packet.confirmed and packet.ack==1):
            self.packet.ACKed = True
            self.statistic.acked += 1
            self.statistic.packet_cnt += 1
            self.packet.packet_cnt += 1
            self.packet.trans_cnt = 0
        if(packet.adr_ack==1):
            self.set_sf(packet.adr_sf)
            self.set_downlink_sf(packet.adr_sf)
            self.packet.ptx = packet.adr_ptx
            self.packet.adr_cnt=0
            self.packet.adr_req = 0
        self.state = 0
        # if(packet.freq ==868700000):
        #     print(f"{self.nodeid} finished ACK RX2 at {env.now}")
        self.received_end.succeed()            
        self.received_end=None
        return
        