import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerOptions, RunningMode
from mediapipe import solutions
from mediapipe.framework.formats import landmark_pb2

WIDTH = 800
HEIGHT = 600

MARGIN = 10  # pixels
FONT_SIZE = 1
FONT_THICKNESS = 1
HANDEDNESS_TEXT_COLOR = (88, 205, 54) # vibrant green

# path to your downloaded model .task file
MODEL_PATH = "hand_landmarker.task"

class HandTracker:
  def __init__(self):
    self.options = HandLandmarkerOptions(
      base_options=mp.tasks.BaseOptions(model_asset_path=MODEL_PATH),
      running_mode=RunningMode.VIDEO,   # or IMAGE if single image
      min_hand_detection_confidence=0.5,
      num_hands = 2,
      min_hand_presence_confidence=0.5,
      min_tracking_confidence=0.5,
    )

    self.landmarker = HandLandmarker.create_from_options(self.options)

  def detect_video(self, frame, ts):
    # Convert BGR (OpenCV) to RGB
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    # Create mp.Image from numpy array
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)

    # Timestamp in ms (just use frame count or time)
    timestamp_ms = int(ts)

    result = self.landmarker.detect_for_video(mp_image, timestamp_ms)
    annotated_image = self.draw_landmarks_on_image(mp_image.numpy_view(), result)
    cv2.imshow("cam", cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR))

    # Detect landmarks
    return result

  def draw_landmarks_on_image(self, rgb_image, detection_result):
    hand_landmarks_list = detection_result.hand_landmarks
    handedness_list = detection_result.handedness
    annotated_image = np.copy(rgb_image)

    # Loop through the detected hands to visualize.
    for idx in range(len(hand_landmarks_list)):
      hand_landmarks = hand_landmarks_list[idx]
      handedness = handedness_list[idx]

      # Draw the hand landmarks.
      hand_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
      hand_landmarks_proto.landmark.extend([
        landmark_pb2.NormalizedLandmark(x=landmark.x, y=landmark.y, z=landmark.z) for landmark in hand_landmarks
      ])
      solutions.drawing_utils.draw_landmarks(
        annotated_image,
        hand_landmarks_proto,
        solutions.hands.HAND_CONNECTIONS,
        solutions.drawing_styles.get_default_hand_landmarks_style(),
        solutions.drawing_styles.get_default_hand_connections_style())

      # Get the top left corner of the detected hand's bounding box.
      height, width, _ = annotated_image.shape
      x_coordinates = [landmark.x for landmark in hand_landmarks]
      y_coordinates = [landmark.y for landmark in hand_landmarks]
      text_x = int(min(x_coordinates) * width)
      text_y = int(min(y_coordinates) * height) - MARGIN

      # Draw handedness (left or right hand) on the image.
      cv2.putText(annotated_image, f"{handedness[0].category_name}",
                  (text_x, text_y), cv2.FONT_HERSHEY_DUPLEX,
                  FONT_SIZE, HANDEDNESS_TEXT_COLOR, FONT_THICKNESS, cv2.LINE_AA)

    return annotated_image

  def close(self):
      if self.landmarker:
          self.landmarker.close()

