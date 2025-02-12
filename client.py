import socket
from time import sleep
import cv2
import numpy as np
from pynput.mouse import Listener as MouseListener
from pynput.keyboard import Listener as KeyboardListener
import threading
from screeninfo import get_monitors

# Global variables
client_width = get_monitors()[0].width
client_height = get_monitors()[0].height
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
    
    if window_bounds is None:
        return  # Window bounds not yet initialized
    
    # Check if the mouse is inside the client window
    wx, wy, w_width, w_height = window_bounds
    if wx <= x <= wx + w_width and wy <= y <= wy + w_height:
        if last_mouse_position is None:
            last_mouse_position = (x - wx, y - wy)  # Adjust for relative position inside the window
        
        # Calculate the distance moved since the last position (relative to the window)
        dx = abs((x - wx) - last_mouse_position[0])
        dy = abs((y - wy) - last_mouse_position[1])
        
        # Only send the command if the mouse has moved more than the threshold
        if dx > MOVE_THRESHOLD or dy > MOVE_THRESHOLD:
            scaled_x, scaled_y = x - wx, y - wy
            scaled_x = round((scaled_x*client_width)/w_width)
            scaled_y = round((scaled_y*client_height)/w_height)
            command = f" MOUSE_MOVE {scaled_x} {scaled_y} {client_width} {client_height}"  # Send relative coordinates
            try:
                client_socket.sendall(command.encode('utf-8'))
                last_mouse_position = (x - wx, y - wy)  # Update the last known position
            except Exception as e:
                print(f"Error sending mouse move: {e}")


def on_click(x, y, button, pressed):
    if window_bounds is None:
        return  # Window bounds not yet initialized
    
    # Check if the mouse is inside the client window
    wx, wy, w_width, w_height = window_bounds
    if wx <= x <= wx + w_width and wy <= y <= wy + w_height:
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
    global running, window_bounds
    try:
        cv2.namedWindow('Remote Desktop',cv2.WINDOW_NORMAL)
        cv2.setMouseCallback('Remote Desktop',lambda *args: None)
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
            
            x, y, width, height = cv2.getWindowImageRect('Remote Desktop')
            window_bounds = (x, y, width, height)
            # Decode the frame
            img_encoded = np.frombuffer(data, dtype=np.uint8)
            frame = cv2.imdecode(img_encoded, cv2.IMREAD_COLOR)
            
            if width>0 and height>0:
                frame = cv2.resize(frame,(width,height))
            
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

    #  global dpi
    # dpi = float(input("Enter DPI: "))
    
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