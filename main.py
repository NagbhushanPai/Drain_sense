import RPi.GPIO as GPIO
import time
from RPLCD import i2c
import urllib.request
from twilio.rest import Client


# Suppress GPIO warnings
GPIO.setwarnings(False)

# Define GPIO pins for float switch, ultrasonic sensor, and alarm
float_switch_pin = 22
ultrasonic_trigger_pin = 27
ultrasonic_echo_pin = 10
alarm_pin = 20
#For sms
client = vonage.Client(key="f5a73475", secret="D11WVsHtf0gXVRsk")
sms = vonage.Sms(client)
# Set up GPIO mode
GPIO.setmode(GPIO.BCM)

# Set up GPIO pins
GPIO.setup(float_switch_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(ultrasonic_trigger_pin, GPIO.OUT)
GPIO.setup(ultrasonic_echo_pin, GPIO.IN)
GPIO.setup(alarm_pin, GPIO.OUT)

# Initialize the LCD
lcd = i2c.CharLCD('PCF8574', 0x27)

# Function to measure distance using ultrasonic sensor
def measure_distance():
    GPIO.output(ultrasonic_trigger_pin, True)
    time.sleep(0.00001)
    GPIO.output(ultrasonic_trigger_pin, False)

    start_time = time.time()
    stop_time = time.time()

    while GPIO.input(ultrasonic_echo_pin) == 0:
        start_time = time.time()

    while GPIO.input(ultrasonic_echo_pin) == 1:
        stop_time = time.time()

    elapsed_time = stop_time - start_time
    distance = (elapsed_time * 34300) / 2  # Speed of sound is 343 m/s
    return distance

try:
    while True:
        # Check float switch state
        float_switch_state = GPIO.input(float_switch_pin)
        #IOT visualisation
        f = urllib.request.urlopen("https://api.thingspeak.com/update?api_key=CGDAF2LJDUZAEK83&field1=%s" % (float_switch_state))
        print (f.read())
        f.close()
        if float_switch_state == GPIO.HIGH:
            # Display on LCD when float switch is triggered
            lcd.clear()
            lcd.cursor_pos = (0, 0)
            lcd.write_string("Float switch is")
            lcd.cursor_pos = (1, 0)
            lcd.write_string("triggered!")

            # Measure distance using the ultrasonic sensor
            distance = measure_distance()
            #IOT visualisation
            f = urllib.request.urlopen("https://api.thingspeak.com/update?api_key=CGDAF2LJDUZAEK83&field2=%s" % (distance))
            print (f.read())
            f.close()
            lcd.clear()
            lcd.cursor_pos = (0, 0)
            distance_str = "Distance: {:.2f}cm".format(distance)
            lcd.write_string(distance_str)
            message_text=f"Water has crossed the set threshold limit.{distance}cm of mahole is filled with liquid ."

            # Activate alarm if distance is less than a threshold (e.g., water level is too high)
            if distance < 3.5:  # Adjust this threshold as needed
                GPIO.output(alarm_pin, GPIO.HIGH)
                lcd.cursor_pos = (1, 0)
                lcd.write_string("Water level high!")
                message_text="Drainage is about to OVERFLOW.Your Manhole Location is :https://maps.app.goo.gl/p5dB2s8DZEmzSkyd8"
            else:
                GPIO.output(alarm_pin, GPIO.LOW)
            #For SMS
            responseData = sms.send_message(
                        {
                            "from": "Vonage APIs",
                            "to": "918401240904",
                            "text": message_text,
            
                        }
                        )
            if responseData["messages"][0]["status"] == "0":
                    print("Message sent successfully.")
                    print(4)
                    time.sleep(2)    
        else:
            GPIO.output(alarm_pin, GPIO.LOW)
            lcd.clear()
            lcd.cursor_pos = (0, 0)
            lcd.write_string("Float switch not")
            lcd.cursor_pos = (1, 0)
            lcd.write_string("triggered.")

        time.sleep(1)  # Delay for 1 second

except KeyboardInterrupt:
    GPIO.cleanup()
    lcd.clear()