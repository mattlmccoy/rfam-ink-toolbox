#!/usr/bin/env python3
"""
analyzer.py — compute metrics for RFAM ROI tool.
"""
import cv2
import numpy as np

def threshold_image(image):
    """
    Compute a binary mask using Otsu's threshold.

    Parameters
    ----------
    image : ndarray
        Input image, which may be grayscale or BGR.  If BGR, it will be
        converted to grayscale internally.

    Returns
    -------
    mask : ndarray of bool
        A boolean array where `True` indicates pixels above the Otsu
        threshold (foreground) and `False` indicates background.
    """
    gray = image
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(
        gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    return thresh.astype(bool)


def compute_metrics(image, roi, px_per_mm=None,
                    do_intensity=True, do_shape=False, do_halo=False):
    """
    Compute metrics for a given ROI.  Metrics are calculated on the
    segmented object(s) within the ROI rather than on the entire ROI
    area.  A global Otsu threshold is applied to the ROI to separate
    dark objects (ink blots) from the brighter background.  Intensity
    statistics are then computed on the object pixels only.  Shape
    metrics and halo eccentricity are derived from the object mask.

    Returns
    -------
    results : dict
        Dictionary of computed metrics.  Extra keys:
          - 'mask_full': boolean mask of the object in full-resolution coords
          - 'contours': list of OpenCV contours for the object
          - 'intensity_pixels': 1D array of all object pixel values
    """
    # 1) Build binary ROI mask at full resolution
    mask = np.zeros(image.shape[:2], dtype=np.uint8)
    roi_type = roi.get('type')
    if roi_type == 'polygon':
        pts = np.array(roi['points'], dtype=np.int32)
        cv2.fillPoly(mask, [pts], 255)
    elif roi_type == 'circle':
        center = tuple(map(int, roi['center']))
        radius = int(roi['radius'])
        cv2.circle(mask, center, radius, 255, -1)
    else:
        # unsupported ROI types (e.g., ruler) → no metrics
        return {}

    # 2) Convert image to grayscale
    gray = image
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 3) Apply ROI mask to grayscale
    #    (not strictly needed for Otsu, but preserves blackout outside ROI)
    roi_gray = cv2.bitwise_and(gray, gray, mask=mask)

    # 4) If ROI is empty, bail
    if not np.any(mask):
        return {}

    results = {}

    # 5) Global Otsu threshold (bright vs. dark)
    global_thresh = threshold_image(image)  # True = bright region
    # Invert within ROI to get dark-ink object pixels
    object_mask = np.zeros_like(mask, dtype=np.uint8)
    object_mask[(~global_thresh) & (mask.astype(bool))] = 255

    # 6) Extract contours of the object(s)
    contours, _ = cv2.findContours(
        object_mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )
    results['contours'] = contours
    # Expose full-resolution boolean mask for downstream cropping
    results['mask_full'] = object_mask.astype(bool)

    # 7) Intensity metrics on object pixels
    if do_intensity:
        obj_pixels = gray[object_mask.astype(bool)]
        if obj_pixels.size > 0:
            results['mean_I']   = float(np.mean(obj_pixels))
            results['median_I'] = float(np.median(obj_pixels))
            results['std_I']    = float(np.std(obj_pixels))
        else:
            results['mean_I'] = results['median_I'] = results['std_I'] = None
        results['area_px'] = int(np.sum(object_mask > 0))
        # raw array for plotting histograms / heatmaps
        results['intensity_pixels'] = obj_pixels

    # 8) Shape metrics (largest contour)
    if do_shape and contours:
        cnt = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(cnt)
        perim = cv2.arcLength(cnt, True)
        results['perimeter_px'] = float(perim)
        results['circularity'] = (
            float(4 * np.pi * area / (perim**2))
            if perim > 0 else None
        )
        M = cv2.moments(cnt)
        if M['m00'] != 0:
            mu20 = M['mu20'] / M['m00']
            mu02 = M['mu02'] / M['m00']
            mu11 = M['mu11'] / M['m00']
            term = np.sqrt((mu20 - mu02)**2 + 4 * mu11**2)
            num = (mu20 + mu02 - term)
            den = (mu20 + mu02 + term)
            results['inertia_ratio'] = (
                float(num / den) if den != 0 else None
            )
        hull = cv2.convexHull(cnt)
        hull_area = cv2.contourArea(hull)
        results['convexity'] = (
            float(area / hull_area) if hull_area > 0 else None
        )

    # 9) Halo eccentricity
    if do_halo and contours:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))
        core = cv2.erode(object_mask, kernel, iterations=1)
        halo = cv2.subtract(object_mask, core)
        halo_cnts, _ = cv2.findContours(
            halo,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        if halo_cnts:
            hc = max(halo_cnts, key=cv2.contourArea)
            if len(hc) >= 5:
                (cx, cy), axes, angle = cv2.fitEllipse(hc)
                a, b = axes[0]/2, axes[1]/2
                if a > 0:
                    ecc = np.sqrt(1 - (b*b)/(a*a))
                    results['halo_eccentricity'] = float(ecc)

    # 10) Area conversion
    if px_per_mm and isinstance(px_per_mm, (int, float)) and px_per_mm > 0:
        if 'area_px' in results:
            results['area_mm2'] = results['area_px'] / (px_per_mm**2)

    return results
