import time
import os
import math
from collections import deque

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, '..', 'data')


BASELINE_HR = 75
BASELINE_TEMP = 37
INPUT_FILE = os.path.join(DATA_DIR, 'raw_data.csv')
OUTPUT_FILE = os.path.join(DATA_DIR, 'ml_inference.csv')

sleep_stats = {'Deep': 0, 'REM': 0, 'Light': 0, 'Awake': 0}
last_mag = 0 

def calculate_sickness_score(current_hr, baseline_hr, current_temp, baseline_temp, current_spo2):
    score = 0.0
    temp_diff = current_temp - baseline_temp
    if temp_diff > 0.5:
        score += (temp_diff * 20.0)
    if current_spo2 < 95:
        score += ((95.0 - current_spo2) * 5.0)
    hr_diff = current_hr - baseline_hr
    if hr_diff > 15:
        score += (hr_diff * 0.5)
    return int(max(0, min(100, score)))

def calculate_sleep_score(current_stats):
    total = sum(current_stats.values())
    if total == 0: return 0
    score = (current_stats['Deep']*1.5 + current_stats['REM']*1.2 + 
             current_stats['Light']*0.5 - current_stats['Awake']*0.5)
    final_score = (score / (total * 1.5)) * 100 
    return max(0, min(100, final_score))

def get_last_line(filepath):
    try:
        with open(filepath, 'r') as f:
            return deque(f, 1)[0].strip()
    except (IndexError, FileNotFoundError):
        return None

with open(OUTPUT_FILE, 'w') as f:
    f.write("timestamp,sickness_score,sleep_stage,sleep_score\n")

last_timestamp = ""

try:
    while True:
        time.sleep(1.0) # downsampled to 1hz
        
        last_line = get_last_line(INPUT_FILE)
        
        if last_line and 'timestamp' not in last_line.lower():
            try:
                data = last_line.split(',')
                if len(data) < 7: continue
                
                timestamp = data[0]
                if timestamp == last_timestamp: continue
                last_timestamp = timestamp
                
                hr = float(data[1])
                spo2 = float(data[2])
                temp = float(data[3])
                acc_x = float(data[4])
                acc_y = float(data[5])
                acc_z = float(data[6])

                sickness_score = calculate_sickness_score(hr, BASELINE_HR, temp, BASELINE_TEMP, spo2)

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

                sleep_stats[stage] += 1
                sleep_score = calculate_sleep_score(sleep_stats)

                with open(OUTPUT_FILE, 'a') as out_file:
                    out_file.write(f"{timestamp},{sickness_score},{stage},{sleep_score:.1f}\n")

                os.system('cls' if os.name == 'nt' else 'clear')
                print(f"--- PICKAXE LIVE INFERENCE PIPELINE ---")
                print(f"Time: {timestamp} | Motion: {motion_delta:.2f}G | HR: {hr} | Temp: {temp:.1f}°C")
                print(f"---------------------------------------")
                print(f"CURRENT STAGE  : >> {stage.upper()} <<")
                print(f"SLEEP SCORE    : {sleep_score:.1f}%")
                print(f"SICKNESS ALERT : {sickness_score}/100")
                print(f"---------------------------------------")
                print(f"Deep: {sleep_stats['Deep']}s | REM: {sleep_stats['REM']}s | Light: {sleep_stats['Light']}s | Awake: {sleep_stats['Awake']}s")
                print("Engine running. Press Ctrl+C to exit.")

            except (IndexError, ValueError):
                pass

except KeyboardInterrupt:
    print("\n\n--- INFERENCE ENGINE SHUTDOWN ---")