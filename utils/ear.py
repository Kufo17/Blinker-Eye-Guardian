import numpy as np

def calculate_ear(eye_points):
    """
    Calculates the Eye Aspect Ratio (EAR) given 6 landmark points.
    eye_points should be a list/array of 6 points: [p1, p2, p3, p4, p5, p6]
    where:
    - p1, p4 are the horizontal corner points.
    - p2, p6 and p3, p5 are vertical pairs.
    """
    # Vertical distances
    v1 = np.linalg.norm(eye_points[1] - eye_points[5]) # p2 - p6
    v2 = np.linalg.norm(eye_points[2] - eye_points[4]) # p3 - p5
    
    # Horizontal distance
    h = np.linalg.norm(eye_points[0] - eye_points[3]) # p1 - p4
    
    # Avoid division by zero
    if h == 0:
        return 0.0
        
    return (v1 + v2) / (2.0 * h)
