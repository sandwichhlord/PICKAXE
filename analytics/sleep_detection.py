import time
import os
import math
from collections import deque


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, '..', 'data')
FILE_PATH = os.path.join(DATA_DIR, 'raw_data.csv')

stats = {'Deep': 0, 'REM': 0, 'Light': 0, 'Awake': 0}
last_mag = 0 

def calculate_live_score(current_stats):
    total = sum(current_stats.values())
    if total == 0: return 0
    score = (current_stats['Deep']*1.5 + current_stats['REM']*1.2 + 
             current_stats['Light']*0.5 - current_stats['Awake']*0.5)
    final_score = (score / (total * 1.5)) * 100 
    return max(0, min(100, final_score))

def get_last_line(filepath):
    with open(filepath, 'r') as f:
        try:
            # deque with maxlen=1 keeps only the very last item it sees
            last_line = deque(f, 1)[0]
            return last_line.strip()
        except IndexError:
            return None
        
try:
    while True:
        if os.path.exists(FILE_PATH) and os.path.getsize(FILE_PATH) > 0:
            last_line = get_last_line(FILE_PATH)
            
            if last_line and 'timestamp' not in last_line.lower():
                try:
                    # format: timestamp,hr,spo2,temp,acc_x,acc_y,acc_z
                    data = last_line.split(',')
                    timestamp = data[0]
                    hr = float(data[1])
                    spo2 = float(data[2])
                    temp = float(data[3])
                    acc_x = float(data[4])
                    acc_y = float(data[5])
                    acc_z = float(data[6])

                    # extrapolation
                    current_mag = math.sqrt(acc_x**2 + acc_y**2 + acc_z**2)
                    motion_delta = abs(current_mag - last_mag)
                    last_mag = current_mag
                    
                    is_moving = motion_delta > 0.2

                    if is_moving or hr > 80:
                        stage = 'Awake'
                    elif hr < 55 and temp < 36.3:
                        stage = 'Deep'
                    elif 55 <= hr <= 70 and temp < 36.5:
                        stage = 'REM' if spo2 < 96 else 'Light'
                    else:
                        stage = 'Light'

                    stats[stage] += 1
                    live_score = calculate_live_score(stats)

                    os.system('cls' if os.name == 'nt' else 'clear')
                    print(f"---LIVE SNAPSHOT ---")
                    print(f"Latest Snapshot: {timestamp}")
                    print(f"Motion Delta: {motion_delta:.2f}G , HR: {hr} , Temp: {temp}")
                    print(f"Current State: >> {stage.upper()} <<")
                    print(f"---")
                    print(f"Deep: {stats['Deep']}s , REM: {stats['REM']}s , Awake: {stats['Awake']}s")
                    print(f"LIVE SLEEP QUALITY: {live_score:.1f}%")
                    print(f"----")
                    print("1Hz multiplexed smampling")

                except (IndexError, ValueError) as e:
                    pass
        # multiplexed sampling
        time.sleep(1) 

except KeyboardInterrupt:
    print("\n\nEND")
    print(f"Fin. scores :-{calculate_live_score(stats):.2f}%")