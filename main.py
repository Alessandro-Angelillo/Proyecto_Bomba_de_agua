from machine import Pin, time_pulse_us
import utime

print("Hello, ESP32!")


trig = Pin(5, Pin.OUT)
echo = Pin(18, Pin.IN)
led_bomba = Pin(2, Pin.OUT)

def medir_distancia():
    # Aseguramos que el TRIG esté en bajo
    trig.value(0)
    utime.sleep_us(2)

    # Enviamos un pulso de 10 microsegundos
    trig.value(1)
    utime.sleep_us(10)
    trig.value(0)

    # Medimos el tiempo en microsegundos que el ECHO tarda en volver
    duracion = time_pulse_us(echo, 1, 30000)

    # Convertimos la duración en distancia (cm)
    distancia_cm = (duracion / 2) / 29.155
    return distancia_cm

while True:
    distancia = medir_distancia()
    print("Distancia: {:.2f} cm".format(distancia))
    utime.sleep(1)