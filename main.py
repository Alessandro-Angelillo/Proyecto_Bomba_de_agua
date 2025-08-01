from machine import Pin, time_pulse_us
import utime

print("Hello, ESP32!")

##########################################
#         Definicion de valores          #
##########################################

Largo_tanque = 100    #Medida de la altura del tanque en cm
limite_superior = 10*Largo_tanque/100  # En el cual la bomba deja de funcionar (desde que baja un 10%)
limite_inferior = 60*Largo_tanque/100  # En el cual la bomba empieza a funcionar (desde que baja un 60%)
estado_de_la_bomba = False

##########################################
#        Definicion de funciones         #
##########################################
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

def controlar_bomba(distancia):  # Funcion para prender/apagar bomba dependiendo del nivel del tanque
    global estado_de_la_bomba
    if distancia > limite_inferior:
        estado_de_la_bomba = True
    elif distancia < limite_superior:
        estado_de_la_bomba = False

def imprimir_estado():  # Funcion para ver por la terminal si la bomba esta prendida o apagada
    global estado_de_la_bomba
    if estado_de_la_bomba:
        print("La bomba esta prendida")
    else:
        print("La bomba esta apagada")

##########################################
#    Comienzo del programa principal     #
##########################################

while True:
    distancia_sensor = medir_distancia()
    print(f"El tanque esta al {100-(distancia_sensor * 100 / Largo_tanque)}%")
    controlar_bomba(distancia_sensor)
    imprimir_estado()
    utime.sleep(0.5)
    print("\033[2J\033[H")
