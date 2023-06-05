import requests

url_api = "http://192.168.0.16:5000/"  # Reemplaza con la URL de tu API

res = requests.get(url_api)

if res.status_code == 200:
    datos = res.json()
    print ("Datos referentes a la temperatura en Donostia:")
    if "temperatura_actual" in datos:
        print("Temperatura actual: {}".format(datos["temperatura_actual"]))
    if "humedad" in datos:
        print("Humedad: {}".format(datos["humedad"]))
    if "hora" in datos:
        print("Hora de recogida de datos: {}".format(datos["hora"]))
else:
    print("Error en la solicitud a la API.")

import time
import signal
import sys
import threading
import RPi.GPIO as GPIO
import adafruit_dht
import board
import neopixel
from max30100 import MAX30100, MODE_HR, MODE_SPO2, INTERRUPT_HR, INTERRUPT_SPO2

class ProgramaPrincipal:
    def __init__(self):
        self.pin_boton = 22
        self.led_pin = 24
        self.sensor_cardiaco = None
        self.sensor_temperatura = None
        self.led_encendido = False
        self.medicion_realizada = False
        self.boton_presionado = False

        # Configurar los pines de la Raspberry Pi
        GPIO.setup(self.pin_boton, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.led_pin, GPIO.OUT)

        # Configurar el LED
        GPIO.output(self.led_pin, GPIO.HIGH)

        # Configurar la tira de LED
        LED_COUNT = 30  # Número de LED en la tira
        LED_PIN = board.D18  # Pin de la Raspberry Pi al que está conectada la tira
        LED_BRIGHTNESS = 0.5  # Brillo de los LED (0.0 a 1.0)
        self.strip = neopixel.NeoPixel(LED_PIN, LED_COUNT, brightness=LED_BRIGHTNESS)

        # Configurar el sensor MAX30100
        self.sensor_cardiaco = MAX30100()
        self.sensor_cardiaco.set_mode(MODE_HR)
        self.sensor_cardiaco.set_spo_config(sample_rate=100, pulse_width=1600)
        self.sensor_cardiaco.enable_interrupt(INTERRUPT_HR)
        self.sensor_cardiaco.enable_interrupt(INTERRUPT_SPO2)

        # Configurar el sensor DHT11
        pin_sensor = 5
        self.sensor_temperatura = adafruit_dht.DHT11(pin_sensor)

    def ejecutar_sensor_cardiaco(self):
        while not self.detener_programa:
            self.sensor_cardiaco.read_sensor()
            hr = self.sensor_cardiaco.red
            hr = min(hr, 180)
            spo2 = self.sensor_cardiaco.ir
            if self.led_encendido and self.boton_presionado:
                print("Ritmo cardíaco:", hr)
                print("Saturación de oxígeno:", spo2)
                self.boton_presionado = False
            time.sleep(0.5)

    def ejecutar_sensor_temperatura(self):
        while not self.detener_programa:
            try:
                temperatura = self.sensor_temperatura.temperature
                humedad = self.sensor_temperatura.humidity
                if self.led_encendido and self.medicion_realizada:
                    print("------------------")
                    print("Temperatura: {:.1f}°C".format(temperatura))
                    print("Humedad: {:.1f}%".format(humedad))
                    print("------------------")
                    self.encender_led_azul()
                    self.medicion_realizada = False
            except RuntimeError as e:
                print("Error al leer el sensor DHT: ", e.args[0])
            time.sleep(0.5)

    def ejecutar_led(self):
        while not self.detener_programa:
            if self.led_encendido:
                if self.medicion_realizada:
                    GPIO.output(self.led_pin, GPIO.LOW)  # Apagar el LED (rojo)
                    self.strip.fill((0, 0, 255))  # Cambiar color a azul
                    self.strip.show()
                    time.sleep(3)
                    self.medicion_realizada = False
                else:
                    GPIO.output(self.led_pin, GPIO.HIGH)  # Encender el LED (rojo)
                    self.strip.fill((255, 0, 0))  # Cambiar color a rojo
                    self.strip.show()
                    time.sleep(0.5)
                    GPIO.output(self.led_pin, GPIO.LOW)  # Apagar el LED (rojo)
                    self.strip.fill((255, 0, 0))  # Cambiar color a rojo
                    self.strip.show()
            else:
                GPIO.output(self.led_pin, GPIO.LOW)  # Apagar el LED (rojo)
                self.strip.fill((255, 0, 0))  # Cambiar color a rojo
                self.strip.show()
            time.sleep(0.1)

    def encender_led_azul(self):
        GPIO.output(self.led_pin, GPIO.LOW)  # Apagar el LED (rojo)
        self.strip.fill((0, 0, 255))  # Cambiar color a azul
        self.strip.show()

    def signal_handler(self, signal, frame):
        self.detener_programa = True

    def pulsador_presionado(self, channel):
        if not self.led_encendido:
            self.led_encendido = True
        self.medicion_realizada = True
        self.boton_presionado = True

    def iniciar_programa(self):
        self.detener_programa = False

        # Configurar el modo de numeración de pines GPIO
        GPIO.setmode(GPIO.BCM)

        # Crear hilos para cada funcionalidad
        hilo_sensor_cardiaco = threading.Thread(target=self.ejecutar_sensor_cardiaco)
        hilo_sensor_temperatura = threading.Thread(target=self.ejecutar_sensor_temperatura)
        hilo_led = threading.Thread(target=self.ejecutar_led)

        # Iniciar los hilos
        hilo_sensor_cardiaco.start()
        hilo_sensor_temperatura.start()
        hilo_led.start()

        # Asignar la función de callback al evento de pulsación del botón
        GPIO.add_event_detect(self.pin_boton, GPIO.FALLING, callback=self.pulsador_presionado, bouncetime=200)

        # Mantener el programa principal en ejecución
        try:
            while not self.detener_programa:
                time.sleep(1)
        except KeyboardInterrupt:
            # Ctrl+C detectado, finalizar el programa
            self.detener_programa = True
            hilo_sensor_cardiaco.join()
            hilo_sensor_temperatura.join()
            hilo_led.join()
            GPIO.output(self.led_pin, GPIO.LOW)  # Apagar el LED
            self.strip.fill((0, 0, 0))  # Apagar la tira LED
            self.strip.show()
            GPIO.cleanup()

# Iniciar el programa principal
programa_principal = ProgramaPrincipal()
programa_principal.iniciar_programa()