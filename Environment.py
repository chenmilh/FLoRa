import numpy as np
from LoRaChannel import LoRaChannel
import json

class LoRaEnvironment():
    def __init__(self):
        self.sensi = None
        self.adr_thresh=None
        
        self.max_ptx = None
        self.TX = None
        self.RX = None
        self.V = None
        
        self.channel_list = None
        self.second_channel=None
        
        self.gamma = None
        self.d0 = None
        self.var = None
        self.Lpld0 = None
        self.GL = None
        
        self.lora_header = None
    
    def get_env_from_json(self,file_path='LoRaEnv.json'):
        with open(file_path, 'r') as f:
            dict_loaded = json.load(fp=f)
            f.close()
        sf7 = np.array(dict_loaded['sensi']['sensi_sf7']) if dict_loaded['sensi']['sensi_sf7'] is not None and len(dict_loaded['sensi']['sensi_sf7'])==4 else np.array([7,-123,-120,-117.0])
        sf8 = np.array(dict_loaded['sensi']['sensi_sf8']) if dict_loaded['sensi']['sensi_sf8'] is not None and len(dict_loaded['sensi']['sensi_sf8'])==4 else np.array([8,-126,-123,-120.0])
        sf9 = np.array(dict_loaded['sensi']['sensi_sf9']) if dict_loaded['sensi']['sensi_sf9'] is not None and len(dict_loaded['sensi']['sensi_sf9'])==4 else np.array([9,-129,-126,-123.0])
        sf10 = np.array(dict_loaded['sensi']['sensi_sf10']) if dict_loaded['sensi']['sensi_sf10'] is not None and len(dict_loaded['sensi']['sensi_sf10'])==4 else np.array([10,-132,-129,-126.0])
        sf11 = np.array(dict_loaded['sensi']['sensi_sf11']) if dict_loaded['sensi']['sensi_sf11'] is not None and len(dict_loaded['sensi']['sensi_sf11'])==4 else np.array([11,-134.53,-131.52,-128.51])
        sf12 = np.array(dict_loaded['sensi']['sensi_sf12']) if dict_loaded['sensi']['sensi_sf12'] is not None and len(dict_loaded['sensi']['sensi_sf12'])==4 else np.array([12,-137,-134,-131.0])

        self.sensi = np.array([sf7,sf8,sf9,sf10,sf11,sf12])        
        self.adr_thres = {12:-20, 11:-17.5, 10:-15,9:-12.5, 8:-10, 7:-7.5}
        
        self.max_ptx = dict_loaded['pathlossModel']['Ptx'] if dict_loaded['pathlossModel']['Ptx']>0 else 14
        # compute energy
        # Transmit consumption in mA from -2 to +17 dBm
        self.TX = dict_loaded['energy']['TX'] if dict_loaded['energy']['TX'] is not None and len(dict_loaded['energy']['TX'])==23 else [22, 22, 22, 23,24, 24, 24, 25, 25, 25, 25, 26, 31, 32, 34, 35, 44,82, 85, 90,105, 115, 125]
        self.RX = dict_loaded['energy']['RX'] if dict_loaded['energy']['RX'] > 0 else 16
        self.V = dict_loaded['energy']['V'] if dict_loaded['energy']['V'] > 0 else 3.0     # voltage XXX        
        
        self.gamma = dict_loaded['pathlossModel']['gamma'] if dict_loaded['pathlossModel']['gamma']>0 else 2.32
        self.d0 = dict_loaded['pathlossModel']['d0'] if dict_loaded['pathlossModel']['d0']>0 else 1000.0
        self.var = dict_loaded['pathlossModel']['var'] if dict_loaded['pathlossModel']['var']>0 else 7.8
        self.Lpld0 = dict_loaded['pathlossModel']['Lpld0'] if dict_loaded['pathlossModel']['Lpld0']>0 else 128.95
        self.GL = dict_loaded['pathlossModel']['GL'] if dict_loaded['pathlossModel']['GL']>0 else 0

        freq_list = []
        self.channel_list = []
        try:
            for channel in dict_loaded['channels']['first_window']:
                freq_list.append(channel['freq'])
                self.channel_list.append(LoRaChannel(channel['freq'],channel['duty_cycle']))
        except: 
            freq_list = [868100000, 868300000, 868500000]
            self.channel_list = []
            for freq in freq_list:
                self.channel_list.append(LoRaChannel(freq,0.01))

        try:
            self.second_channel = LoRaChannel(dict_loaded['channels']['second_window']['freq'],dict_loaded['channels']['second_window']['duty_cycle'])
        except:
            self.second_channel = LoRaChannel(868700000,0.1)
        
        self.lora_header = 1