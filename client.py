import socket
from time import sleep
import cv2
import numpy as np
from pynput.mouse import Listener as MouseListener
from pynput.keyboard import Listener as KeyboardListener
import threading
from screeninfo import get_monitors
import time
import tkinter as tk
from tkinter import filedialog
import os

# Global variables
client_width = get_monitors()[0].width
client_height = get_monitors()[0].height
client_socket = None
running = True
last_mouse_position = None  # To store the last known mouse position
MOVE_THRESHOLD = 5  # Minimum pixel movement before sending a MOUSE_MOVE command

def kill_all_threads():
    global running
    print("Exiting...")
    running = False
    client_socket.close()
    mouse_listener.stop()
    keyboard_listener.stop()
    image_thread.join()
    file_sharing_thread.join()

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

def on_scroll(x, y, dx, dy):
    if window_bounds is None:
        return  # Window bounds not yet initialized
    
    # Check if the mouse is inside the client window
    wx, wy, w_width, w_height = window_bounds
    if wx <= x <= wx + w_width and wy <= y <= wy + w_height:
        if dy > 0:
            command = " MOUSE_SCROLL UP"
        elif dy < 0:
            command = " MOUSE_SCROLL DOWN"
        else:
            return  # No scroll action
        
        try:
            client_socket.sendall(command.encode('utf-8'))
        except Exception as e:
            print(f"Error sending mouse scroll: {e}")

# Function to send keyboard events to the server
def on_press(key):
    global keyboard_enable, ctrl_r_pressed, file_transfer_active, file_sharing_thread, action, keyboard_listener
    try:
        command = f" KEY_PRESS {key.char}"
        if ctrl_r_pressed:
            if file_sharing_thread.is_alive():
                if key.char == "s": 
                    action = "send"
                    return
                if key.char == "r": 
                    action = "receive"
                    return
                if key.char == "f": 
                    action = "close"
                    return
            else:
                if key.char == "f":
                    file_transfer_active = not file_transfer_active
                    file_sharing_thread = threading.Thread(target=handle_file_transfer)
                    file_sharing_thread.start()


    except AttributeError:
        command = f" KEY_DOWN {key.name}"
        if key.name == "ctrl_r":
            ctrl_r_pressed = True
    try:
        client_socket.sendall(command.encode('utf-8'))
        # print(command)
    except Exception as e:
        print(f"Error sending key press: {e}")
    finally:
        try:
            if(key.name == "ctrl_l"):
                kill_all_threads()
        except:
            pass

def on_release(key):
    global ctrl_r_pressed
    try:
        command = f" KEY_UP {key.name}"
        if key.name == "ctrl_r":
            ctrl_r_pressed = False
    except:
        return
    try:
        client_socket.sendall(command.encode('utf-8'))
        if key.name == "alt_l":
            print("Client Keyboard Active!")
            keyboard_listener.stop()
            keyboard_enable = KeyboardListener(on_press=keyboard_enabler)
            keyboard_enable.start()
            return
        # print(command)
    except Exception as e:
        print(f"Error sending key press: {e}")
    finally:
        try:
            if(key.name == "ctrl_l"):
                kill_all_threads()
        except:
            pass

def keyboard_enabler(key):
    global keyboard_listener
    try:
        if key.name == "alt_l":
            print("Host Keyboard Active")
            keyboard_enable.stop() 
            sleep(0.5)
            keyboard_listener = KeyboardListener(on_press=on_press,on_release=on_release,suppress=True)
            keyboard_listener.start()
            return
        if key.name == "ctrl_l":
            kill_all_threads()
    except:
        pass

# Thread to handle receiving images from the host
def image_receiver():
    global running, window_bounds, count
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
            count += 1
            # Exit on 'q' key press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                running = False
                break
                
    except Exception as e:
        # print("Exiting...")
        # print(f"Error in image receiver: {e}")
        pass
    finally:
        cv2.destroyAllWindows()
        running = False

def handle_file_transfer():
    global file_transfer_active, action
    file_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    file_port = 9998
    sleep(1)
    file_socket.connect((host,file_port))
    print("File Transfer Connected!")
    try:
        action = ""
        while file_transfer_active:
            
            if action == "":
                continue

            elif action == "send":
                # Open Windows Explorer file selection dialog on the client
                root = tk.Tk()
                root.withdraw()  # Hide the main tkinter window
                file_path = filedialog.askopenfilename(
                    title="Select a file to send",
                    filetypes=[("All Files", "*.*")]
                )
                root.destroy()  # Destroy the tkinter window after selection
                
                if not file_path:  # If no file is selected
                    print("No file selected. Aborting transfer.")
                    file_transfer_active = not file_transfer_active
                    continue
                
                file_name = os.path.basename(file_path)
                file_size = os.path.getsize(file_path)
                
                # Notify the host that we are sending a file
                file_socket.sendall(b"send")
                
                # Send metadata
                file_socket.sendall(f"FILE_TRANSFER:{file_name}:{file_size}".encode('utf-8'))
                sleep(1)
                # Send the file data in chunks
                with open(file_path, 'rb') as f:
                    bytes_sent = 0
                    while chunk := f.read(4096):  # Read in chunks of 4KB
                        file_socket.sendall(chunk)
                        bytes_sent += len(chunk)
                print(f"File '{file_name}' sent successfully.")
                file_transfer_active = not file_transfer_active
            
            elif action == "receive":
                # Notify the host that we want to receive a file
                file_socket.sendall(b"receive")
                
                # Receive metadata
                print("RECEIVER ON!")
                metadata = file_socket.recv(1024).decode('utf-8')
                if metadata == "FILE_TRANSFER_ABORT":
                    print("Host aborted the file transfer.")
                    continue
                
                if not metadata.startswith("FILE_TRANSFER"):
                    print("Invalid file transfer response from host.")
                    continue
                
                _, file_name, file_size = metadata.split(":")
                file_size = int(file_size)
                print("Receiving File!")
                # Save the file to the current working directory
                save_path = os.path.join(os.getcwd(), file_name)
                with open(save_path, 'wb') as f:
                    bytes_received = 0
                    while bytes_received < file_size:
                        chunk = file_socket.recv(min(4096, file_size - bytes_received))
                        if not chunk:
                            break
                        f.write(chunk)
                        bytes_received += len(chunk)
                print(f"File '{file_name}' received and saved to '{save_path}'.")
                file_transfer_active = not file_transfer_active
            
            elif action == "close":
                file_socket.sendall(b"close")
                file_transfer_active = not file_transfer_active

            else:
                print("Invalid action. Please choose 'send', 'receive' or 'close'.")
            
            action = ""
    
    except Exception as e:
        print(f"Error during file transfer: {e}")
        file_transfer_active = False

    finally:
        file_socket.close()
        print("File Transfer Closed!")


# Main function
def main():
    global client_socket, host, running, mouse_listener, keyboard_listener, keyboard_enable, image_thread, count, file_sharing_thread, file_transfer_active, ctrl_r_pressed

    #  global dpi
    # dpi = float(input("Enter DPI: "))
    
    file_transfer_active = False
    file_sharing_thread = threading.Thread(target=handle_file_transfer)
    # Create a socket object
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Connect to the host
    host = input("Enter the host IP address: ")
    port = 9999
    client_socket.connect((host, port))
    ctrl_r_pressed = False
    count = 0
    # Start the image receiver thread
    image_thread = threading.Thread(target=image_receiver)
    image_thread.start()
    
    # Start listening for mouse and keyboard events
    mouse_listener = MouseListener(on_move=on_move, on_click=on_click,on_scroll=on_scroll)
    keyboard_listener = KeyboardListener(on_press=on_press,on_release=on_release,suppress=True)
    keyboard_enable = KeyboardListener(on_release=keyboard_enabler)
    
    mouse_listener.start()
    keyboard_listener.start()

    try:
        # Keep the main thread alive until the user exits
        while running:
            sleep(1)
            print("FPS: ",count)
            count = 0
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