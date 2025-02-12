import socket
from time import sleep
import cv2
import numpy as np
from pynput.mouse import Listener as MouseListener
from pynput.keyboard import Listener as KeyboardListener
import threading

# Global variables
client_socket = None
running = True
last_mouse_position = None  # To store the last known mouse position
MOVE_THRESHOLD = 5  # Minimum pixel movement before sending a MOUSE_MOVE command

def kill_all_threads():
    running = False
    client_socket.close()
    mouse_listener.stop()
    keyboard_listener.stop()
    image_thread.join()

# Function to send mouse events to the server
def on_move(x, y):
    global last_mouse_position
    
    if last_mouse_position is None:
        last_mouse_position = (x, y)
    
    # Calculate the distance moved since the last position
    dx = abs(x - last_mouse_position[0])
    dy = abs(y - last_mouse_position[1])
    
    # Only send the command if the mouse has moved more than the threshold
    if dx > MOVE_THRESHOLD or dy > MOVE_THRESHOLD:
        command = f" MOUSE_MOVE {x} {y}"
        try:
            client_socket.sendall(command.encode('utf-8'))
            # print(command)
            last_mouse_position = (x, y)  # Update the last known position
        except Exception as e:
            print(f"Error sending mouse move: {e}")

def on_click(x, y, button, pressed):
    if pressed:
        if button.name == 'left':
            command = " MOUSE_CLICK LEFT"
        elif button.name == 'right':
            command = " MOUSE_CLICK RIGHT"
        try:
            client_socket.sendall(command.encode('utf-8'))
        except Exception as e:
            print(f"Error sending mouse click: {e}")

# Function to send keyboard events to the server
def on_press(key):
    try:
        command = f" KEY_PRESS {key.char}"
    except AttributeError:
        command = f" KEY_PRESS {key.name}"
    try:
        client_socket.sendall(command.encode('utf-8'))
    except Exception as e:
        print(f"Error sending key press: {e}")
    finally:
        try:
            if(key.name == "ctrl_l"):
                kill_all_threads()
        except:
            pass


# Thread to handle receiving images from the host
def image_receiver():
    global running
    try:
        while running:
            # Receive the size of the incoming frame
            size_data = client_socket.recv(4)
            if not size_data:
                break
            size = int.from_bytes(size_data, byteorder='big')
            
            # Receive the frame data
            data = b""
            while len(data) < size:
                packet = client_socket.recv(size - len(data))
                if not packet:
                    break
                data += packet
            
            # Decode the frame
            img_encoded = np.frombuffer(data, dtype=np.uint8)
            frame = cv2.imdecode(img_encoded, cv2.IMREAD_COLOR)
            
            # Display the frame
            cv2.imshow('Remote Desktop', frame)
            
            # Exit on 'q' key press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                running = False
                break
                
    except Exception as e:
        print(f"Error in image receiver: {e}")
    finally:
        cv2.destroyAllWindows()
        running = False

# Main function
def main():
    global client_socket, running, mouse_listener, keyboard_listener, image_thread
    
    # Create a socket object
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Connect to the host
    host = input("Enter the host IP address: ")
    port = 9999
    client_socket.connect((host, port))
    
    # Start the image receiver thread
    image_thread = threading.Thread(target=image_receiver)
    image_thread.start()
    
    # Start listening for mouse and keyboard events
    mouse_listener = MouseListener(on_move=on_move, on_click=on_click)
    keyboard_listener = KeyboardListener(on_press=on_press)
    
    mouse_listener.start()
    keyboard_listener.start()
    
    try:
        # Keep the main thread alive until the user exits
        while running:
            sleep(2)
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        running = False
        client_socket.close()
        mouse_listener.stop()
        keyboard_listener.stop()
        image_thread.join()

if __name__ == "__main__":
    main()