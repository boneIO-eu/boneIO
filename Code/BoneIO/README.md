Example usage:
GPIOZERO_PIN_FACTORY=pigpio PIGPIO_ADDR=10.0.0.1 boneio run -d --mqttserver mqtt.server --username mqtt --password mqtt -r 17 -i 3,5 --input_prefix_pin "" --relay_prefix_pin "" -rp '{"3":"17"}'

Which means script will connect to remote pigpio, connect to mqtt server and:
- use pin 17 as relay pin
- use pins 3,4,5 as input pins
- no prefixes (so it is rpi)
- it will map single click on PIN 3 to toggle PIN 17
