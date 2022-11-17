import prior_only
import shutil
import os
import LoRaSim_randomSF


import csv
import numpy as np
import matplotlib.pyplot as plt
import random
from plotter import *


sim_times = 10

nrNodes = 500 # if single run
avgSendTime = 5*60*1000
simtime = 3*60*60*1000
plsize = 20
full_collision = 1

max_Dist = 5000
regular_placement=0

# 100:7 1500:8 2000:9 2500:10 3500:11 4500:12


# attack_start = 1*60*60*1000
attack_start = 0

temp = None
for i in range(sim_times):
    sf_file,results_file,results_file_on_time,result = prior_only.run(nrNodes,avgSendTime,simtime,plsize,\
                                                                    max_dist = max_Dist,\
                                                                    regular_placement=regular_placement,\
                                                                    sim_times=sim_times)
    # sf_file,results_file,results_file_on_time,result = LoRaSim_randomSF.run(nrNodes,avgSendTime,simtime,plsize,\
    #                                                                 max_dist = max_Dist,\
    #                                                                 regular_placement=regular_placement,\
    #                                                                 sim_times=sim_times,\
    #                                                             greedy_node=greedy_node,\
    #                                                             greedy_list=greedy_list,\
    #                                                             attack_start=attack_start)
    if temp is None:
        temp = result
    else: 
        temp = np.vstack((temp,result))
avg = list(np.mean(temp, axis=0))        
avg.insert(0,nrNodes)

print(["nrNodes","total sent","new packets","resend tentatives",\
            "packets abandonned","collisions","lost packets",\
            "receive ratio(based on total sent)","ack ratio(based on new packets)",\
            "Acked number","Energy(J)","energy_per_100_ack(J)","effective packets ratio","energy_per_100_new_packet"])
print(list(avg))
a = os.listdir("./data/for_massive")
for j in a:
    if os.path.splitext(j)[1] == '.csv':
        try:
            shutil.move("./data/for_massive/" + j, "./data/for_massive/prior_only/normal/" + j)
        except:
            os.makedirs("./data/for_massive/prior_only/normal/")
            shutil.move("./data/for_massive/" + j, "./data/for_massive/prior_only/normal/" + j)