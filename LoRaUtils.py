import math
from scipy.stats import norm

def airtime(sf,cr,pl,bw):
    H = 0        # implicit header disabled (H=0) or not (H=1)
    DE = 0       # low data rate optimization enabled (=1) or not (=0)
    Npream = 8   # number of preamble symbol (12.25  from Utz paper)

    if bw == 125 and sf in [11, 12]:
        # low data rate optimization mandated for BW125 with SF11 and SF12
        DE = 1
    if sf == 6:
        # can only have implicit header with SF6
        H = 1

    Tsym = (2.0**sf)/bw
    Tpream = (Npream + 4.25)*Tsym
    # print "sf", sf, " cr", cr, "pl", pl, "bw", bw
    payloadSymbNB = 8 + max(math.ceil((8.0*pl-4.0*sf+28+16-20*H)/(4.0*(sf-2*DE)))*(cr+4),0)
    Tpayload = payloadSymbNB * Tsym
    return (Tpream + Tpayload)


def ber_reynders(eb_no, sf):
    """Given the energy per bit to noise ratio (in db), compute the bit error for the SF"""
    return norm.sf(math.log(sf, 12)/math.sqrt(2)*eb_no)

def ber_reynders_snr(snr, sf, bw, cr):
    """Compute the bit error given the SNR (db) and SF"""
    Temp = [4.0/5,4.0/6,4.0/7,4.0/8]
    CR = Temp[cr-1]
    BW = bw*1000.0
    eb_no =  snr - 10*math.log10(BW/2**sf) - 10*math.log10(sf) - 10*math.log10(CR) + 10*math.log10(BW)
    return ber_reynders(eb_no, sf)

def per(sf,bw,cr,rssi,pl):
    snr = rssi  +174 - 10*math.log10(bw*1000) - 6
    return 1 - (1 - ber_reynders_snr(snr, sf, bw, cr))**(pl*8)

def frequencyCollision(f1,f2,bw1,bw2):
    f_coll = False
    if (abs(f1-f2)<=120 and (bw1==500 or bw2==500)):
        f_coll = True
    elif (abs(f1-f2)<=60 and (bw1==250 or bw2==250)):
        f_coll = True
    else:
        if (abs(f1-f2)<=30):
            f_coll = True
    return f_coll

def timingCollision(arrive_time, arrive_sf,arrive_bw,other_arrivetime,other_duration):
    Npream = 8
    Tpreamb = 2**arrive_sf/(1.0*arrive_bw) * (Npream - 5)
    p2_end = other_arrivetime + other_duration
    p1_cs = arrive_time + Tpreamb
    if p1_cs < p2_end:
        return True
    return False

def powerCollision(rssi1, rssi2):
    powerThreshold = 6 # dB
    if abs(rssi1 - rssi2) < powerThreshold:
        return 0
    elif rssi1 - rssi2 < powerThreshold:
        return 1
    return 2