import serial
import cv2
import mediapipe as mp
from picamera2 import Picamera2
import threading
import time

uart = serial.Serial('/dev/ttyAMA0', baudrate=115200, timeout=0.001)  # Adjust port name if needed

# Initialize MediaPipe Face module
mp_face = mp.solutions.face_detection
face_detection = mp_face.FaceDetection()

# Initialize MediaPipe Face Landmarks module
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh()

# Initialize PiCamera
picam2 = Picamera2()
picam2.sensor_resolution = (2304, 1296)  # Set the camera resolution
picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (2304, 1296)}))
picam2.start()

# Set the desired processing resolution (keeping the original resolution)
processing_resolution = (picam2.sensor_resolution[0] // 4, picam2.sensor_resolution[1] // 4)

# Event for communication between threads
position_event = threading.Event()

# Function to process landmarks and print position
def process_landmarks(landmarks, bbox, iw, ih):
    for face_landmarks in landmarks.multi_face_landmarks:
        for lm in face_landmarks.landmark:
            # Extract landmark coordinates
            x, y = int(lm.x * iw), int(lm.y * ih)

            # Draw landmarks
            cv2.circle(resized_frame, (x, y), 1, (0, 0, 255), -1)

            # Set position event
            position_event.data = (x, y)
            position_event.set()

# Thread for printing position
def print_position():
    while True:
        if position_event.wait():  # Wait until position event is set
            position_event.clear()  # Clear the event for next iteration
            x, y = position_event.data
            
            # Check relative position
            if x < processing_resolution[0] // 2 - 30:
                uart.write("r\n".encode())
                print("right")
            elif x > processing_resolution[0] // 2 + 30:
                uart.write("l\n".encode())
                print("left")
        if position_event.wait():  # Wait until position event is set
            position_event.clear()  # Clear the event for next iteration
            x, y = position_event.data
            
            if y < processing_resolution[1] // 2 - 30:
                uart.write("u\n".encode())
                print("up")
            elif y > processing_resolution[1] // 2 + 30:
                uart.write("d\n".encode())
                print("down")

# Start the thread for printing position
position_thread = threading.Thread(target=print_position)
position_thread.daemon = True
position_thread.start()

while True:
    frame = picam2.capture_array()

    # Resize the frame by averaging 4x4 blocks of pixels
    resized_frame = cv2.resize(frame, processing_resolution, interpolation=cv2.INTER_AREA)

    # Convert the resized frame to RGB for MediaPipe
    rgb_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)

    # Detect faces
    face_results = face_detection.process(rgb_frame)

    # If faces are detected, process landmarks
    if face_results.detections:
        for detection in face_results.detections:
            # Extract bounding box
            bboxC = detection.location_data.relative_bounding_box
            ih, iw, _ = resized_frame.shape
            bbox = int(bboxC.xmin * iw), int(bboxC.ymin * ih), \
                   int(bboxC.width * iw), int(bboxC.height * ih)

            # Convert frame to RGB
            rgb_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)

            # Process face landmarks
            landmarks = face_mesh.process(rgb_frame)

            if landmarks.multi_face_landmarks:
                process_landmarks(landmarks, bbox, iw, ih)

    # Display the frame
    cv2.imshow("frame", resized_frame)

    # Wait for a key event (cv2.waitKey(1) allows the OpenCV window to update)
    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break

# Release resources
cv2.destroyAllWindows()
picam2.stop()
