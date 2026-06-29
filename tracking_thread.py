import cv2
import numpy as np
import time
import mediapipe as mp
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QImage
from utils.ear import calculate_ear

class TrackingThread(QThread):
    # Signals to communicate with UI
    calibration_message = pyqtSignal(str)
    blink_detected = pyqtSignal()
    ear_updated = pyqtSignal(float)
    face_detected = pyqtSignal(bool)
    frame_updated = pyqtSignal(QImage)
    status_message = pyqtSignal(str)
    night_boost_active = pyqtSignal(bool)
    calibration_finished = pyqtSignal()
    calibration_stage_changed = pyqtSignal(int)
    verification_blink = pyqtSignal(int)

    # Landmark indices for Left and Right eyes
    LEFT_EYE_INDICES = [362, 385, 387, 263, 373, 380]
    RIGHT_EYE_INDICES = [33, 160, 158, 133, 153, 144]

    def __init__(self):
        super().__init__()
        self.running = False
        self.send_preview = False
        self.language = "en"  # Active language
        self.camera_active = False
        
        # Calibration state variables
        self.calibrated = True
        self.threshold = 0.2  # Default fallback threshold
        self.closed_frames_count = 0

    def recalibrate(self):
        """Resets the calibration state to start fresh."""
        self.closed_frames_count = 0
        self.calibrated = True
        self.camera_active = False
        
        msg = "Recalibration started." if self.language == "en" else "Запущено повторне калібрування."
        self.status_message.emit(msg)

    def set_send_preview(self, enabled):
        """Toggles sending video frames for UI preview to save CPU."""
        self.send_preview = enabled

    def stop(self):
        """Stops the thread loop and blocks until finished."""
        self.running = False
        self.camera_active = False
        self.wait()

    def run(self):
        self.running = True
        
        # Initialize MediaPipe Face Mesh
        mp_face_mesh = mp.solutions.face_mesh
        face_mesh = mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Start camera capture
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            msg = "Error: Failed to access camera." if self.language == "en" else "Помилка: Не вдалося отримати доступ до камери."
            self.status_message.emit(msg)
            face_mesh.close()
            return
            
        # Configure HD resolution
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        msg = "Camera started successfully. Searching for face..." if self.language == "en" else "Камеру успішно запущено. Шукаю обличчя..."
        self.status_message.emit(msg)
        
        # For blink state tracking (prevents multiple signals for one blink)
        eye_closed = False
        frame_count = 0
        
        while self.running:
            ret, frame = cap.read()
            if not ret:
                msg = "Error: Failed to receive frame from camera." if self.language == "en" else "Помилка: Кадр з камери не отримано."
                self.status_message.emit(msg)
                time.sleep(0.03)  # Avoid tight loop in case of errors
                continue
                
            self.camera_active = True
                
            frame_count += 1
            if frame_count % 3 != 0:
                time.sleep(0.01)
                continue
                
            # Flip horizontally for natural mirror look
            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape
            
            # Programmatic brightness boost (Night Brightness Boost)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            mean_brightness = np.mean(gray)
            if mean_brightness < 50:
                frame = cv2.convertScaleAbs(frame, alpha=1.8, beta=50)
                self.night_boost_active.emit(True)
            else:
                self.night_boost_active.emit(False)
            
            # Convert to RGB for MediaPipe processing
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(rgb_frame)
            
            face_found = results.multi_face_landmarks is not None
            self.face_detected.emit(face_found)
            
            avg_ear = None
            if face_found:
                face_landmarks = results.multi_face_landmarks[0]
                landmarks = face_landmarks.landmark
                
                # Extract coordinates
                left_eye_pts = [
                    np.array([landmarks[idx].x * w, landmarks[idx].y * h])
                    for idx in self.LEFT_EYE_INDICES
                ]
                right_eye_pts = [
                    np.array([landmarks[idx].x * w, landmarks[idx].y * h])
                    for idx in self.RIGHT_EYE_INDICES
                ]
                
                # Calculate EAR values
                left_ear = calculate_ear(left_eye_pts)
                right_ear = calculate_ear(right_eye_pts)
                avg_ear = (left_ear + right_ear) / 2.0
                
                # Draw landmarks on frame
                for pt in left_eye_pts + right_eye_pts:
                    cv2.circle(frame, (int(pt[0]), int(pt[1])), 3, (0, 255, 0), -1)
                    
                # Emit current EAR value
                self.ear_updated.emit(avg_ear)
                
                # Blink detection
                if avg_ear < self.threshold:
                    self.closed_frames_count += 1
                else:
                    if 1 <= self.closed_frames_count <= 4:
                        self.blink_detected.emit()
                    self.closed_frames_count = 0
            else:
                # Face lost
                self.closed_frames_count = 0

            
            # Emit processed frame for UI preview if enabled
            if self.send_preview:
                if face_found and avg_ear is not None:
                    # Gather coordinates of both eyes to calculate crop bounding box
                    all_eye_pts = left_eye_pts + right_eye_pts
                    xs = [pt[0] for pt in all_eye_pts]
                    ys = [pt[1] for pt in all_eye_pts]
                    
                    min_x = max(0, int(min(xs)) - 35)
                    max_x = min(w, int(max(xs)) + 35)
                    min_y = max(0, int(min(ys)) - 35)
                    max_y = min(h, int(max(ys)) + 35)
                    
                    if max_x > min_x and max_y > min_y:
                        preview_frame = frame[min_y:max_y, min_x:max_x]
                    else:
                        preview_frame = frame
                else:
                    preview_frame = frame
                    
                rgb_preview = cv2.cvtColor(preview_frame, cv2.COLOR_BGR2RGB)
                preview_h, preview_w, preview_ch = rgb_preview.shape
                bytes_per_line = preview_ch * preview_w
                q_img = QImage(
                    rgb_preview.data, 
                    preview_w, 
                    preview_h, 
                    bytes_per_line, 
                    QImage.Format.Format_RGB888
                ).copy() # Use copy() for thread-safety and memory lifetime
                self.frame_updated.emit(q_img)
                
            # Cap thread frequency to ~30 FPS
            time.sleep(0.03)
            
        # Clean up resources
        self.camera_active = False
        cap.release()
        face_mesh.close()
        msg = "Camera stopped." if self.language == "en" else "Камеру зупинено."
        self.status_message.emit(msg)
