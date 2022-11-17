from LoRaUtils import *
class Packet():
    def __init__(self,plsize,sf,bw,cr,ptx,freq):
        #PHY info
        self.sf = sf
        self.bw = bw
        self.cr = cr
        self.freq = freq
        self.ptx = ptx
        self.plsize = plsize
        self.rectime = 0
        self.get_air_time()
        
    def get_air_time(self):
        self.rectime = airtime(self.sf,self.cr,self.plsize,self.bw)
    
class ULPacket(Packet):
    def __init__(self,senderId,plsize,sf,downlink_sf,bw,cr,ptx,freq,adr_enabled):
        #PHY info
        super(ULPacket,self).__init__(plsize,sf,bw,cr,ptx,freq)
        self.downlink_sf = downlink_sf
        
        self.senderId = senderId
        self.packetId = None
        self.add_time = None
        self.confirmed = False

        self.packet_cnt = 0
        self.trans_cnt = 0
        
        # ADR part
        self.adr_enabled = adr_enabled
        self.adr_req = 0
        self.adr_cnt = 0
        
        self.received = True
        self.ACKed = True

class DLPacket(Packet):
    def __init__(self,receiverId,plsize,sf,bw,cr,ptx,freq,mac_command=False):
        #PHY info
        super(DLPacket,self).__init__(plsize,sf,bw,cr,ptx,freq)
        
        self.senderId = None
        self.receiverId = receiverId
        self.DLwindow = 1
        self.adr_ack = 0
        self.adr_sf = 7
        self.adr_ptx=14
        self.ack = 0
        self.mac_command = mac_command
    
    def set_sf(self,sf):
        self.sf = sf
        self.get_air_time()