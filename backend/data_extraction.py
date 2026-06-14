import socket
import time
import os
from datetime import datetime
import math


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, '..', 'data')
FILE_PATH = os.path.join(DATA_DIR, 'raw_data.csv')

# TCP phone connection
PHONE_IP = '172.31.78.17' # TCP server connection to phone
PHONE_PORT = 8080

# buffer sizes
MAX_CSV_ROWS = 1000
rows_since_last_prune = 0 # counter for batch prune

total_steps = 0
is_stepping = False
STEP_THRESHOLD = 1.4
ir_buffer = []
BUFFER_SIZE = 50

print(f"--- Neural Arena: Secure Wi-Fi Ingestion ---")
print(f"Connecting to Gateway at {PHONE_IP}:{PHONE_PORT}...")

try:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.settimeout(5.0) 
    client_socket.connect((PHONE_IP, PHONE_PORT))
    client_socket.settimeout(None) 
    
    print(f"linked\n")
    
    buffer = ""
    
    while True:
        # boilerplate 
        chunk = client_socket.recv(1024).decode('utf-8', errors='ignore')
        if not chunk:
            break 
            
        buffer += chunk
        
        # complete lines from buffer
        while '\n' in buffer:
            line, buffer = buffer.split('\n', 1)
            line = line.strip()
            
            # healthy code :)
            if not line:
                continue
                
            data = line.split(',')
            if len(data) != 5:
                continue 
                
            try:
                rawIR = float(data[0])
                temp = float(data[1]) - 14.0 # calibration offset cuz using IMUs internal temp sensor (normal temp sensor broke)
                acc_x = float(data[2])
                acc_y = float(data[3])
                acc_z = float(data[4])
                
                current_mag = math.sqrt(acc_x**2 + acc_y**2 + acc_z**2)
                if current_mag > STEP_THRESHOLD and not is_stepping:
                    total_steps += 0.5
                    is_stepping = True
                elif current_mag < 1.0:
                    is_stepping = False

                timestamp = datetime.now().strftime("%H:%M:%S")
                
                # extrapolating HR and SpO2
                ir_buffer.append(rawIR)
                if len(ir_buffer) > BUFFER_SIZE:
                    ir_buffer.pop(0)

                if len(ir_buffer) == BUFFER_SIZE:
                    # peak detection approximation for HR
                    mean_ir = sum(ir_buffer) / len(ir_buffer)
                    peaks = sum(1 for i in range(1, len(ir_buffer)-1) 
                                if ir_buffer[i] > mean_ir and 
                                ir_buffer[i] > ir_buffer[i-1] and 
                                ir_buffer[i] > ir_buffer[i+1])
                    
                    hr = float(peaks * 12)
                    
                    variance = sum((x - mean_ir)**2 for x in ir_buffer) / len(ir_buffer)
                    ac_dc_ratio = math.sqrt(variance) / mean_ir if mean_ir != 0 else 0
                    
                    estimated_spo2 = 100.0 - (ac_dc_ratio * 100.0)
                    spo2 = max(90.0, min(100.0, estimated_spo2))
                    
                    # sanity check HR limits to avoid crazy numbers during sensor noise
                    hr = max(40.0, min(200.0, hr))
                else:
                    # default baselines while buffer fills
                    hr = 75.0
                    spo2 = 98.0
                
                csv_row = f"{timestamp},{hr},{spo2},{temp},{acc_x},{acc_y},{acc_z},{total_steps}\n"
                
                with open(FILE_PATH, 'a') as file:
                    if os.path.getsize(FILE_PATH) == 0:
                        file.write("timestamp,hr,spo2,temp,acc_x,acc_y,acc_z,steps\n")
                    file.write(csv_row)
                
                rows_since_last_prune += 1
                
                # batch pruning
                # each 50 rows check file size and slice old data
                if rows_since_last_prune >= 50:
                    rows_since_last_prune = 0
                    
                    with open(FILE_PATH, 'r') as read_file:
                        all_lines = read_file.readlines()
                        
                    #plus 1 for the header
                    if len(all_lines) > MAX_CSV_ROWS + 1:
                        pruned_lines = [all_lines[0]] + all_lines[-MAX_CSV_ROWS:]
                        
                        with open(FILE_PATH, 'w') as write_file:
                            write_file.writelines(pruned_lines)

                print(f"TS:{timestamp} , HR:{hr:.0f} , spo2:{spo2:.1f} , temp:{temp:.1f} , z:{acc_z:.2f} , y:-{acc_y:.2f} , x:{acc_x:.2f} , steps:{total_steps}")
                
            except ValueError:
                pass

except ConnectionRefusedError:
    print(f"\n[ERROR] cant find android tcp server")
except socket.timeout:
    print("\n[ERROR] Connection timed out. Phone didn't respond.")
except KeyboardInterrupt:
    print("\nData Ingestion Stopped Cleanly.")
finally:
    if 'client_socket' in locals():
        client_socket.close()