from LoRaUtils import *
import random
class Gateway():
    def __init__(self,id,channel_list,second_channel,demoduler_number=8):
        self.gatewayId = id
        self.x = 0
        self.y = 0
        self.z = 0
        self.receiving = {}
        self.max_demoduler = demoduler_number
        self.available_demoduler = demoduler_number
        self.ul_buffer = []
        self.forward_trigger = None
        self.RX1 = {}
        self.RX2 = None
        self.state = 0 #0 : idle, 1:transmiting
        
        for channel in channel_list:
            self.RX1[channel.freq] = {"dc":channel.duty_cycle,"tx":0}
        self.RX2 = {"dc":second_channel.duty_cycle,"tx":0}
        
    def processing(self,env,ulpacket,sender):
        duration = ulpacket.rectime
        yield env.timeout(duration)
        succ = True
        collided = self.receiving[ulpacket.packetId]["collided"]
        processed = self.receiving[ulpacket.packetId]["processed"]
        rssi = self.receiving[ulpacket.packetId]["rssi"]

        if(collided):
            succ = False
            sender.statistic.collisions += 1
        if(not processed):
            succ = False
        else:
            if(per(ulpacket.sf,ulpacket.bw,ulpacket.cr,rssi,ulpacket.plsize) > random.uniform(0,1)):
                succ = False
                sender.statistic.perror += 1
            if(self.available_demoduler < self.max_demoduler):
                self.available_demoduler += 1
        self.receiving.pop(ulpacket.packetId)
        if(succ and not ulpacket.received):
            ulpacket.received = True
            sender.statistic.received += 1
            self.ul_buffer.append({"packet":ulpacket,"rssi":rssi,"gateway":self.gatewayId})
            if(self.forward_trigger is None):
                self.forward_trigger = env.event()
            self.forward_trigger.succeed()
            self.forward_trigger = env.event()

    def check_collision(self,ulpacket,rssi):
        collided = False
        if(len(self.receiving)>0):
            for other in self.receiving.values():
                freq_collision = frequencyCollision(ulpacket.freq, other["freq"],ulpacket.bw,other["bw"])
                if(freq_collision and (ulpacket.sf==other["sf"])):
                    if timingCollision(ulpacket.add_time, ulpacket.sf,ulpacket.bw,other["add_time"],other["duration"]):
                        surviver = powerCollision(rssi, other["rssi"])
                        if(surviver != 2):
                            other["collided"]=True
                        if(surviver != 1):
                            collided = True
        return collided
    
    def onReceive(self,ulpacket,rssi,sender,env):
        # check collision
        collided = self.check_collision(ulpacket,rssi)
        self.receiving[ulpacket.packetId]={"freq":ulpacket.freq,"bw":ulpacket.bw,"sf":ulpacket.sf,"add_time":ulpacket.add_time,"duration":ulpacket.rectime,"rssi":rssi,"processed":False,"collided":collided}            
        if(self.available_demoduler>0):
            self.receiving[ulpacket.packetId]["processed"] = True
            self.available_demoduler -= 1
        env.process(self.processing(env,ulpacket,sender))
        return

        
    def forward(self,network,env):
        if(self.forward_trigger is None):
            self.forward_trigger = env.event()
        while True:
            yield self.forward_trigger
            if(len(self.ul_buffer)>0):
                packet_info = self.ul_buffer.pop(0)
                network.onReceive(packet_info,env)
    
    def transmit(self,dl_packet,dlwindow,env):
        self.state = 1
        freq = dl_packet.freq
        if len(self.receiving)>0:
            for p in self.receiving.values():
                p["processed"] = False
        self.available_demoduler = self.max_demoduler
        if(dlwindow==1):
            self.RX1[freq]["tx"]=1
            yield env.timeout(dl_packet.rectime)
            self.state = 0
            yield env.timeout(dl_packet.rectime*(1/self.RX1[freq]["dc"]-self.RX1[freq]["dc"]))
            self.RX1[freq]["tx"]=0
            return
        if(dlwindow==2):
            self.RX2["tx"] = 1
            yield env.timeout(dl_packet.rectime)
            self.state = 0
            yield env.timeout(dl_packet.rectime*(1/self.RX2["dc"]-self.RX2["dc"]))
            self.RX2["tx"]=0
            return            