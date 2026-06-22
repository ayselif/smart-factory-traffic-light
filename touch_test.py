from time import sleep
from gpiozero import DigitalInputDevice

touch = DigitalInputDevice(
    18,
    pull_up=False
)

print("Touch test started.")
print("Metal uca dokun. Durdurmak için Control + C.")

try:
    while True:
        print(f"Touch value: {touch.value}")
        sleep(0.2)

except KeyboardInterrupt:
    print("\nTouch test stopped.")
