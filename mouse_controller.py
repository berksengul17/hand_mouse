import subprocess
import time
import math

SCREEN_WIDTH = 2560
SCREEN_HEIGHT = 1440
PADDING = 20
SENSITIVITY = 4000

class MouseController:
    def __init__(self):
        self.prev_index = None
        self.prev_pos = None

        self.is_touching = False
        self.touch_start_time = 0.0

    def ydotool_mouse_move(self, x, y):
        # ydotool expects integers
        x = int(x)
        y = int(y)

        print(f"Move mouse {x}, {y}")

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

                    # First frame: just initialize
                    if self.prev_index is None:
                        self.prev_index = (index.x, index.y)
                        self.prev_pos = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
                        return
                    
                    dx = (index.x - self.prev_index[0]) * SENSITIVITY
                    dy = (index.y - self.prev_index[1]) * SENSITIVITY

                    prev_x = self.prev_pos[0]
                    prev_y = self.prev_pos[1]

                    cur_x = max(PADDING, min(SCREEN_WIDTH - PADDING, prev_x - dx))  # note: minus to invert direction
                    cur_y = max(PADDING, min(SCREEN_HEIGHT - PADDING, prev_y + dy))

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
                            self.smooth_move(prev_x, prev_y, cur_x, cur_y)
       
                    else:
                        # Touch just ended
                        if self.is_touching:
                            self.is_touching = False
                            self.mouse_event("80") # mouse up

                        # Interpolate small steps
                        if (abs(dx) >= 10 or abs(dy) >= 10):
                            self.smooth_move(prev_x, prev_y, cur_x, cur_y)
                    
                    self.prev_pos = (cur_x, cur_y)
                    self.prev_index = (index.x, index.y)

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
