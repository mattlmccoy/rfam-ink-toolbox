#!/usr/bin/env python3
"""
visualize_intensity_multi_matplotlib.py

Loads one or more RFAM‐tool session CSVs and combines their analyses.
Then produces Matplotlib plots:
  1) Boxplot of replicate mean intensities by ink type
  2) Bar chart of average mean intensity per ink type
  3) Scatter of individual replicate intensities (with jitter)

Dependencies: tkinter, pandas, numpy, matplotlib
"""
import os
import tkinter as tk
from tkinter import filedialog

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def select_csvs():
    root = tk.Tk()
    root.withdraw()
    paths = filedialog.askopenfilenames(
        title="Select one or more RFAM session CSVs",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
    )
    root.destroy()
    return list(paths)

def load_and_tag(paths):
    """Read each CSV and add a __source column."""
    frames = []
    for p in paths:
        df = pd.read_csv(p)
        df["__source"] = os.path.basename(p)
        frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

def main():
    # 1) Pick files
    paths = select_csvs()
    if not paths:
        print("No files selected. Exiting.")
        return

    # 2) Load & tag
    df = load_and_tag(paths)
    if df.empty:
        print("No data loaded. Exiting.")
        return

    # 3) Map ink_key -> description
    desc_map = {
        1: "5 wt% C, petroleum",
        2: "25 wt% C, petroleum",
        3: "25 wt% C, IPA",
        4: "Sharpie (control)"
    }
    df["ink_key"] = df["ink_key"].astype(int)
    df["ink_desc"] = df["ink_key"].map(desc_map)

    # 4) Matplotlib style
    plt.style.use("ggplot")

    # Determine the order of categories
    order = list(desc_map.values())

    # 5) Boxplot
    data = [ df[df["ink_desc"]==ink]["mean_I"].values for ink in order ]
    fig, ax = plt.subplots(figsize=(8,5))
    bp = ax.boxplot(
        data,
        labels=order,
        patch_artist=True,
        medianprops=dict(color="black"),
        boxprops=dict(facecolor="lightgray", edgecolor="gray")
    )
    ax.set_title("Mean Intensity Distribution by Ink Type")
    ax.set_ylabel("Mean Intensity (0–255)")
    ax.tick_params(axis="x", rotation=45)
    plt.tight_layout()
    plt.show()

    # 6) Bar chart of averages ± std
    means = df.groupby("ink_desc")["mean_I"].mean().reindex(order)
    stds  = df.groupby("ink_desc")["mean_I"].std().reindex(order).fillna(0)

    x = np.arange(len(order))
    fig, ax = plt.subplots(figsize=(6,4))
    ax.bar(x, means.values, yerr=stds.values, capsize=5, color="lightblue", edgecolor="gray")
    ax.set_xticks(x)
    ax.set_xticklabels(order, rotation=45, ha="right")
    ax.set_title("Average Mean Intensity per Ink Type")
    ax.set_ylabel("Mean Intensity (0–255)")
    plt.tight_layout()
    plt.show()

    # 7) Scatter with jitter
    fig, ax = plt.subplots(figsize=(8,5))
    for i, ink in enumerate(order):
        vals = df[df["ink_desc"]==ink]["mean_I"].values
        # add horizontal jitter
        xs = np.random.normal(i, 0.05, size=len(vals))
        ax.scatter(xs, vals, alpha=0.8, edgecolors="w", s=60)
    ax.set_xticks(x)
    ax.set_xticklabels(order, rotation=45, ha="right")
    ax.set_title("Individual Replicate Mean Intensities")
    ax.set_ylabel("Mean Intensity (0–255)")
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
