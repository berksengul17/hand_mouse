import cv2
from mouse_controller import MouseController
from hand_tracker import HandTracker

def main():
    mouse_controller = MouseController()
    hand_tracker = HandTracker()

    cam = cv2.VideoCapture(4)

    while True:
        ret, frame = cam.read()
        if not ret:
            break
        
        ts = cam.get(cv2.CAP_PROP_POS_MSEC)
        result = hand_tracker.detect_video(frame, ts)
        mouse_controller.move_mouse(result)

        if cv2.waitKey(1) & 0xFF == 27:
            break
    
    # mouse up just in case
    mouse_controller.mouse_event("80")
    hand_tracker.close()
    
    cam.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
   main()