import numpy as np

class Statistic():
    def __init__(self):
        self.total_send = 0
        self.packet_cnt = 0
        self.abandoned = 0
        self.retransmissions = 0
        self.received = 0
        self.acked = 0
        self.collisions = 0
        self.ack_lost = 0
        self.lost = 0
        self.perror = 0
        self.receive_ratio = 0
        self.ack_ratio = 0
        self.energy = 0
        self.energy_per100_ack = 0
    
    def sim_end(self):
        self.receive_ratio = (self.received)/float(self.total_send) if self.total_send!=0 else 0
        self.ack_ratio = (self.acked)/float(self.packet_cnt) if self.packet_cnt!=0 else 0
        self.energy_per100_ack = 100*self.energy/(self.acked) if self.acked !=0 else 100*self.energy