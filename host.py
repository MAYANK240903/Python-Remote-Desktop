import socket
import cv2
import numpy as np
import pyautogui
import threading
from pynput.mouse import Controller, Button
from pynput.keyboard import Controller as KeyboardController, Key
import time
from time import sleep
from screeninfo import get_monitors
# from mss import mss
# import d3dshot
from turbojpeg import TurboJPEG
import os
import tkinter as tk
from tkinter import filedialog
import bettercam


# global running
host_width = get_monitors()[0].width
host_height = get_monitors()[0].height
running = threading.Event()
running.set()
mouse = Controller()
keyboard = KeyboardController()

def kill_all_threads():
    try:
        global running, camera
        print("Exiting...")
        running.clear()
        client_socket.close()
        camera.stop()
        del camera
        image_sender_thread.join()
        input_receiver_thread.join()
    except:
        pass

def counter(starttime,connection_time):
    global running
    endtime = starttime+(connection_time*60)
    while running.is_set():
        sleep(1)
        curr_time = time.time()
        if curr_time >= endtime:
            print(f"Time Over.\nConnection Lasted for {connection_time} minutes.")
            kill_all_threads()
            return

def getmstime():
    return round(time.time()*1000)

def image_sender(client_socket):
    global running, d
    jpeg = TurboJPEG('C:\\libjpeg-turbo-gcc64\\bin\\libturbojpeg.dll')
    # prev_time = getmstime()
    # prev_frame = jpeg.encode(camera.get_latest_frame())
    # monitor = mss().monitors[1]
    while running.is_set():
        try:
            # curr_time = getmstime()
            # print(curr_time)
            # diff = curr_time-prev_time
            # b = 0.0
            # a = 0.0
            # if diff>0:
            
            # screenshot = pyautogui.screenshot()
            # screenshot = mss().grab(monitor)
            # b = getmstime()
            frame = camera.get_latest_frame()
            # time_elapsed = (curr_time-prev_time)//1000
            # if frame is None and time_elapsed>=1:
            #     client_socket.sendall(len(prev_frame).to_bytes(4, byteorder='big'))
            #     client_socket.sendall(prev_frame)
            #     prev_time = curr_time
            # elif frame is None:
            #     client_socket.sendall(len(prev_frame).to_bytes(4, byteorder='big'))
            #     client_socket.sendall(prev_frame)
            #     continue
            # screenshot = d.screenshot()
            # frame = np.array(screenshot)
            # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Encode the frame as JPEG
            # _, img_encoded = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY),75])
            data = jpeg.encode(frame)
            # data = img_encoded
            # print(getmstime()-b)
            
            size = len(data)
            client_socket.sendall(size.to_bytes(4, byteorder='big'))
            
            client_socket.sendall(data)
            # prev_frame = data
        except Exception as e:
            print(e)
            kill_all_threads()
            running.clear()
        
def input_receiver(client_socket):
    global running, ctrl_r_pressed, file_sharing_thread, file_transfer_active
    ctrl_r_pressed = False
    while running.is_set():
        try:
            command = client_socket.recv(1024).decode('utf-8')
        except:
            pass
        # print(command)
        if command.startswith(" MOUSE_MOVE"):
            x, y = map(int, command.split(" ")[2:4])
            client_width, client_height = map(int, command.split(" ")[4:6])
            # x = round(x*dpi)
            # y = round(y*dpi)
            x = round((x*host_width)/client_width)
            y = round((y*host_height)/client_height)
            mouse.position = (x, y)
            # print(command+" scaled coordinates: "+str(x)+" "+str(y))
        elif command.startswith(" MOUSE_CLICK"):
            button = command.split()[1]
            if button == "LEFT":
                mouse.click(Button.left)
            elif button == "RIGHT":
                mouse.click(Button.right)
        elif command.startswith(" KEY_PRESS"):
            key = command.split()[1]
            if key == "None":
                continue
            if key == "f" and ctrl_r_pressed:
                file_transfer_active = not file_transfer_active
                if file_sharing_thread.is_alive():
                    file_sharing_thread.join()
                    print("File Sharing Stopped!")
                else:
                    file_sharing_thread = threading.Thread(target=handle_file_transfer)
                    file_sharing_thread.start()
                continue
            try:
                key_attrib = getattr(Key,key)
            except AttributeError:
                key_attrib = key
            keyboard.tap(key_attrib)
        elif command.startswith(" KEY_DOWN"):
            key = command.split()[1]
            if key=="ctrl_l":
                running.clear()
                break
            if key=="ctrl_r":
                ctrl_r_pressed = True
            try:
                key_attrib = getattr(Key,key)
            except AttributeError:
                key_attrib = key
            keyboard.press(key_attrib)
            # if key == "ctrl_r":
            #     keyboard.press(Key.ctrl_r)
            # elif key == "shift_l":
            #     keyboard.press(Key.shift_l)
            # elif key == "shift_r":
            #     keyboard.press(Key.shift_r)
            # elif key == "space":
            #     keyboard.press
        elif command.startswith(" KEY_UP"):
            key = command.split()[1]
            if key=="ctrl_l":
                running.clear()
                break
            if key=="ctrl_r":
                ctrl_r_pressed = False
            try:
                key_attrib = getattr(Key,key)
            except AttributeError:
                key_attrib = key
            keyboard.release(key_attrib)
        elif command.startswith(" MOUSE_SCROLL"):
            direction = command.split()[1]
            if direction == "UP":
                mouse.scroll(0, 1)  # Scroll up
            elif direction == "DOWN":
                mouse.scroll(0, -1)  # Scroll down

def handle_file_transfer():
    global file_transfer_active
    file_server_socket = socket.socket(socket.AF_INET6,socket.SOCK_STREAM)
    file_server_socket.setsockopt(socket.IPPROTO_IPV6,socket.IPV6_V6ONLY,0)
    file_port = 9998
    file_server_socket.bind((host,file_port))
    file_server_socket.listen(5)
    (file_socket,address) = file_server_socket.accept()
    print("File Transfer Connected!")
    try:
        while file_transfer_active:
            binary_action = file_socket.recv(1024)
            action = binary_action.decode('utf-8').strip().lower()
            if action == "receive":
                print("Client requested to receive a file.")
                
                root = tk.Tk()
                root.withdraw()
                file_path = filedialog.askopenfilename(
                    title="Select a file to send",
                    filetypes=[("All Files", "*.*")]
                )
                root.destroy()
                
                if not file_path:
                    print("No file selected. Aborting transfer.")
                    file_socket.sendall(b"FILE_TRANSFER_ABORT")
                    file_transfer_active = not file_transfer_active
                    continue
                
                file_name = os.path.basename(file_path)
                file_size = os.path.getsize(file_path)
                
                # Send metadata
                file_socket.sendall(f"FILE_TRANSFER:{file_name}:{file_size}".encode('utf-8'))
                sleep(1)
                # Send the file data in chunks
                with open(file_path, 'rb') as f:
                    bytes_sent = 0
                    while chunk := f.read(4096):
                        file_socket.sendall(chunk)
                        bytes_sent += len(chunk)
                print(f"File '{file_name}' sent successfully.")
                file_transfer_active = not file_transfer_active
            
            elif action == "send":
                print("Client requested to send a file.")
                
                # Receive metadata
                print("RECEIVER ON!")
                metadata = file_socket.recv(1024).decode('utf-8')
                # metadata = b"\n"
                # while b"\n" not in metadata:
                #     chunk = file_socket.recv(1024)
                #     if not chunk:
                #         break
                # metadata = metadata.decode('utf-8').strip()
                # print(metadata)
                if not metadata.startswith("FILE_TRANSFER"):
                    print("Invalid file transfer request.")
                    file_transfer_active = not file_transfer_active
                    continue
                
                _, file_name, file_size = metadata.split(":")
                file_size = int(file_size)
                # print(metadata)
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
                file_transfer_active = not file_transfer_active

            else:
                print(binary_action)
                print("Invalid action received from client.")
    
    except Exception as e:
        print(f"Error during file transfer: {e}")
        file_transfer_active = False
    
    finally:
        file_server_socket.close()
        file_socket.close()
        print("File Transfer Closed!")

def add_user(newusr,newpasswd,newtime):
    f = open(f"{os.path.dirname(__file__)}\\cred_file.txt",'a')
    f.write(f"\n{newusr}:{newpasswd}:{newtime}")
    print("Successfully Added New User!")

def main():
    global client_socket, host, image_sender_thread, input_receiver_thread, d, file_transfer_active, file_sharing_thread, timed, camera
    global running

    # global dpi
    # dpi = float(input("Enter DPI: "))

    host = '::'
    port = 9999

    #host authentication
    # print(bettercam.device_info())
    # print(bettercam.output_info())
    print("Checking Authentication...")
    authentication_socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    authentication_socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
    authentication_socket.bind((host,port))
    authentication_socket.settimeout(30.0)
    authentication_socket.listen(5)
    (auth_accept,address) = authentication_socket.accept()
    cred = auth_accept.recv(1024).decode('utf-8')
    cred.strip()
    # print(cred)
    try:
        cred_file = open(f"{os.path.dirname(__file__)}\\cred_file.txt",'r')
    except FileNotFoundError:
        print("cred_file.txt does not exist in script location.\nPlease make one with format {username}:{password}\nExiting...")
        return
    allowed = True if cred in cred_file.read() else False
    if not allowed:
        print("Invalid Credentials.\nUnauthorized Access.")
        auth_accept.sendall(b"unauthorized")
        auth_accept.close()
        authentication_socket.close()
        return
    else:
        cred_file.seek(0)
        lines = cred_file.readlines()
        cred_line = [line for line in lines if line.startswith(cred)][0].split(":")
        if len(cred_line) == 3:
            connection_time = int(cred_line[2])
            # int typecasting here?
            timed = True
            auth_accept.sendall(f"authorized:{connection_time}".encode('utf-8'))
            print(f"Timed Connection Established for {connection_time} minutes.")
            starttime = time.time()
            counter_thread = threading.Thread(target=lambda: counter(starttime,connection_time))
            counter_thread.start()
        else:
            auth_accept.sendall(b"authorized")
        print("Authorized Client Connected!")
        auth_accept.close()
        authentication_socket.close()

    file_transfer_active = False
    server_socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.IPPROTO_IPV6,socket.IPV6_V6ONLY,0)
    server_socket.bind((host, port))
    server_socket.settimeout(30.0)
    
    server_socket.listen(5)
    print(f"Listening on {host}:{port}")
    
    # d = d3dshot.create(capture_output="numpy")

    (client_socket, address) = server_socket.accept()
    print(f"Connection from {address}")
    camera = bettercam.create(output_color="BGR")
    camera.start(target_fps=144)
    running.set()
    try:
        image_sender_thread = threading.Thread(target=lambda: image_sender(client_socket=client_socket))
        image_sender_thread.start()
        input_receiver_thread = threading.Thread(target=lambda: input_receiver(client_socket=client_socket))
        input_receiver_thread.start()
        file_sharing_thread = threading.Thread(target=handle_file_transfer)
        while running.is_set():
            sleep(2)
                
    except Exception as e:
        print(f"Error: {e}")
        client_socket.close()
    finally:
        running.clear()
        client_socket.close()
        image_sender_thread.join()
        input_receiver_thread.join()
        print("Exiting...")


if __name__ == "__main__":
    main()