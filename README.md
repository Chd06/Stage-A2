# 🧠 Neural Control of a Mobile Robotic Platform

> **Proof of Concept** — Brain-Computer Interface (BCI) using SSVEP paradigm to control a TurtleBot robot via EEG signals.

**Internship project** @ Lab'CESI Lyon (CESI Engineering School)  
**Supervised by** Julien Coyne  
**Duration** 8 weeks

---

## 📋 Overview

This project explores the feasibility of controlling a mobile robot (TurtleBot under ROS) using a Brain-Computer Interface based on **Steady-State Visual Evoked Potentials (SSVEP)**.

The principle: visual stimuli (arrows) flicker at different frequencies on screen. When the user focuses on one arrow, the brain synchronizes to that frequency — detectable via FFT analysis on occipital EEG electrodes. The detected direction is then sent as a command to the robot via a REST API.

---

## 🏗️ System Architecture

```
EEG Headset (Unicorn Hybrid Black)
        ↓
acquisition_live.py
  - Live data reading via UnicornPy SDK
  - 3-second sliding buffer
  - Bandpass filter (Butterworth order 4)
  - DC offset removal
  - FFT on occipital channels (Ch6, Ch7, Ch8)
  - SNR-based frequency detection
        ↓
Flask API (robot PC, port 5000)
  - Route /commande → receives {"direction": "forward"}
  - Creates ROS Twist message
        ↓
TurtleBot (/cmd_vel topic)
```

---

## 🛠️ Hardware & Environment

| Component | Details |
|-----------|---------|
| EEG Headset | Unicorn Hybrid Black (g.tec) — 8 dry electrodes, 250 Hz |
| Robot | TurtleBot under ROS |
| OS | Windows |
| Language | Python 3.7 |
| EEG Software | Unicorn Suite (visualization & recording) |

---

## 📁 Project Structure

```
Stage-A2/
│
├── simulation.py              # Visual stimulus (Pygame) — flickering arrows
├── acquisition_live.py        # Live EEG acquisition & real-time detection
├── pipeline.py                # Offline CSV analysis with SNR computation
├── test_connexion.py          # Flask API connection test
│
├── enregistrements_recorder/  # EEG recordings (.csv, .bdf)
│   └── *.csv
│
├── Unicorn.dll                # Unicorn SDK dependencies (required)
├── UnicornPy.pyd
└── README.md
```

> ⚠️ **Important**: `UnicornPy.pyd`, `Unicorn.dll`, `cpprest142_2_10.dll` and `Gtec_Licensing_Unicorn.dll` must all be in the same folder as the scripts.

---

## 🔧 Scripts Description

### `simulation.py`
Pygame-based visual stimulus displaying 4 triangular arrows on a black background, each flickering at a different frequency at 120 FPS.

| Direction | Frequency |
|-----------|-----------|
| Up (forward) | 8 Hz |
| Down (backward) | 10 Hz |
| Left | 12 Hz |
| Right | 15 Hz |

### `acquisition_live.py`
Real-time EEG acquisition and SSVEP detection pipeline:
- Connects to the Unicorn headset via Bluetooth
- Buffers 3 seconds of data (750 samples at 250 Hz)
- Applies DC offset removal and Butterworth bandpass filter (10–25 Hz)
- Computes FFT on the average of channels Ch6, Ch7, Ch8
- Detects dominant frequency and compares it to target frequencies
- Sends directional command to the robot Flask API via HTTP POST
- Optional CSV saving with timestamp

### `pipeline.py`
Offline analysis tool for recorded CSV files:
- Reads Unicorn CSV recordings from a folder
- Applies Butterworth bandpass filter (0.5–30 Hz) on Ch6, Ch7, Ch8
- Splits signal into 5-second windows
- Computes FFT per window
- Calculates **SNR** (Signal-to-Noise Ratio) at each target frequency
- Computes a global quality score (% of windows with SNR > 1.5)
- Displays two plots:
  - SNR over time for the 4 target frequencies
  - Global FFT spectrum with target frequency markers

---

## 📐 Signal Processing Pipeline

```
Raw EEG signal
      ↓
DC offset removal (subtract channel mean)
      ↓
Butterworth bandpass filter (order 4)
      ↓
3-second windowing
      ↓
FFT (Fast Fourier Transform)
      ↓
SNR computation at target frequencies
      ↓
Detection / Command
```

**Why Butterworth?** It provides the flattest possible frequency response in the passband — no distortion or unwanted amplification of the frequencies of interest, unlike Chebyshev or elliptic filters.

**Why SNR instead of raw amplitude?** Raw amplitude varies with overall signal level (movement artifacts, contact quality). SNR normalizes by comparing the amplitude at the target frequency to its immediate neighbors in the spectrum — a value > 1.5 indicates a genuine peak above background noise.

---

## ⚙️ Installation & Requirements

```bash
pip install numpy scipy matplotlib pandas pygame
```

Additionally, the **Unicorn Python API** must be installed from the Unicorn Suite package (g.tec). Make sure the required DLLs are present in the project directory.

---

## 🚀 Usage

### 1. Run the visual stimulus
```bash
python simulation.py
```

### 2. Run live acquisition (in a separate terminal)
```bash
python acquisition_live.py
```

### 3. Analyze a recorded CSV file
```bash
python pipeline.py
```
The script will list available CSV files in `enregistrements_recorder/` and let you choose which one to analyze.

---

## 📊 Key Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| `FREQUENCE` | 250 Hz | EEG sampling rate |
| `FENETRE_SEC` | 3 s | Analysis window duration |
| `SEUIL_MIN` | 20.0 | Minimum amplitude threshold |
| `FREQS_CIBLES` | 8/10/12/15 Hz | Target SSVEP frequencies |
| Bandpass filter | 10–25 Hz | Live acquisition filter |
| Butterworth order | 4 | Filter steepness |
| Occipital channels | Ch6, Ch7, Ch8 | Channels used for SSVEP |

---

## 📈 Results & Discussion

The complete pipeline (stimulus → acquisition → signal processing → robot command) was successfully implemented and validated. However, **clear SSVEP responses were not consistently detected** in the recordings, with SNR values fluctuating randomly around 1.0 across recording sessions.

**Likely causes:**
- Dry electrodes may provide insufficient contact quality for SSVEP
- Target frequencies (8–15 Hz) overlap with natural alpha waves (8–13 Hz), masking the SSVEP response
- Fixation duration per stimulus was too short
- High inter-individual variability in SSVEP responses

---

## 🔭 Future Work & Perspectives

- **Test higher stimulation frequencies** (18–30 Hz) to avoid alpha band interference
- **Implement CCA** (Canonical Correlation Analysis) — state-of-the-art SSVEP detection method, more robust than plain FFT
- **User-specific calibration** — automatic SNR threshold and frequency tuning per user before each session
- **Real-time signal quality dashboard** — display electrode contact quality and per-channel noise level
- **Explore alternative BCI paradigms**: P300 event-related potential, Motor Imagery (mu/beta rhythms), EOG-based eye blink detection
- **Finalize robot integration** — re-enable Flask API commands once reliable detection is achieved

---

## 📚 Key Concepts

**SSVEP (Steady-State Visual Evoked Potentials)**: When a person fixates on a flickering visual stimulus, their visual cortex generates electrical activity at the same frequency as the flicker — detectable via EEG on occipital electrodes.

**SNR (Signal-to-Noise Ratio)**: Ratio of the FFT amplitude at the target frequency to the mean amplitude of neighboring frequency bins. SNR ≈ 1.0 = noise only; SNR > 1.5 = detectable signal; SNR > 2.0 = strong signal.

**FFT (Fast Fourier Transform)**: Algorithm that converts a time-domain signal into its frequency components — the core of SSVEP detection.

---

## 📄 License

This project was developed as part of an academic internship at Lab'CESI Lyon. All rights reserved.
