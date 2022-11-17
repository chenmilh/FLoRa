class LoRaChannel():
    def __init__(self,freq,duty_cycle):
        self.freq = freq
        self.duty_cycle = duty_cycle
        self.transmission_time = 0