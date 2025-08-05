#!/usr/bin/env python3
"""
main.py — orchestrates GUI, analysis, and data export for RFAM ROI tool.
"""
import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import colors

from gui import main as gui_main
from analyzer import compute_metrics
from dataio import build_dataframe, export_csv
from plots import (
    plot_histogram,
    plot_boxplot,
    plot_area_histogram,
    plot_area_vs_intensity,
    plot_circularity_vs_intensity
)


def main():
    """Run the RFAM ROI selection and analysis pipeline."""
    # 1) Collect ROIs + session data
    session = gui_main()
    if not session or not session.get('rois'):
        print("No ROIs collected; exiting.")
        return

    # 2) Reload full-resolution image
    img_path = session['file_path']
    img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        print(f"Failed to reload image from {img_path}; exiting.")
        return

    # 3) Compute metrics per ROI
    results = []
    for roi in session['rois']:
        metrics = compute_metrics(
            image=img,
            roi=roi,
            px_per_mm=session['px_per_mm'],
            do_intensity=session['analysis']['intensity'],
            do_shape=session['analysis']['shape'],
            do_halo=session['analysis']['halo']
        )
        # carry forward mask_full for ROI‐only heatmaps
        metrics.update({
            'label':     roi['label'],
            'ink_key':   roi['ink_key'],
            'rep':       roi['rep'],
            'mask_full': metrics.get('mask_full')
        })
        results.append(metrics)

    # 4) ROI‐only heatmaps (Viridis, each scaled to its own min/max)
    scale = session['scale']
    for r in results:
        mask = r.get('mask_full')
        if mask is None:
            continue
        label = r['label']

        # Bounding box with padding
        ys, xs = np.nonzero(mask)
        y0, y1 = ys.min(), ys.max()
        x0, x1 = xs.min(), xs.max()
        pad = 1000
        y0p = max(0, y0 - pad)
        y1p = min(img.shape[0] - 1, y1 + pad)
        x0p = max(0, x0 - pad)
        x1p = min(img.shape[1] - 1, x1 + pad)
        crop = img[y0p:y1p+1, x0p:x1p+1]

        # Convert to grayscale
        gray_crop = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if crop.ndim == 3 else crop.copy()

        # Downsample the crop
        h_c, w_c = gray_crop.shape[:2]
        ds = cv2.resize(
            gray_crop,
            (max(1, int(w_c * scale)), max(1, int(h_c * scale))),
            interpolation=cv2.INTER_AREA
        )

        # Normalize to 0–255
        norm = cv2.normalize(ds, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

        # Determine vmin/vmax and mean
        vmin, vmax = int(norm.min()), int(norm.max())
        mean_val = r.get('mean_I')

        # Plot heatmap
        fig, ax = plt.subplots(figsize=(5, 5))
        hm = ax.imshow(
            norm,
            cmap='viridis',
            vmin=vmin, vmax=vmax,
            alpha=1.0,
            aspect='equal'
        )
        cbar = fig.colorbar(hm, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label('Pixel Intensity (0–255)')

        # Draw mean intensity marker
        if mean_val is not None:
            cbar.ax.hlines(
                mean_val,
                *cbar.ax.get_xlim(),
                colors='white',
                linestyles='--',
                linewidth=1
            )
            cbar.ax.text(
                cbar.ax.get_xlim()[1],
                mean_val,
                f' μ={mean_val:.1f}',
                va='center',
                ha='left',
                color='white',
                fontsize=8
            )

        ax.set_title(f'ROI Heatmap: {label}')
        ax.axis('off')
        plt.show()

    # 5) Full-image intensity histograms & boxplot
    intensity_arrays = [
        r['intensity_pixels'] for r in results
        if r.get('intensity_pixels') is not None
    ]
    labels      = [
        r['label'] for r in results
        if r.get('intensity_pixels') is not None
    ]
    mean_vals   = [
        r['mean_I'] for r in results
        if r.get('mean_I') is not None
    ]
    mean_labels = [
        r['label'] for r in results
        if r.get('mean_I') is not None
    ]

    for arr, lbl in zip(intensity_arrays, labels):
        try:
            plot_histogram(arr, lbl)
        except Exception as e:
            print(f"Warning: histogram {lbl} failed: {e}")

    if mean_vals:
        try:
            plot_boxplot(mean_vals, mean_labels)
        except Exception as e:
            print(f"Warning: boxplot failed: {e}")

    # --- additional global plots ---
    areas = [r['area_px'] for r in results if r.get('area_px') is not None]
    if areas:
        try:
            plot_area_histogram(areas)
        except Exception as e:
            print(f"Warning: area histogram failed: {e}")

    if areas and mean_vals:
        try:
            plot_area_vs_intensity(areas, mean_vals)
        except Exception as e:
            print(f"Warning: area vs intensity failed: {e}")

    if session['analysis']['shape']:
        circs = [
            r['circularity'] for r in results
            if r.get('circularity') is not None
        ]
        if circs and mean_vals:
            try:
                plot_circularity_vs_intensity(circs, mean_vals)
            except Exception as e:
                print(f"Warning: circ vs intensity failed: {e}")

    # 6) Export results to CSV
    metadata = {
        'analysis_intensity': session['analysis']['intensity'],
        'analysis_shape':     session['analysis']['shape'],
        'analysis_halo':      session['analysis']['halo'],
        'conversion_used':    session['conversion_used'],
    }
    df = build_dataframe(results, metadata)
    outdir = os.path.join(os.path.dirname(__file__), 'session_data')
    os.makedirs(outdir, exist_ok=True)
    csv_path = export_csv(df, outdir)
    print(f"Results written to {csv_path}")

    # 7) Object outlines overlay (green)
    try:
        scale = session['scale']
        h, w = img.shape[:2]
        vis = cv2.resize(
            img,
            (int(w * scale), int(h * scale)),
            interpolation=cv2.INTER_AREA
        ) if scale != 1.0 else img.copy()

        if vis.ndim == 2:
            vis_color = cv2.cvtColor(vis, cv2.COLOR_GRAY2BGR)
        elif vis.shape[2] == 4:
            vis_color = cv2.cvtColor(vis, cv2.COLOR_BGRA2BGR)
        else:
            vis_color = vis.copy()

        for r in results:
            for cnt in r.get('contours', []):
                cnt_disp = (cnt * scale).astype(int)
                cv2.drawContours(vis_color, [cnt_disp], -1, (0, 255, 0), 2)

        cv2.imshow('Object Outlines', vis_color)
        print("Press 'q' or ESC to close outlines.")
        while True:
            if cv2.waitKey(0) & 0xFF in (ord('q'), 27):
                break
        cv2.destroyWindow('Object Outlines')
    except Exception as e:
        print(f"Note: could not display outlines: {e}")


if __name__ == "__main__":
    main()
