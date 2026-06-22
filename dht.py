import time

import adafruit_dht
import board

sensor = adafruit_dht.DHT11(
    board.D4,
    use_pulseio=False,
)

try:
    while True:
        try:
            temperature = sensor.temperature
            humidity = sensor.humidity

            print(
                f"Temperature: {temperature:.1f} °C | "
                f"Humidity: {humidity:.1f} %"
            )

        except RuntimeError as error:
            print(f"Reading error: {error}")

        time.sleep(3)

except KeyboardInterrupt:
    print("\nSensor test stopped.")

finally:
    sensor.exit()
