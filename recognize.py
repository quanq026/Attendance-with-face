import os
import cv2
import face_recognition
import numpy as np
from datetime import datetime
from utils import load_encodings, popup, save_log, get_employee_name

def recognize_face():
    known = load_encodings()
    if not known:
        popup("Error", "No employees registered.")
        return
    popup("Instructions", "Align your face in the camera. Press 'q' to cancel.")
    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        popup("Error", "Cannot open camera.")
        return
    cv2.namedWindow("Check-In", cv2.WINDOW_NORMAL)
    cv2.setWindowTitle("Check-In", "Face Recognition")
    while True:
        ret, frame = cam.read()
        if not ret:
            popup("Error", "Cannot read camera frame.")
            break
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(rgb)
        encodings = face_recognition.face_encodings(rgb, locations)
        for face_encoding in encodings:
            ids = list(known.keys())
            known_encs = [np.array(known[eid]["encoding"]) for eid in ids]
            distances = face_recognition.face_distance(known_encs, face_encoding)
            if len(distances) > 0 and distances.min() < 0.6:
                idx = distances.argmin()
                emp_id = ids[idx]
                timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                save_log(emp_id, timestamp)
                name = get_employee_name(emp_id)
                popup("Success", f"Checked-in {name} (ID: {emp_id}) at {timestamp}")
                cam.release()
                cv2.destroyAllWindows()
                return
        cv2.imshow("Check-In", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or cv2.getWindowProperty("Check-In", cv2.WND_PROP_VISIBLE) < 1:
            break
    cam.release()
    cv2.destroyAllWindows()