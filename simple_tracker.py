import cv2
import mediapipe as mp
import numpy as np
import time
from PIL import Image, ImageDraw, ImageFont

# Landmark indices for Left and Right eyes
LEFT_EYE_INDICES = [362, 385, 387, 263, 373, 380]
RIGHT_EYE_INDICES = [33, 160, 158, 133, 153, 144]

def calculate_ear(eye_points):
    # Vertical distances
    v1 = np.linalg.norm(eye_points[1] - eye_points[5]) # p2 - p6
    v2 = np.linalg.norm(eye_points[2] - eye_points[4]) # p3 - p5
    
    # Horizontal distance
    h = np.linalg.norm(eye_points[0] - eye_points[3]) # p1 - p4
    
    # Eye Aspect Ratio (EAR)
    ear = (v1 + v2) / (2.0 * h)
    return ear

def get_font(size):
    # List of common fonts for cross-platform compatibility
    fonts_to_try = ["arial.ttf", "calibri.ttf", "Helvetica.ttc", "DejaVuSans.ttf"]
    for font_name in fonts_to_try:
        try:
            return ImageFont.truetype(font_name, size)
        except IOError:
            continue
    # Fallback font
    return ImageFont.load_default()

def main():
    # Initialize MediaPipe Face Mesh
    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )
    
    # Start video capture (webcam 0)
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Помилка: Не вдалося відкрити камеру.")
        return
        
    print("Програма запущена. Знайдіть обличчя в кадрі для початку калібрування.")
    print("Натисніть 'q' для виходу.")
    
    # Calibration variables
    calibration_start_time = None
    open_ear_values = []
    closed_ear_values = []
    threshold = 0.2  # Default threshold
    calibrated = False
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Помилка: Не вдалося отримати кадр.")
            break
            
        # Flip the image horizontally for mirror view
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        
        # Convert BGR (OpenCV) to RGB (MediaPipe)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process the frame with Face Mesh
        results = face_mesh.process(rgb_frame)
        
        # Draw eyelids landmarks using OpenCV first
        avg_ear = None
        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                landmarks = face_landmarks.landmark
                
                # Get the pixel coordinates of the left eye landmarks
                left_eye_pts = [
                    np.array([landmarks[idx].x * w, landmarks[idx].y * h])
                    for idx in LEFT_EYE_INDICES
                ]
                
                # Get the pixel coordinates of the right eye landmarks
                right_eye_pts = [
                    np.array([landmarks[idx].x * w, landmarks[idx].y * h])
                    for idx in RIGHT_EYE_INDICES
                ]
                
                # Calculate EAR for both eyes
                left_ear = calculate_ear(left_eye_pts)
                right_ear = calculate_ear(right_eye_pts)
                avg_ear = (left_ear + right_ear) / 2.0
                
                # Draw green points on eyelids landmarks
                for pt in left_eye_pts + right_eye_pts:
                    cv2.circle(frame, (int(pt[0]), int(pt[1])), 3, (0, 255, 0), -1)
        
        # Convert BGR frame to RGB for PIL drawing (to support Cyrillic text)
        img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)
        
        # Get fonts
        font_small = get_font(24)
        font_large = get_font(30)
        
        # Handle calibration logic and text drawing
        if results.multi_face_landmarks and avg_ear is not None:
            if not calibrated:
                # Start calibration timer when face is first detected
                if calibration_start_time is None:
                    calibration_start_time = time.time()
                
                elapsed = time.time() - calibration_start_time
                
                if elapsed < 3.0:
                    # Phase 1: Open eyes (first 3 seconds)
                    open_ear_values.append(avg_ear)
                    time_left = max(1, int(3.0 - elapsed) + 1)
                    text = f"КАЛІБРУВАННЯ: Дивіться в камеру (ОЧІ ВІДКРИТІ)...\nЗалишилось: {time_left} сек\nПоточний EAR: {avg_ear:.3f}"
                    draw.text((30, 40), text, font=font_large, fill=(255, 255, 255), spacing=8)
                elif elapsed < 6.0:
                    # Phase 2: Closed eyes (next 3 seconds)
                    closed_ear_values.append(avg_ear)
                    time_left = max(1, int(6.0 - elapsed) + 1)
                    text = f"КАЛІБРУВАННЯ: ЗАКРИЙТЕ ОЧІ...\nЗалишилось: {time_left} сек\nПоточний EAR: {avg_ear:.3f}"
                    draw.text((30, 40), text, font=font_large, fill=(255, 255, 255), spacing=8)
                else:
                    # Calculate custom threshold
                    avg_open_ear = np.mean(open_ear_values) if open_ear_values else 0.3
                    avg_closed_ear = np.mean(closed_ear_values) if closed_ear_values else 0.15
                    
                    threshold = avg_closed_ear + 0.35 * (avg_open_ear - avg_closed_ear)
                    
                    print("\n" + "="*40)
                    print(" КАЛІБРУВАННЯ ЗАВЕРШЕНО УСПІШНО!")
                    print(f" Середній EAR (відкриті очі): {avg_open_ear:.4f}")
                    print(f" Середній EAR (закриті очі): {avg_closed_ear:.4f}")
                    print(f" Розрахований поріг (threshold): {threshold:.4f}")
                    print("="*40 + "\n")
                    
                    calibrated = True
            else:
                # Normal eye tracking phase
                if avg_ear < threshold:
                    status_text = "CLOSED"
                    status_color = (255, 0, 0) # Red in RGB
                else:
                    status_text = "OPEN"
                    status_color = (0, 255, 0) # Green in RGB
                    
                draw.text((30, 40), f"EAR: {avg_ear:.3f}", font=font_small, fill=(255, 255, 255))
                draw.text((30, 80), f"Поріг: {threshold:.3f}", font=font_small, fill=(255, 255, 255))
                draw.text((30, 120), f"Статус: {status_text}", font=font_large, fill=status_color)
        else:
            # Face lost or not yet detected
            if not calibrated:
                if calibration_start_time is not None:
                    # Calibration was started but face is lost
                    draw.text((30, 40), "Обличчя втрачено!\nБудь ласка, поверніться в кадр...", font=font_large, fill=(255, 0, 0), spacing=8)
                else:
                    # Face not yet found
                    draw.text((30, 40), "Шукаю обличчя для початку калібрування...", font=font_large, fill=(255, 255, 255))
            else:
                # Face lost in tracking mode
                draw.text((30, 40), "Обличчя не виявлено", font=font_large, fill=(255, 0, 0))
                
        # Convert PIL back to BGR for OpenCV
        frame = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
        
        # Display the frame
        cv2.imshow('Eye Tracker', frame)
        
        # Check if 'q' is pressed to quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    # Clean up
    cap.release()
    cv2.destroyAllWindows()
    face_mesh.close()

if __name__ == '__main__':
    main()
