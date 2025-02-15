import cv2  
import mediapipe as mp  
import pyautogui as pag  
from scipy.interpolate import interp1d  
from ctypes import cast, POINTER  
from comtypes import CLSCTX_ALL  
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume  
import numpy as np  
from pynput.keyboard import Controller  
import keyboard  
import webbrowser 

############## Initialization ##############

cap = cv2.VideoCapture(0)  # Use scrcpy's mirrored screen as input
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1980)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

mpHands = mp.solutions.hands # Load Mediapipe Hands module
hands = mpHands.Hands(min_detection_confidence=0.70, min_tracking_confidence=0.70)
mpDraw = mp.solutions.drawing_utils #draw landmarks on the detected hand.

# Audio volume control setup
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume.iid, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))
volMin, volMax = volume.GetVolumeRange()[:2]

# Constants and variables
lms = [4, 8, 12, 16, 20]  # Key landmarks for fingers
volBar = 400  # Initial position of the volume bar


# Utility functions

def detectGesture(fingers):
    if fingers == [False, True, False, False, False]:
        return "INDEX"  # Increase Volume
    elif fingers == [True, False, False, False, False]:
        return "THUMB"  # Decrease Volume
    elif fingers == [True, True, True, True, True]:
        return "FIVE"  # Pause 
    elif fingers == [False, True, True, True, True]:
        return "FIST"  # Play
    elif fingers == [False, False, True, False, False]:
        return "MIDDLE" 
    elif fingers == [False, True, True, False, False]:
        return "VICTORY"
    elif fingers == [False, True, False, False, True]:
        return "SWAG"
    return "NONE"
 

def remap(x, in_min, in_max, out_min, out_max, flag=0):
    if x > in_max:
        return out_max 
    if x < in_min:
        return out_min 
    try:
        m = interp1d([in_min, in_max], [out_min, out_max]) #SciPy’s interpolation module.
        return float(m(x)) #Creates a mapping function and  Converts distance into volume shown in volume bar
    except Exception as e:
        print(f"Error in remapping: {e}")
        return 0.0


netflix_opened=False
youtube_opened=False


# Main loop

while True:  # Infinite loop to continuously capture frames from the camera

    success, img = cap.read()  # Read a frame from the camera 
    if not success:  # Check if the frame was successfully captured
        print("Failed to access the camera.")  # Print an error message if capturing fails
        break  # Exit the loop if the camera is inaccessible
    

    imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # Convert the image from BGR to RGB format for processing

    results = hands.process(imgRGB)  # Process the image to detect hands using Mediapipe's hand tracking module 
    
    lmList = []  # List to store the coordinates of detected hand landmarks
    # lmList is a list containing the (x, y) coordinates of 21 hand landmarks.
    
    if results.multi_hand_landmarks:  # Check if hand landmarks are detected
        for handlandmark in results.multi_hand_landmarks:  # Iterate through each detected hand
            for lm in handlandmark.landmark:  # Iterate through each landmark of the hand
                h, w, _ = img.shape  # Get the image dimensions (height and width)
                lmList.append([int(lm.x * w), int(lm.y * h)])  # Convert landmark positions to pixel coordinates
            mpDraw.draw_landmarks(img, handlandmark, mpHands.HAND_CONNECTIONS)  # Draw hand landmarks on the image 
    
    if lmList:  # If landmarks are detected
        fingers = []  # List to store the status of each finger (open/closed)

        if lmList[5][0] < lmList[17][0]:  # Check if the hand is facing left
            fingers.append(lmList[lms[0]][0] < lmList[lms[0] - 1][0])  # Thumb open/closed condition
        
        else:  # If the hand is facing right
            fingers.append(lmList[lms[0]][0] > lmList[lms[0] - 1][0])  # Thumb open/closed condition


        for lm in range(1, len(lms)):  # Iterate through the other fingers
            fingers.append(lmList[lms[lm]][1] < lmList[lms[lm] - 2][1])  # Check if fingers are extended
        
     
        
        gesture = detectGesture(fingers)  # Identify the gesture based on finger states
        

        cv2.putText(img, gesture, (20, 50), cv2.FONT_HERSHEY_COMPLEX, 0.9, (0, 255, 0), 2)  # Display the detected gesture




        # Perform actions based on detected gestures
        if gesture == "INDEX":  # If the index finger is raised
            vol = volume.GetMasterVolumeLevel() + 0.4  # Increase the system volume
            vol = min(vol, volMax)  # Ensure volume does not exceed the maximum limit
            volume.SetMasterVolumeLevel(vol, None)  # Set the new volume level
            volBar = remap(vol, volMin, volMax, 400, 150, 1)  # Update the volume bar display

        elif gesture == "THUMB":  # If the thumb is raised
            vol = volume.GetMasterVolumeLevel() - 0.4  # Decrease the system volume
            vol = max(vol, volMin)  # Ensure volume does not go below the minimum limit
            volume.SetMasterVolumeLevel(vol, None)  # Set the new volume level
            volBar = remap(vol, volMin, volMax, 400, 150, 1)  # Update the volume bar display

        elif gesture == "FIVE":  # If all fingers are open
            pag.scroll(-25)  # Scroll down on the screen

        elif gesture == "FIST":  # If a fist is detected (all fingers closed)
            pag.scroll(25)  # Scroll up on the screen

        elif gesture == "VICTORY":  # If the victory finger is extended
            if not netflix_opened:  # Check if Netflix is already opened
                webbrowser.open("https://www.netflix.com")  # Open Netflix in the browser
                netflix_opened = True  # Mark Netflix as opened to prevent multiple launches

        elif gesture == "SWAG":  # If the Swag finger is extended
            if not youtube_opened:  # Check if YouTube is already opened
                webbrowser.open("https://www.youtube.com")  # Open YouTube in the browser
                youtube_opened = True  # Mark YouTube as opened to prevent multiple launches


    cv2.rectangle(img, (50, 150), (85, 400), (0, 255, 0), 3)  # Draw the volume bar outline
    cv2.rectangle(img, (50, int(volBar)), (85, 400), (0, 255, 0), -1)  # Fill the volume level in the bar


    cv2.imshow("Hand Gesture Control", img)  # Display the processed image with overlays
    if cv2.waitKey(1) & 0xFF == ord("q"):  # Check if 'q' key is pressed
        break  # Exit the loop if 'q' is pressed

cap.release()  # Release the camera resource
cv2.destroyAllWindows()  # Close all OpenCV windows
