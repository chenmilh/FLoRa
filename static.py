import os
import numpy as np
import csv

class static():
    def __init__(self,x,y,is_dynamic = False):
        self.x = x
        self.y = y
        self.is_dynamic = is_dynamic
        self.init_sf = 0
        self.final_sf = 0
        self.total_send = 0
        self.new_packet = 0
        self.retransmissions = 0
        self.received = 0
        self.acked = 0
        self.collisions = 0
        self.lost = 0
        self.receive_ratio = 0
        self.ack_ratio = 0
        self.effective_send = 0
        self.energy = 0
        self.energy_per100_ack = 0
    
    def sim_end(self):
        self.receive_ratio = (self.received)/float(self.total_send) if self.total_send!=0 else 0
        self.ack_ratio = (self.acked)/float(self.new_packet) if self.new_packet!=0 else 0
        self.effective_send = (self.new_packet)/float(self.total_send) if self.total_send!=0 else 0
        self.energy_per100_ack = 100*self.energy/(self.acked) if self.acked !=0 else 100*self.energy
    


