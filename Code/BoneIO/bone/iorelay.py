from Adafruit_BBIO import GPIO


class IORelay:

    relayPin = None
    hostname = None
    mqttClient = None

    def __init__(
        self, relayPinParam, hostname, mqttClient
    ):  # we use global mqttClient - be aware
        try:
            self.mqttClient = mqttClient
            self.hostname = hostname
            self.relayPin = relayPinParam

            GPIO.setup(self.relayPin, GPIO.OUT)
            GPIO.output(self.relayPin, GPIO.LOW)

            stateTopic = hostname + "/relay/" + self.relayPin
            self.mqttClient.publish(stateTopic, "off", retain=True)

        except Exception as ex:
            # logging.exception(str(ex))
            print("IORelay.__init__ error:", str(ex))

    def set_state(self, relayPin, command):
        try:
            if command == "on":
                GPIO.output(relayPin, GPIO.HIGH)
            elif command == "off":
                GPIO.output(relayPin, GPIO.LOW)

        except Exception as ex:
            # logging.exception(str(ex))
            print("IORelay.set_state error:", str(ex))

    def on_mqtt_message(self, client, userdata, message):
        try:

            # Odczyt wartosci true/false jako string
            state = message.payload.decode("utf-8")

            stateTopic = str(message.topic).replace("/command", "")
            relayNum = stateTopic.replace(self.hostname + "/relay/", "")
            # print(relayNum)

            self.set_state(relayNum, state)
            self.mqttClient.publish(stateTopic, state, retain=True)

        except Exception as ex:
            # logging.exception(str(ex))
            print("IORelay.on_mqtt_message error:", str(ex))

    def relay_start(self):
        try:

            commandTopic = self.hostname + "/relay/" + self.relayPin + "/command"
            # print(commandTopic)
            self.mqttClient.on_message = self.on_mqtt_message
            self.mqttClient.subscribe(commandTopic)

        except Exception as ex:
            # logging.exception(str(ex))
            print("IORelay.relay_start error:", str(ex))
