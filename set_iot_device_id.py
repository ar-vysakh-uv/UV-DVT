import tkinter as tk
import can
import threading
import time
import struct
from threading import Timer

HOST_COMM_IOT_DEVICE_ID_TEST_MODE=0x066
HOST_COMM_IOT_DEVICE_ID_SET=0x067
HOST_COMM_IOT_DEVICE_ID_SAVE=0x068
HOST_COMM_IOT_DEVICE_ID_DATA=0x569


#can_bus_host = can.interface.Bus(bustype='vector', app_name=None, channel=0, bitrate=500000,data_bitrate=500000, fd=True)
can_bus_host = can.interface.Bus(bustype='ixxat', channel=0, bitrate=500000, fd=True)

def can_host_send_data(buff, len, can_id):
    #for x in range(len):
    #    print(buff[x])
    can_bus_host.send(can.Message(data = buff, arbitration_id = can_id, dlc=len, is_fd = True, is_extended_id=False))


def timer_timeout():
    can_data = [0x11, 0x13, 0x15, 0x17,0x19, 0x1A, 0x1C, 0x1E]
    can_host_send_data(can_data,len(can_data), HOST_COMM_IOT_DEVICE_ID_TEST_MODE)
    #print("message")
    timer = threading.Timer(1, timer_timeout)
    timer.start()

def receive_can_data():
    can_bus_host.set_filters([{"can_id": HOST_COMM_IOT_DEVICE_ID_DATA, "can_mask": 0x7FF, "extended": False}])
    while True:
        #print('receive_can_data')
        message_host = can_bus_host.recv()
        print(message_host)
        if message_host is not None:
            if message_host.arbitration_id == HOST_COMM_IOT_DEVICE_ID_DATA:
                debug_text = 'NULL'
                if ( (message_host.data[0] != 0xfc) and (message_host.data[1] != 0xfc) and (message_host.data[2] != 0xfc) and (message_host.data[3] != 0xfc)):                   
                    print(message_host.dlc)
                    for x in range(message_host.dlc):
                        if x != 0:
                            debug_text += chr(message_host.data[x])
                        else:
                            debug_text = chr(message_host.data[x])
                    print(debug_text)
                label_debug_frame.config(text=debug_text)
        time.sleep(0.1)



def process_input_1():
    # Get the user's inputs from the entry widgets
    device_id_string = set_device_id.get()  # Assuming set_device_id.get() returns a string
    print(device_id_string)

    # Convert each character to a byte and store in a list
    device_id_bytes = [ord(char) for char in device_id_string]

    # Convert the list to a bytes object
    device_id_bytes = bytes(device_id_bytes)

    # Get the size or length of the bytes object
    can_host_send_data(device_id_bytes, len(device_id_bytes), HOST_COMM_IOT_DEVICE_ID_SET)

def process_save_device_id():
    print('process_save_device_id')
    # Get the user's inputs from the entry widgets

    can_data = [0x00]
    can_host_send_data(can_data, 8, HOST_COMM_IOT_DEVICE_ID_SAVE);


# Create the main Tkinter window
window = tk.Tk(className="IOT URL SET" )
window.title("IOT URL SET")

window.configure(bg="#ECECEC")

frame_window = tk.LabelFrame(window, padx=5, pady=5, width=1500, height=1500)
frame_window.pack_propagate(0)
frame_window.pack(padx=10, pady=10)

frame_window_1 = tk.LabelFrame(frame_window, padx=5, pady=5, width=800, height=500)
frame_window_1.pack_propagate(0)
frame_window_1.pack( padx=10, pady=10)
# Displaying the frame1 in row 0 and column 0
frame_window_1.grid(row=0, column=0)

# Create the input labels and entry widgets
label1 = tk.Label(frame_window_1, text="Device ID:", font=("Calibri", 16))
#label1.pack()
label1.grid(row=0, column=0, padx=5, pady=5)
set_device_id = tk.Entry(frame_window_1, font=("Calibri", 16))
set_device_id.grid(row=0, column=1, padx=10, pady=10)
#set_votage.pack()


# Create check button for input 1
#check_var1 = tk.BooleanVar()
#check_button1 = tk.Checkbutton(frame_window_1, text="1st Rectifier ON", variable=check_var1, font=("Calibri", 16))
#check_button1.grid(row=1, column=0)
#check_button1.pack()

# Create check button for input 1
#check_var2 = tk.BooleanVar()
#check_button2 = tk.Checkbutton(frame_window_1, text="2st Rectifier ON", variable=check_var2, font=("Calibri", 16))
#check_button2.grid(row=1, column=1)
#check_button2.pack()

# Create a button to trigger the processing
button = tk.Button(frame_window_1, text="send", command=process_input_1, font=("Calibri", 16))
button.grid(row=2, column=0, padx=20, pady=20)
#button.pack()

debug_frame_window = tk.LabelFrame(frame_window, padx=10, pady=10, width=800, height=500)
debug_frame_window.pack_propagate(0)
debug_frame_window.grid(row=0, column=1)

# Create the input labels and entry widgets
label_debug_frame = tk.Label(debug_frame_window, text="Debug Info:", font=("Calibri", 13))
label_debug_frame.grid(row=0, column=0, padx=100, pady=60)

frame_window_5 = tk.LabelFrame(frame_window, padx=5, pady=5, width=200, height=50,bg="green")
frame_window_5.pack_propagate(0)
frame_window_5.pack(padx=5, pady=5)
frame_window_5.grid(row=3, column=0)

# Create a button to trigger the processing
button = tk.Button(frame_window_5, text="Save device ID", command=process_save_device_id, font=("Calibri", 16))
button.grid(row=6, column=0, padx=10, pady=10)
button.pack()


thread_1 = threading.Thread(target=receive_can_data)

# Start both threads
thread_1.start()

timer = Timer(1, timer_timeout)
timer.start()

# Start the Tkinter event loop
window.mainloop()

thread_1.join()


