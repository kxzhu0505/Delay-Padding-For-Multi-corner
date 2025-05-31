import subprocess
import concurrent.futures
from concurrent.futures import  ThreadPoolExecutor, ProcessPoolExecutor
import numpy as np
import re
import os
import scipy.special
import lmoments3.distr
from skextremes.models.classic import GEV


#Ssta: /home/wllpro/llwang07/kxzhu/ssta/OpenSTA_S/app/sta 
#Dsta: /home/wllpro/llwang07/kxzhu/ssta/OpenSTA_D/app/sta


#Funtions prepared for l-mom
def pelgev(xmom):
    SMALL = 1e-5
    eps = 1e-6
    maxit = 20
    EU =0.57721566
    DL2 = np.log(2)
    DL3 = np.log(3)
    A0 =  0.28377530
    A1 = -1.21096399
    A2 = -2.50728214
    A3 = -1.13455566
    A4 = -0.07138022
    B1 =  2.06189696 
    B2 =  1.31912239 
    B3 =  0.25077104
    C1 =  1.59921491
    C2 = -0.48832213
    C3 =  0.01573152
    D1 = -0.64363929
    D2 =  0.08985247

    T3 = xmom[2]
    if xmom[1]<= 0 or abs(T3)>= 1:
        print("L-Moments Invalid")
        return
    if T3<= 0:
        G=(A0+T3*(A1+T3*(A2+T3*(A3+T3*A4))))/(1+T3*(B1+T3*(B2+T3*B3)))
        if T3>= -0.8:
            para3 = G
            GAM = np.exp(scipy.special.gammaln(1+G))
            para2=xmom[1]*G/(GAM*(1-2**(-G)))
            para1=xmom[0]-para2*(1-GAM)/G
            para = [para3,para1,para2]
            return(para)

        if T3 <= -0.97:
            G = 1-scipy.log(1+T3)/DL2
            
        T0=(T3+3)*0.5
        for IT in range(1,maxit):
            X2=2**(-G)
            X3=3**(-G)
            XX2=1-X2
            XX3=1-X3
            T=XX3/XX2
            DERIV=(XX2*X3*DL3-XX3*X2*DL2)/(XX2**2)
            GOLD=G
            G=G-(T-T0)/DERIV
            if abs(G-GOLD) <= eps*G:
                para3 = G
                GAM = scipy.exp(scipy.special.gammaln(1+G))
                para2=xmom[1]*G/(GAM*(1-2**(-G)))
                para1=xmom[0]-para2*(1-GAM)/G
                para = [para3,para1,para2]
                return(para)
            
        print("Iteration has not converged")

    Z=1-T3
    G=(-1+Z*(C1+Z*(C2+Z*C3)))/(1+Z*(D1+Z*D2))
    if abs(G)<SMALL:
        para2 = xmom[1]/DL2
        para1 = xmom[0]-EU*para2
        para = [para1,para2,0]
        return(para)
    else:
        para3 = G
        GAM = np.exp(scipy.special.gammaln(1+G))
        para2=xmom[1]*G/(GAM*(1-2**(-G)))
        para1=xmom[0]-para2*(1-GAM)/G
        para = [para3,para1,para2]
        return(para)

#Parse the output of the Opensta and extract the timing path data and delay
def parse_timing_data(output):
    timing_paths = {}
    current_path = {}
    lines = re.split(r'\n\n', output)

    for line in lines:
        match_start = re.search(r'Startpoint: (\w+)',line)
        match_end = re.search(r'Endpoint: (\w+)',line)
        match_arr =  re.search(r"\s*(\d+\.\d+)\s+data arrival time", line)
        match_slack = re.search(r'slack',line)
        if match_start:
            current_path['startpoint'] = match_start.group(1)
        if match_end:
            current_path['endpoint'] = match_end.group(1)
        if match_arr:
            delay_arr = float(match_arr.group(1))
        if match_slack:
            key = (current_path['startpoint'], current_path['endpoint'])
            timing_paths[key] = delay_arr
            current_path = {}
            delay_arr = 0.0

    return timing_paths


def run_opensta(input_file):
    # OpenSTA Command
    command = f"bsub -I /home/wllpro/llwang07/kxzhu/ssta/OpenSTA_S/app/sta -exit {input_file}"
    
    try:
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        #print(f"result: {result}")
    except Exception as e:
        print(f"Error running OpenSTA: {e}")
        return {}

    timing_path_info = parse_timing_data(result.stdout)
    #print(len(timing_path_info))
    return timing_path_info

def _run_ssta(input_file, num_iterations, _fit_method, lib_info):
    iternum = int(num_iterations/50)
    max_file_path = input_file.replace(".tcl", "_setup.tcl")
    min_file_path = input_file.replace(".tcl", "_hold.tcl")
    if not os.path.exists(max_file_path):
        raise FileNotFoundError(f"Setup timing file not found: {max_file_path}")
    if not os.path.exists(min_file_path):
        raise FileNotFoundError(f"Hold timing file not found: {min_file_path}")
    #print(f"max_file_path: {max_file_path}")
    #print(f"min_file_path: {min_file_path}")
    
    ssta_max_info = {}
    ssta_min_info = {}
    ssta_info = {}
    
    for i in range(iternum):
        with ProcessPoolExecutor() as executor:
            futures_max = {executor.submit(run_opensta, max_file_path)  for _ in range(50)}
            futures_min = {executor.submit(run_opensta, min_file_path)  for _ in range(50)}

            for future in concurrent.futures.as_completed(futures_max):
                for key, value in future.result().items():
                    ssta_max_info.setdefault(key, []).append(value)

            for future in concurrent.futures.as_completed(futures_min):
                for key, value in future.result().items():
                    ssta_min_info.setdefault(key, []).append(value)

    print("Finished GEV SSTA.\n")
    print("=============================================================================================\n")
    #print(ssta_max_info)
    print("Begin GEV Fit.\n")
    #TODO: More fit method include l-mom mom mle
    if _fit_method == 'mom' or _fit_method == 'mle':
        for key in ssta_max_info.keys():
            #print(f'Fit metohd is from skextremes {_fit_method}.')
            max_model = GEV(ssta_max_info[key], fit_method = _fit_method)
            min_model = GEV(ssta_min_info[key], fit_method = _fit_method)
            ssta_info[key] = [(max_model.c,max_model.loc,max_model.scale),(min_model.c,min_model.loc,min_model.scale),lib_info[key][0],lib_info[key][1]]
        for key in ssta_max_info.keys():
            #print(f'Fit metohd is from lmoments3 {_fit_method}.')
            max_model = lmoments3.lmom_ratios(ssta_max_info[key])
            para_fit_max_lmom = pelgev(max_model)
            min_model = lmoments3.lmom_ratios(ssta_min_info[key])
            para_fit_min_lmom = pelgev(min_model)
            ssta_info[key] = [(para_fit_max_lmom[0],para_fit_max_lmom[1],para_fit_max_lmom[2]),(para_fit_min_lmom[0],para_fit_min_lmom[1],para_fit_min_lmom[2]),lib_info[key][0],lib_info[key][1]]
    tp_file = input_file.replace(".tcl", '_tp.txt')
    with open(tp_file,'w') as file:
        for key,value in ssta_info.items():
            file.write(f"{key[0]} {key[1]} {value[0]} {value[1]} {value[2]} {value[3]}\n")        
        print(len(ssta_info))
    print("Finished GEV FIT.\n")
    print("=============================================================================================\n")