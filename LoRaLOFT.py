import string
import numpy as np
import json,base64,pickle
from sklearn.neighbors import LocalOutlierFactor
import csv

class LoRaLOFT():
    def __init__(self,interval = 0):
        self.nodes = {}
        self.dector = None
        self.black_list = {}
        self.block_proba = {0:0,1:0.9,2:0.95,3:1}
        self.renew_interval = interval
        self.renew_counter = 1
    
    def load_model(self,path:string):
        self.dector = Detector()
        with open(path, 'r') as f:
            dict_loaded = json.load(fp=f)
        for sf in range(7,13):
            self.dector.thres_dict[sf] = dict_loaded["thres"][str(sf)]
            decoded_model = base64.b64decode(dict_loaded["classifiers"][str(sf)].encode('utf-8'))
            loaded_model = pickle.loads(decoded_model)
            self.dector.cls_dict[sf] = loaded_model
    
    def clear_nodes(self):
        self.nodes = {}
        self.black_list = {}
    
    def detect_and_renew(self,detect_time):
        # self.renew_counter -= 1
        # if self.renew_counter == 0:
        #     self.black_list = {}
        suspect_list = self.dector.detect(self.nodes,detect_time)
        for idx in self.nodes.keys():
            if idx in suspect_list:
                if idx not in self.black_list.keys():
                    self.black_list[idx] = 1
                else:
                    if self.black_list[idx] < 3:
                        self.black_list[idx] += 1
            else:
                if idx in self.black_list.keys():
                    self.black_list[idx] -= 1
                    if self.black_list[idx] == 0:
                        self.black_list.pop(idx)
        if self.renew_counter==0:
            self.renew_counter=1
            for id in self.nodes.keys():
                self.nodes[id]["received"] = 0
                self.nodes[id]["energy"] = 0
                self.nodes[id]["activate_time"] = detect_time
        
    def detect_start(self,env):
        if(self.renew_interval>0):
            while True:
                yield env.timeout(self.renew_interval)
                self.detect_and_renew(env.now)
                print(self.black_list)
                print("---")
                

class Detector():
    def __init__(self):
        self.cls_dict = {}
        self.thres_dict = {}

    
# {idx:{received,energy,sf}}
    def detect(self,nodes:dict,detect_time):
        # node_nums = len(nodes)
        first_score = {}
        # test = np.array([[idx]+[nodes[idx]["received"]*coeff]+[nodes[idx]["energy"]*coeff]+[nodes[idx]["sf"]] for idx in nodes.keys()])
        # with open("./data/for_massive/detect_test/test.csv", 'w',newline ='') as file:
        #     writer = csv.writer(file,delimiter=',')
        #     writer.writerows(np.array(test))
        sups_score = []
        abnormals_index=[]
        lowest_normal=9999
        for idx in nodes.keys():
            sf = int(nodes[idx]["sf"])
            coeff = 60*60*1000/(detect_time-nodes[idx]["activate_time"])
            to_classified = np.array([nodes[idx]["received"]*coeff,nodes[idx]["energy"]*coeff]).reshape(1, -1)
            if sf < 10:
                to_compare = to_classified[0][1]
            else:
                to_compare = to_classified[0][0]                
            cls = self.cls_dict[sf]
            first_score[idx] = cls.decision_function(to_classified)
            if to_compare >self.thres_dict[sf]:
                sups_score.append(first_score[idx])
                abnormals_index.append(idx)
            else:
                if first_score[idx] < lowest_normal:
                    lowest_normal=first_score[idx]
        sups_score.append(lowest_normal)
        abnormal_score = np.array(sups_score)
        outlier_index = []
        if len(abnormal_score)>0:
            abnormal_mean = np.mean(abnormal_score)
            abnormal_std = np.std(abnormal_score)
            outlier_thres = abnormal_mean+abnormal_std

            for idx in abnormals_index:
                if(first_score[idx]<outlier_thres):
                    outlier_index.append(idx)
            if len(outlier_index)>0:
                return outlier_index
            else:
                return abnormals_index
        return []