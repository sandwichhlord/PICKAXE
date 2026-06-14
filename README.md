# PICKAXE: Biometric Edge Computing Wearable

![C++](https://img.shields.io/badge/Firmware-C++-blue) ![Python](https://img.shields.io/badge/Backend-Python-yellow) ![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-red) ![ESP32](https://img.shields.io/badge/Hardware-ESP32-lightgrey)

**Status: Functional Prototype** > **Note for recruiters/reviewers:** This repo contains the firmware and pipeline for an IoT wearable I built with a 4-person project team. The core architecture works great, but since it was a rapid college project, I'm still cleaning up some technical debt (like swapping the CSV buffers for a proper message broker like Redis).

Video demonstrations are in the demo folder!

## Why We Built This
Expensive fitness trackers (like Apple Watches or Fitbits) already have all the raw sensors needed to extrapolate cool health insights like sickness likelihood, fall detection or granular sleep stages. But they usually lock those features behind subscription paywalls or don't let you access the raw data yourself. My team and I built PICKAXE to show how easy it is to build a completely free, open-source biometric pipeline from scratch, right from the bare metal up to the UI.

## System Architecture & Data Pipeline
The system is pretty modular. We split the hardware data collection, the network ingestion, and the ML inferences into distinct decoupled layers.

1. **The Edge Node (ESP32 Firmware):** 
   * Captures raw IMU and IR sensor telemetry at a high-frequency **20Hz sampling rate**.
   * We didn't want to rely on the cloud for everything, so stuff like impact detection (falls) runs directly on the ESP32. If it detects a fall, the blue LED blinks instantly without waiting for any server response.
2. **The Wireless Bridge:** 
   * The ESP32 shoots the raw packets via **Bluetooth** to an Android phone, which acts as a TCP server to forward the stream to my laptop over **Wi-Fi**.
3. **Data Ingestion (`data_extraction.py`):** 
   * Connects to the TCP socket and extrapolates Heart Rate (BPM) and SpO2 from the raw IR signal.
   * Dumps the cleaned telemetry into `data/raw_data.csv` (`timestamp, hr, spo2, temp, acc_x, acc_y, acc_z, steps`).
4. **The Inference Engine (`backend/server.py`):** 
   * Processing 20Hz frames constantly is a nightmare for CPU usage. So we built an efficient **downsampling architecture**. It only polls the rolling CSV buffer at **1Hz**, which drastically reduces background processing.
   * Runs heuristic decision trees to calculate a `sickness_score` and `sleep_stage`, outputting the results to `data/ml_inference.csv`.
5. **The Frontend (`frontend/app.py`):** 
   * A Streamlit dashboard that continuously reads the inference buffers. I had to write some exception handling to bypass file-locking collisions, but it displays the real-time vitals and analytical extrapolations pretty smoothly.

## Features That Actually Work Well
* **Zero-Latency Edge Detection:** Fall detection triggers right on the hardware. No API calls needed.
* **Resource-Efficient Downsampling:** Only running the inference at 1Hz means the Streamlit app doesn't crash the background CPU while it runs.
* **Rolling Buffer Management:** The ingestion script automatically prunes the active CSV state files to a maximum of 1,000 rows so we don't accidentally memory leak or cause file I/O bottlenecks if left running overnight.


## How To Run

1. Flash the Hardware

Upload firmware/esp_32_code.ino to your ESP32.

Connect the Android device via Bluetooth and start the TCP Server app.

2. Start the Pipeline
Open three separate terminal instances and launch the microservices in this exact order:
```
# Terminal 1: Start the Ingestion Layer
python data_extraction.py
# Terminal 2: Start the Inference Engine
python backend/server.py
# Terminal 3: Launch the Dashboard
streamlit run frontend/app.py
```

## Repository Structure
```text
PICKAXE/
├── backend/                  
│   └── server.py              # 1hz inference
├── data/                      
│   ├── ml_inference.csv       # heuristic output state
│   └── raw_data.csv
├── demos/
│   ├── DashboardDemo.mp4
│   └── HardwareDemo.mp4
├── firmware/                  
│   └── esp_32_code.ino        # C++ ESP32 edge logic & Bluetooth transmission
├── frontend/
│   └── app.py                 # streamlit UI dashboard
├── data_extraction.py         # Wi-Fi TCP Socket ingestion & IR extrapolation
├── README.md
└── requirements.txt