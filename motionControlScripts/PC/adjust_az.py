import socket
import msvcrt  # Detects key input without pressing enter
import time

# Pi server comm settings
HOST = '192.168.27.194'  # Raspberry Pi's IP address
PORT = 12345  # The port on which the server is listening

# Motion parameters
az_sweep_step = 0.1  # Initial step size
step_increment = 0.01  # Step change amount
min_step = 0.0  # Minimum step size
max_step = 10.0  # Maximum step size
send_delay = 0.1  # Delay between sending commands

# Tracking movement
total_movement = 0.0
current_key = None  # Track the currently pressed key


# Function to send motion requests to the Raspberry Pi server
def send_command(command):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(command.encode())


print("Controls:")
print("  - Hold 'd' to move right.")
print("  - Hold 'a' to move left.")
print("  - Press 'w' to increase step size.")
print("  - Press 's' to decrease step size.")
print("  - Press 'q' to quit.")

while True:
    if msvcrt.kbhit():  # Check if a key was pressed
        key = msvcrt.getch().decode('utf-8').lower()

        if key == 'q':  # Quit the program
            print("Exiting...")
            break
        elif key == 'w':  # Increase step size
            if az_sweep_step < max_step:
                az_sweep_step = min(az_sweep_step + step_increment, max_step)
                print(f"Step size increased to: {az_sweep_step:.2f}")
        elif key == 's':  # Decrease step size
            if az_sweep_step > min_step:
                az_sweep_step = max(az_sweep_step - step_increment, min_step)
                print(f"Step size decreased to: {az_sweep_step:.2f}")
        elif key in ('d', 'a'):  # Start movement tracking
            if key != current_key:  # If a new key is pressed, reset total movement
                total_movement = 0.0
                current_key = key

    # Movement loop (runs while a key is being held)
    if current_key:
        movement = az_sweep_step if current_key == 'd' else -az_sweep_step
        send_command(f'move_az_DM542T.py:{movement}')
        total_movement += movement  # Accumulate movement in the correct direction
        print(f"Moved {total_movement:.2f} degrees")
        time.sleep(send_delay)

    # If no key is being held, reset movement tracking
    if not msvcrt.kbhit():
        total_movement = 0.0
        current_key = None
