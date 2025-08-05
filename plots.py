#!/usr/bin/env python3
"""
plots.py — Matplotlib plotting for RFAM ROI tool.
"""
import matplotlib.pyplot as plt

def plot_histogram(intensities, label):
    """Show histogram of pixel intensities."""
    plt.figure()
    plt.hist(intensities, bins=256, color='gray', edgecolor='black')
    plt.title(f'Intensity Histogram: {label}')
    plt.xlabel('Pixel Intensity')
    plt.ylabel('Frequency')
    plt.show()

def plot_boxplot(means, labels):
    """Show boxplot of mean intensities."""
    plt.figure()
    plt.boxplot(means, labels=labels)
    plt.title('Mean Intensity Boxplot')
    plt.ylabel('Mean Intensity')
    plt.show()

def plot_area_histogram(areas):
    plt.figure()
    plt.hist(areas, bins=20, edgecolor='black')
    plt.title('ROI Area Distribution')
    plt.xlabel('Area (px²)')
    plt.ylabel('Count')
    plt.show()

def plot_area_vs_intensity(areas, means):
    plt.figure()
    plt.scatter(areas, means)
    plt.title('Area vs. Mean Intensity')
    plt.xlabel('Area (px²)')
    plt.ylabel('Mean Intensity')
    plt.show()

def plot_circularity_vs_intensity(circs, means):
    plt.figure()
    plt.scatter(circs, means)
    plt.title('Circularity vs. Mean Intensity')
    plt.xlabel('Circularity')
    plt.ylabel('Mean Intensity')
    plt.show()
