# -*- coding: utf-8 -*-
"""
CELLBANGLE: A Python module for visualizing and tracking ellipsioids through
            a video file at close to real-time. This process would yield
            similar data to FACS, ideally

EXAMPLE:    Mazutis, Linas, et al. "Single-cell analysis and sorting using 
            droplet-based microfluidics." Nature protocols 8.5 (2013): 870-891.
            (http://www.nature.com/nprot/journal/v8/n5/full/nprot.2013.046.html)
         
TODO:       [ ] Introduce cell tracking
            [ ] Add real-time image processing feature
            [ ] Give real-time metrics for cell size/features
            
Created on Wed Dec 24 13:03:24 2014

@author: Dan Sweeney (sweeneyd@vt.edu)
         Nico Baudoin
"""

import cv2
import numpy as np

# ============================================================================
#               Useful DSP and Video Processing Functions
# ============================================================================
class cellBangle(object):
    def __init__(self, filename):
        cap = cv2.VideoCapture(filename)
        meds = getMedian(cap)
        while cap.isOpened():
            try:
                ret, frame = cap.read()
                if frame != None:
                    thresh, contours, coord_list = getFiltered(frame, meds)
                    #thresh = getCanny(frame) 
                else:
                    break
                cv2.imshow('thresh', thresh)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    cap.release()
                    cv2.destroyAllWindows()
                    break
                
            except KeyboardInterrupt:
                cv2.destroyAllWindows()
                break
        
# Find median pixel values in a video    
def getMedian(cap):
    total_data = []
    while cap.isOpened():
        try:
            ret, frame = cap.read()
            if frame == None:
                break
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            total_data.append(gray)
        except KeyboardInterrupt:
            cv2.destroyAllWindows()
            break
    lin_stack = np.vstack(x.ravel() for x in total_data)
    lin_median = np.median(lin_stack,axis = 0)
    meds = np.uint8(lin_median.reshape(total_data[0].shape))
    return meds

# Remove background and +/-10% of the image 
def trimEdges(raw, background):
    b = np.abs(raw - background)
    indices = b > 225
    b[indices] = 0
    return b

# Find ellipsoids or circles in object and project them onto image mask
def getContours(img, fit_type='ellipse', AREA_EXCLUSION_LIMITS=(200, 2000), CELL_RADIUS_THRESHOLD = 4):
    contours, hierarchy = cv2.findContours(img,
                                           cv2.RETR_TREE,
                                           cv2.CHAIN_APPROX_SIMPLE)
    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    coord_list = []
    for i in range(len(contours)):
        if fit_type == 'circle':
            radius_list = []
            center_list = []
            (x,y),radius = cv2.minEnclosingCircle(contours[i])
            if radius > CELL_RADIUS_THRESHOLD:
                center = (int(x), int(y))
                center_list.append(center)
                radius_list.append(radius)
                cv2.circle(img,center,int(radius),(0,255,0),-11)
            coord_list.append([center_list, radius_list])
            
        elif fit_type == 'ellipse':
            if len(contours[i]) >= 5:
                ellipse = cv2.fitEllipse(contours[i])
                area = np.pi*np.product(ellipse[1])
                if area >= AREA_EXCLUSION_LIMITS[0] and area < AREA_EXCLUSION_LIMITS[1]:
                    cv2.ellipse(img,ellipse,(0,255,0),-1)
    return img, contours, coord_list

# Get     
def getFiltered(img, meds, CELL_BINARY_THRESHOLD = 127):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    subBG = trimEdges(gray, meds)
    thresh = cv2.erode(subBG, None, 10)
    thresh = cv2.dilate(thresh, None, 10)
    ret,thresh = cv2.threshold(subBG,CELL_BINARY_THRESHOLD,255,0)
    thresh, contours, coord_list = getContours(thresh)
    return thresh, contours, coord_list
    
def getCanny(img, meds, CELL_BINARY_THRESHOLD = 127):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    subBG = trimEdges(gray, meds)
    thresh = cv2.erode(subBG, None, 10)
    thresh = cv2.dilate(thresh, None, 10)
    ret,thresh = cv2.threshold(subBG,CELL_BINARY_THRESHOLD,255,0)
    thresh = cv2.Canny(thresh, 5, 10)
    return thresh
    
# ============================================================================
#                           Video Analysis
# ============================================================================

if __name__ == '__main__':
    filename = '/Users/Dan/Movies/nprot.mp4'
    cb = cellBangle(filename)