# 🧱 Tile Defect Detection System

A computer vision–based quality control web application built with **Streamlit** and **OpenCV** that automatically detects cracks and surface spots on ceramic/floor tiles in real time.

---

## 📋 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
- [Running the App](#-running-the-app)
- [How It Works](#-how-it-works)
- [Detection Logic](#-detection-logic)
- [Dashboard & Reports](#-dashboard--reports)
- [File Storage](#-file-storage)
- [Known Limitations](#-known-limitations)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔐 Auth System | Secure Signup & Login with bcrypt password hashing |
| 📷 Image Input | Upload an image **or** capture directly from webcam |
| 🔍 Defect Detection | Automatic crack length & spot detection using OpenCV |
| 📊 KPI Dashboard | Today's production summary — total, good, defective tiles, defect rate |
| 📈 Analytics Charts | Daily production bar chart + per-tile trend graphs |
| 📁 Inspection History | Per-user table of all past inspections |
| 🖼️ Tile Gallery | Side-by-side input vs. processed image viewer |
| ⬇️ Excel Export | Download full inspection history as `.xlsx` |
| 🌙 Dark Mode UI | Modern dark theme using Streamlit custom CSS |
| 🚪 Sign Out | Secure logout that clears all session data |

---

## 🛠️ Tech Stack

| Library | Purpose |
|---------|---------|
| `streamlit` | Web UI framework |
| `opencv-python` | Image processing & defect detection |
| `numpy` | Array operations for image data |
| `pandas` | CSV inspection history management |
| `matplotlib` | Analytics charts and graphs |
| `bcrypt` | Password hashing for user authentication |
| `openpyxl` | Excel report generation |

---

## 📂 Project Structure

```
Tile Defect Detection System/
│
├── app.py                  # Main Streamlit application
├── auth.py                 # Login & Signup logic
├── utils.py                # OpenCV tile inspection engine
├── users.json              # User accounts (auto-created on first signup)
│
├── inspection_data/        # Per-user CSV inspection logs (auto-created)
│   └── <username>.csv
│
├── output_tiles/           # Input & output images for all inspections (auto-created)
│   └── <username>_input_<timestamp>.jpg
│   └── <username>_output_<timestamp>.jpg
│
└── defective_tiles/        # Defective tile images, organized by user & date (auto-created)
    └── <username>/
        └── <DD-MM-YYYY>/
            └── defective_<timestamp>.jpg
```

---

## ⚙️ Installation

### Prerequisites
- Python **3.9+**
- pip

### 1. Clone / Download the project

```bash
git clone <your-repo-url>
cd "Tile Defect Detection System"
```

### 2. Install dependencies

```bash
pip install streamlit opencv-python numpy pandas matplotlib bcrypt openpyxl
```

---

## ▶️ Running the App

```bash
streamlit run app.py
```

The app will open automatically in your browser at:

```
Local URL:   http://localhost:8501
Network URL: http://<your-ip>:8501
```

---

## 🔄 How It Works

```
User logs in
     │
     ▼
Upload image OR capture from camera
     │
     ▼
OpenCV processes the tile image
  ├── Crack Detection  (Canny edge → contours → arc length in mm)
  └── Spot Detection   (Adaptive threshold → morphology → shape filter)
     │
     ▼
Result: GOOD ✅ or DEFECTIVE ❌
     │
     ├── Save input & output images to output_tiles/
     ├── If DEFECTIVE → also save to defective_tiles/<user>/<date>/
     └── Append record to inspection_data/<username>.csv
```

---

## 🔍 Detection Logic

### Crack Detection

1. Resize image to **512×512**
2. Convert to grayscale → Gaussian blur
3. Apply **Canny edge detection** (thresholds: 60 / 160)
4. Dilate edges to connect fragments
5. Find contours with area > 200 px²
6. Sum arc lengths → convert to **millimetres** (× 0.1 px/mm)

### Spot Detection

1. Apply **adaptive Gaussian threshold** (block size: 15, C: 3)
2. Morphological opening to remove noise (2 iterations)
3. Find contours; filter by area **80 – 3000 px²**
4. Compute **aspect ratio** and **solidity** for each contour
5. Classify as a real spot if `aspect_ratio < 2.5` AND `solidity > 0.6`

### Defect Decision Thresholds

| Metric | Threshold | Action |
|--------|-----------|--------|
| Crack length | > **8 mm** | → DEFECTIVE |
| Spot count | ≥ **3 spots** | → DEFECTIVE |
| Defect area % | > **1.5 %** | → DEFECTIVE |

> ⚠️ Tiles with **fewer than 3 detected spots** are classified as GOOD, even if some spots are present.

---

## 📊 Dashboard & Reports

### KPI Cards (today only)
- 🧱 Total Tiles Inspected
- ❌ Defective Tiles
- ✅ Good Tiles
- 📉 Defect Rate (%)

### Charts
- **Daily Bar Chart** — Good vs Defective tiles per day
- **Defect % per Tile** — bar chart
- **Crack Length Trend** — area + line chart
- **Spot Count Trend** — area + line chart

### Excel Export
Download the full inspection history as a formatted `.xlsx` file from the sidebar.

---

## 💾 File Storage

| Path | Content |
|------|---------|
| `users.json` | User accounts with bcrypt-hashed passwords |
| `inspection_data/<user>.csv` | Columns: Time, Crack(mm), Spots, Defect %, Result |
| `output_tiles/` | `<user>_input_<ts>.jpg` and `<user>_output_<ts>.jpg` |
| `defective_tiles/<user>/<date>/` | Only defective tile output images |

---

## ⚠️ Known Limitations

- Detection accuracy depends on image quality and lighting conditions.
- The `PIXEL_TO_MM` conversion factor (`0.1`) is approximate; calibrate for your camera/resolution for production use.
- User data is stored locally in JSON/CSV files — not suitable for multi-server deployments without a proper database.
- Camera capture requires HTTPS or `localhost` for browser permissions.

---

## 👤 Author

Built as a tile quality control prototype using computer vision and Streamlit.
