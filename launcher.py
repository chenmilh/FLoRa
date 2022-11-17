import simpy
import math

from Nodes import Node
from PriorKnowledgeNode import PriorKnowledgeNode

from Gateway import Gateway
from Network import Network
from NetworkWithLoRaLOFT import NetworkWithLoRaLOFT

from Environment import LoRaEnvironment


def run(max_dist,GW_num,Node_num,period,plsize,sim_time):
    lora_env = LoRaEnvironment()
    lora_env.get_env_from_json()

    network = Network(environment=lora_env)
    # network.LoRaLOFT.load_model("./models_globecom.json")

    for i in range(GW_num):
        network.GW_list[i] = Gateway(i,network.environment.channel_list,network.environment.second_channel)
    for i in range(Node_num):
        n = PriorKnowledgeNode(i,period,network.environment.channel_list,plsize+network.environment.lora_header,random_transmit=True)
        n.set_packet(confirmed=True,adr_enabled=False)
        network.nodes_list[i] = n
    
    network.random_placement(max_dist)
    for node in network.nodes_list.values():
        mindist =  max_dist
        for gw in network.GW_list.values():
            dist = math.sqrt((node.x-gw.x)**2+(node.y-gw.y)**2+(node.z-gw.z)**2)
            if(dist < mindist):
                mindist = dist
        node.Initialize_sf(mindist,network) 
    
    env = simpy.Environment()
    for gw in network.GW_list.values():
        env.process(gw.forward(network,env))
    for node in network.nodes_list.values():
        env.process(node.transmit(env,network))
    # env.process(network.LoRaLOFT.detect_start(env))
    env.run(until=sim_time)

    nodes = network.nodes_list.values()
    for n in nodes:
        n.statistic.sim_end()
    
    sent = sum(n.statistic.total_send for n in nodes)
    diff_packet = sum(n.statistic.packet_cnt for n in nodes)
    resend_packet = sum(n.statistic.retransmissions for n in nodes)
    rest_packet = sum(n.statistic.abandoned for n in nodes)
    
    energy = sum(node.statistic.energy for node in nodes)
    nrCollisions = sum(node.statistic.collisions for node in nodes)
    nrReceived = sum(node.statistic.received for node in nodes)
    nrACKed = sum(node.statistic.acked for node in nodes)
    nrLost = sum(node.statistic.lost for node in nodes)
    nrACKLost = sum(node.statistic.ack_lost for node in nodes)
    
    print("energy (in J): ", energy)
    print("\n")
    SFdistribution = [0]*6
    for n in nodes:
        SFdistribution[n.packet.sf-7]+=1

    print("SFdistribution: ", SFdistribution)
    
    # SFdistribution = [0]*6
    # for n in network.LoRaLOFT.black_list.keys():
    #     SFdistribution[network.nodes_list[n].packet.sf-7]+=1

    print("attacker SF: ", SFdistribution)

    print("****************************************")
    print("actual packets: ", diff_packet)
    print("resend packets: ", resend_packet)
    print("sent packets: ", sent)
    print("non sent packets: ", rest_packet)
    print("collisions: ", nrCollisions)
    print("received packets: ", nrReceived)
    print("received and acked packets: ", nrACKed)
    print("lost packets: ", nrLost)
    print("ack lost packets: ", nrACKLost)

    # data extraction rate
    der2 = (nrReceived)/float(sent) if sent!=0 else 0
    print("PDR:", der2)
    der3 = (nrACKed)/float(diff_packet) if diff_packet!=0 else 0
    print("PSR:", der3)
    print("****************************************")
    print("\n")
    
    return network


