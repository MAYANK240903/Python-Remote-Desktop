import socket
import cv2
import numpy as np
import pyautogui
import threading
from pynput.mouse import Controller, Button
from pynput.keyboard import Controller as KeyboardController, Key
import time
from time import sleep

# Initialize mouse and keyboard controllers
# global running
running = threading.Event()
running.set()
mouse = Controller()
keyboard = KeyboardController()

def kill_all_threads():
    try:
        running.clear()
        client_socket.close()
        image_sender_thread.join()
        input_receiver_thread.join()
    except:
        pass

def getmstime():
    return round(time.time()*1000)

def image_sender(client_socket):
    global running
    prev_time = getmstime()
    while running.is_set():
        try:
            curr_time = getmstime()
            # print(curr_time)
            diff = curr_time-prev_time
            prev_time = curr_time
            if diff>16:
                screenshot = pyautogui.screenshot()
                frame = np.array(screenshot)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Encode the frame as JPEG
                _, img_encoded = cv2.imencode('.jpg', frame)
                data = img_encoded.tobytes()
                
                # Send the size of the data first
                size = len(data)
                client_socket.sendall(size.to_bytes(4, byteorder='big'))
                
                # Send the actual data
                client_socket.sendall(data)
        except:
            running.clear()
        
def input_receiver(client_socket):
    global running
    while running.is_set():
        command = client_socket.recv(1024).decode('utf-8')
        # print(command)
        if command.startswith(" MOUSE_MOVE"):
            x, y = map(int, command.split(" ")[2:4])
            mouse.position = (x, y)
        elif command.startswith(" MOUSE_CLICK"):
            button = command.split()[1]
            if button == "LEFT":
                mouse.click(Button.left)
            elif button == "RIGHT":
                mouse.click(Button.right)
        elif command.startswith(" KEY_PRESS"):
            key = command.split()[1]
            if(key=="ctrl_l"):
                running.clear()
                break
            keyboard.press(key)
            keyboard.release(key)



def main():
    # Create a socket object
    global client_socket, image_sender_thread, input_receiver_thread
    global running
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Bind the socket to a public host, and a well-known port
    host = '0.0.0.0'  # Listen on all available interfaces
    port = 9999
    server_socket.bind((host, port))
    
    # Become a server socket
    server_socket.listen(5)
    print(f"Listening on {host}:{port}")
    
    # Accept connections from outside
    (client_socket, address) = server_socket.accept()
    print(f"Connection from {address}")
    running.set()
    try:
        image_sender_thread = threading.Thread(target=lambda: image_sender(client_socket=client_socket))
        image_sender_thread.start()
        input_receiver_thread = threading.Thread(target=lambda: input_receiver(client_socket=client_socket))
        input_receiver_thread.start()
        while running.is_set():
            sleep(2)
            # Capture the screen
            # Receive input commands from the client
                
    except Exception as e:
        print(f"Error: {e}")
        client_socket.close()
    finally:
        running.clear()
        client_socket.close()
        image_sender_thread.join()
        input_receiver_thread.join()


if __name__ == "__main__":
    main()