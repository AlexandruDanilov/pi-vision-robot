from machine import Pin, PWM, UART
import utime

MID = 1500000
MIN = 1000000
MAX = 2000000

SERVO_MIN_ANGLE_X = -120
SERVO_MAX_ANGLE_X = 120
SERVO_MIN_ANGLE_Y = -45  # Adjusted limit for Y-axis servo
SERVO_MAX_ANGLE_Y = 90   # Adjusted limit for Y-axis servo

SERVO_MIN_PULSE_WIDTH = 1000000
SERVO_MAX_PULSE_WIDTH = 2000000

# Function to convert angle to pulse width
def angle_to_pulse_width(angle):
    return SERVO_MIN_PULSE_WIDTH + int((angle - SERVO_MIN_ANGLE_X) / (SERVO_MAX_ANGLE_X - SERVO_MIN_ANGLE_X) * (SERVO_MAX_PULSE_WIDTH - SERVO_MIN_PULSE_WIDTH))

# Setup servo pins
pin_x = 26
pin_y = 18
pwm_x = PWM(Pin(pin_x))
pwm_y = PWM(Pin(pin_y))

pwm_x.freq(50)
pwm_y.freq(50)
pwm_x.duty_ns(MID)
pwm_y.duty_ns(MID)

# Function to move servo to a specified angle
def move_to_angle(servo, angle):
    if servo == 'x':
        pwm = pwm_x
        min_angle = SERVO_MIN_ANGLE_X
        max_angle = SERVO_MAX_ANGLE_X
    elif servo == 'y':
        pwm = pwm_y
        min_angle = SERVO_MIN_ANGLE_Y
        max_angle = SERVO_MAX_ANGLE_Y
    else:
        print("Invalid servo selection")
        return
    
    angle = min(max(angle, min_angle), max_angle)  # Clamp angle within limits
    pulse_width = angle_to_pulse_width(angle)
    pwm.duty_ns(pulse_width)

# Move both motors to specified target angles
def move_to_target_angles(target_angle_x, target_angle_y):
    move_to_angle('x', target_angle_x)
    move_to_angle('y', target_angle_y)

# Function to handle UART input
def handle_uart_input():
    global received_data
    received_data = ""  # Initialize received_data if not defined
    while uart.any():
        received_data += uart.read().decode().strip()  # Accumulate received data
        if '\n' in received_data:  # Check if a complete command is received
            data, _, received_data = received_data.partition('\n')  # Split at newline
            print("Received:", data)  # Print received data
            if data == "u":
                return 0, 3  # Increase Y angle
            elif data == "d":
                return 0, -3  # Decrease Y angle
            elif data == "l":
                return -5, 0  # Decrease X angle
            elif data == "r":
                return 5, 0  # Increase X angle
            else:
                print("Invalid command:", data)
    return 0, 0  # Return default values if no valid command is received


# Configure UART communication
uart = UART(0, baudrate=115200)  # UART 0 is the default UART on Raspberry Pi Pico

target_angle_x = 0
target_angle_y = 0

# Main loop
if __name__ == "__main__":
    while True:
        delta_angle_x, delta_angle_y = handle_uart_input()
        target_angle_x = max(min(SERVO_MAX_ANGLE_X, target_angle_x + delta_angle_x), SERVO_MIN_ANGLE_X)
        target_angle_y = max(min(SERVO_MAX_ANGLE_Y, target_angle_y + delta_angle_y), SERVO_MIN_ANGLE_Y)
        move_to_target_angles(target_angle_x, target_angle_y)
