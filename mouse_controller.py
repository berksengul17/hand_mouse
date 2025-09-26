import subprocess
import time
import math

SCREEN_WIDTH = 2560
SCREEN_HEIGHT = 1440
SMOOTHING = 0.4

class MouseController:
    def __init__(self):
        self.prev_pos = (0, 0)
        self.is_touching = False
        self.touch_start_time = 0.0

    def ydotool_mouse_move(self, x, y):
        # ydotool expects integers
        x = int(x)
        y = int(y)

        try:
            subprocess.run(
                ["ydotool", "mousemove", "-a", str(x), str(y)],
                check=True
            )
        except subprocess.CalledProcessError as e:
            print("Error running ydotool:", e)

    def move_mouse(self, detection_result):
        if detection_result.hand_landmarks:
            for i in range(len(detection_result.hand_landmarks)):
                handedness = detection_result.handedness[i][0]

                if handedness.category_name == "Left":
                    index = detection_result.hand_landmarks[i][8]
                    thumb = detection_result.hand_landmarks[i][4]

                    target_x = (1 - index.x) * SCREEN_WIDTH
                    target_y = index.y * SCREEN_HEIGHT

                    prev_x, prev_y = self.prev_pos

                    dx = target_x - prev_x
                    dy = target_y - prev_y

                    # Apply smoothing
                    smooth_x = prev_x + SMOOTHING * dx
                    smooth_y = prev_y + SMOOTHING * dy

                    # if touch detected, start a timer for hold
                    if self.detect_touch(index, thumb):
                        now = time.time()

                        if not self.is_touching:
                            self.is_touching = True
                            self.touch_start_time = now
                            self.mouse_event("40") # mouse down
                        
                        # if the user holds the touch more than 1 second
                        # start moving the mouse around
                        hold_duration = now - self.touch_start_time
                        if (hold_duration > 1.0):
                            self.smooth_move(prev_x, prev_y, smooth_x, smooth_y)
                            self.prev_pos = (smooth_x, smooth_y)
       
                    else:
                        # Touch just ended
                        if self.is_touching:
                            self.is_touching = False
                            self.mouse_event("80") # mouse up

                        # Interpolate small steps
                        if (abs(dx) >= 10 or abs(dy) >= 10):
                            self.smooth_move(prev_x, prev_y, smooth_x, smooth_y)
                            self.prev_pos = (smooth_x, smooth_y)


    def smooth_move(self, prev_x, prev_y, target_x, target_y, steps=10, delay=0.005):
        for i in range(1, steps + 1):
            interp_x = prev_x + (target_x - prev_x) * i / steps
            interp_y = prev_y + (target_y - prev_y) * i / steps
            self.ydotool_mouse_move(interp_x, interp_y)
            time.sleep(delay)

    def detect_touch(self, index, thumb):
        d = self.distance(index, thumb)

        if d < 0.05:  # threshold, tune this!
            return True
        return False
    
    # i can create a seperate data class or something similar for the codes
    def mouse_event(self, code):
        subprocess.run(["ydotool", "click", code], 
                       check=True, 
                       stdout=subprocess.DEVNULL)
    
    def distance(self, a, b):
        return math.sqrt((a.x - b.x)**2 + (a.y - b.y)**2 + (a.z - b.z)**2)
