import time
import os


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, '..', 'data')
INPUT_FILE = os.path.join(DATA_DIR, 'raw_data.csv')
OUTPUT_FILE = os.path.join(DATA_DIR, 'ml_inference.csv')

BASELINE_HR = 75
BASELINE_TEMP = 36.5
 
# SICKNESS SCORE FUNCTION -> finds the sickness score
def calculate_sickness_score(current_hr, baseline_hr, current_temp, baseline_temp, current_spo2):
    """
    heuristic decision tree; calculates sickness score (0-100).
    high score = high chance of illness/fever/overtraining.
    """
    score = 0.0
    
    # temperature variance
    temp_diff = current_temp - baseline_temp
    if temp_diff > 0.5:
        score += (temp_diff * 20.0)
    
    if current_spo2 < 95:
        score += ((95.0 - current_spo2) * 5.0)
    hr_diff = current_hr - baseline_hr
    if hr_diff > 15:
        score += (hr_diff * 0.5)
            
    # clamping the values
    return int(max(0, min(100, score)))


if not os.path.exists(OUTPUT_FILE) or os.path.getsize(OUTPUT_FILE) == 0:
    with open(OUTPUT_FILE, 'w') as f:
        f.write("timestamp,sickness_score\n")
last_timestamp = ""

try:
    while True:
        time.sleep(1.0)
        
        if not os.path.exists(INPUT_FILE):
            continue
            
        try:
            with open(INPUT_FILE, 'r') as f:
                lines = f.readlines()
                if len(lines) < 2: 
                    continue
                    
                last_line = lines[-1].strip()
                
            if not last_line or last_line.startswith("timestamp"):
                continue
                
            data = last_line.split(',')
            if len(data) != 7:
                continue
                
            timestamp = data[0]
            
            if timestamp == last_timestamp:
                continue 
            last_timestamp = timestamp
            
            current_hr = float(data[1])
            current_spo2 = float(data[2])
            current_temp = float(data[3])
            
            sickness_score = calculate_sickness_score(
                current_hr, BASELINE_HR, 
                current_temp, BASELINE_TEMP, 
                current_spo2
            )
            
            with open(OUTPUT_FILE, 'a') as out_file:
                out_file.write(f"{timestamp},{sickness_score}\n")
                
            print(f"TS:{timestamp} , HR:{current_hr} , temp:{current_temp:.1f} , score: {sickness_score}/100")
            
        except (IndexError, ValueError):
            pass

except KeyboardInterrupt:
    print("\n END")
