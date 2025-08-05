# 🧪 RFAM Ink Toolbox

A modular, GUI-driven analysis pipeline for ex-situ characterization of RFAM (Radio Frequency Additive Manufacturing) prints. Built for high-resolution scanned images, this tool allows for region selection, metric computation, and visualizations of ink droplet quality and consistency.

---

## 📦 Features

- 🖱️ **Interactive ROI Selection**  
  Use the GUI to draw polygon, circular, or ruler-based regions of interest on high-resolution scanned images.

- 📏 **Quantitative Analysis**  
  Computes intensity, shape, area, and halo metrics per region using adaptive thresholding and OpenCV.

- 🌈 **Visualization Tools**  
  Generates:
  - Overlay plots with object outlines
  - Heatmaps (with viridis colormap) of grayscale intensity
  - ROI-specific heatmaps with colorbars and average intensity indicators

- 📂 **Data Output**  
  Session data and results are written to disk as structured `.csv` files for downstream analysis.

---

## 🧰 Project Structure
```
rfam-ink-toolbox/
├── analyzer.py # Core metric computations (intensity, shape, halo)
├── dataio.py # Handles reading/writing session and results data
├── extra_analysis_vis.py # Post-analysis visualization (e.g., comparisons across inks)
├── gui.py # Interactive ROI selection interface
├── main.py # Orchestrates session flow
├── plots.py # Heatmaps and contour visualizations
├── utils.py # Helper functions
├── README.md # Project documentation
```

## 🖥️ Getting Started

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/rfam-ink-toolbox.git
   cd rfam-ink-toolbox
   
2. **Install dependencies**
All required packages are standard and should be available in most environments:
- opencv-python
- numpy
- matplotlib
- tkinter (for GUI)

3. **Run the tool**
```bash
python main.py
```

## 🧪 Example Workflow
1. Load a high-resolution scanned image of RFAM droplet prints.
2. Use the GUI to select and label regions of interest (ROIs).
3. Automatically compute:
  - Mean, median, and standard deviation of intensity
  - ROI pixel area and shape descriptors
  - Halo eccentricity (if enabled)
4. Export results as .csv and visualize ROI-specific heatmaps with viridis colormap.
5. Optionally aggregate multiple .csv sessions into a combined analysis.

## 📊 Example Outputs
- ✅ ROI object outlines
- 🌡️ ROI-only intensity heatmaps with average values labeled
- 📈 Combined CSV outputs for multi-session comparison
- 🧵 Ruler-based scaling in mm²

## 🧪 ROI Labeling Scheme
Ink samples are automatically labeled using a consistent shorthand:
```bash
2_25wtp_petro_03
│ │           │
│ │           └─ replicate #
│ └────────── ink type
└──────────── ink key (1–4)
```

## 📎 Notes
- Designed to work with flatbed scanner images from RFAM diagnostic scans.
- Supports interactive labeling and replicate tracking (e.g., 2_25wtp_petro_03).
- All results saved automatically to a /session_data/ directory.

## 📝 License
MIT License © 2025 Matt McCoy
