from machine import Pin, time_pulse_us # type: ignore
import utime # type: ignore
import socket
import network # type: ignore
import _thread


print("Hello, ESP32!")

##########################################
#         Definicion de valores          #
##########################################

Largo_tanque = 100    #Medida de la altura del tanque en cm
limite_superior = 10*Largo_tanque/100  # En el cual la bomba deja de funcionar (desde que baja un 10%)
limite_inferior = 60*Largo_tanque/100  # En el cual la bomba empieza a funcionar (desde que baja un 60%)
estado_de_la_bomba = False
ssid = 'OverSys-2.4GHz'
password = '010101ACAC'
modo_manual = False   # arranca en automatico
bomba_encendida = False  # arranca apagado 

##########################################
#        Definicion de funciones         #
##########################################
trig = Pin(27, Pin.OUT)
echo = Pin(26, Pin.IN)
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

def controlar_automatico(dist):  # Funcion para prender/apagar bomba dependiendo del nivel del tanque
    global estado_de_la_bomba
    if dist > limite_inferior:
        estado_de_la_bomba = True
    elif dist < limite_superior:
        estado_de_la_bomba = False

def controlar_manual(on_off):  # Funcion para prender/apagar bomba con un boton
    global estado_de_la_bomba
    if on_off:
        estado_de_la_bomba = True
    else:
        estado_de_la_bomba = False


def medir_distancia_filtrada(n=5):  #Toma 5 mediciones, descarta las mas extremas (de arriba y abajo) y hace un promedio de las 3 restantes. Para una medicion mas confiable
    mediciones = []
    for _ in range(n):
        d = medir_distancia()
        mediciones.append(d)
        utime.sleep_ms(50)
    mediciones.sort()
    mediciones_filtradas = mediciones[1:-1]
    promedio = sum(mediciones_filtradas)/len(mediciones_filtradas)
    return promedio

def eleccion_de_modo(distancia, manual, boton_on_off):  # sirve para decidir segun que prender o apagar la bomba
    if manual:
        controlar_manual(boton_on_off)
    else:
        controlar_automatico(distancia)


def conectar_modo_STA(red_ssdi, red_password):  #Conectamos la placa al wifi
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    sta.connect(red_ssdi, red_password)
    print('Conectando a la red wifi...')
    tiempo_conexion = utime.time()
    while not sta.isconnected():
        print('.', end="")
        utime.sleep(0.1)
        if utime.time() - tiempo_conexion > 15:
            break
    if sta.isconnected():
        config = sta.ifconfig()
        print()
        print('Conectado')
        print("-"*40)
        print('Configuración de red:')
        print(f"IP: {config[0]}")
        print(f"Mascara de red: {config[1]}")
        print(f"Gateway: {config[2]}")
        print(f"DNS: {config[3]}")
        print("-"*40)
        return sta
    else:
        print("No se pudo conectar")
        return None

def generar_pagina(nivel_agua_pct, modo_manual, estado_de_la_bomba):
    modo_texto = "Manual" if modo_manual else "Automático"
    bomba_texto = "Encendida" if estado_de_la_bomba else "Apagada"
    disabled_attr = "" if modo_manual else "disabled"

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Control del Tanque</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="refresh" content="10">
    <style>
        body {{
            font-family: Arial, sans-serif;
            background-color: #f2f2f2;
            text-align: center;
            padding: 1rem;
        }}
        h1 {{
            color: #333;
        }}
        .card {{
            background: white;
            padding: 1rem 1.5rem;
            border-radius: 10px;
            display: inline-block;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            margin-bottom: 1rem;
        }}
        .estado {{
            margin: 0.5rem 0;
            font-size: 1rem;
        }}
        button {{
            padding: 10px 20px;
            margin: 5px;
            font-size: 1rem;
            border: none;
            border-radius: 8px;
            cursor: pointer;
        }}
        .primary {{ background-color: #4CAF50; color: white; }}
        .danger {{ background-color: #f44336; color: white; }}
        .disabled {{
            background: #ccc;
            cursor: not-allowed;
        }}
    </style>
</head>
<body>
    <h1>Panel de Control del Tanque</h1>
    <div class="card">
        <p class="estado"><strong>Nivel de agua:</strong> {nivel_agua_pct}%</p>
        <p class="estado"><strong>Modo:</strong> {modo_texto}</p>
        <p class="estado"><strong>Bomba:</strong> {bomba_texto}</p>
    </div>

    <div class="card">
        <form action="/" method="get" style="display:inline;">
            <button class="primary" name="modo" value="manual" type="submit">Cambiar a Manual</button>
        </form>
        <form action="/" method="get" style="display:inline;">
            <button class="primary" name="modo" value="auto" type="submit">Cambiar a Automático</button>
        </form>
    </div>

    <div class="card">
        <form action="/" method="get" style="display:inline;">
            <button class="primary" name="bomba" value="on" type="submit" {disabled_attr}>Encender bomba</button>
        </form>
        <form action="/" method="get" style="display:inline;">
            <button class="danger" name="bomba" value="off" type="submit" {disabled_attr}>Apagar bomba</button>
        </form>
    </div>
</body>
</html>
"""
    return html



def servidor_web(wlan):
    global modo_manual, bomba_encendida, estado_de_la_bomba
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(5)
    print(f'Servidor activo en: http://{wlan.ifconfig()[0]}')

    while True:
        try:
            cliente, addr = s.accept()
            print('Se conectó un usuario desde la IP %s' % str(addr))
            request_raw = cliente.recv(1024)
            request = request_raw.decode('utf-8', 'ignore')
            print("Request:", request.splitlines()[0])

            # Extraer path de la primera línea: "GET /?modo=manual&bomba=on HTTP/1.1"
            request_line = request.split('\r\n')[0]
            parts = request_line.split(' ')
            path = parts[1] if len(parts) > 1 else '/'

            # Procesar modo
            if 'modo=manual' in path:
                modo_manual = True
            elif 'modo=auto' in path:
                modo_manual = False

            # Procesar bomba (solo si está en modo manual)
            if modo_manual:
                if 'bomba=on' in path:
                    bomba_encendida = True
                elif 'bomba=off' in path:
                    bomba_encendida = False

            # Actualizar estado real de la bomba según modo y override
            distancia_sensor = medir_distancia_filtrada()
            eleccion_de_modo(distancia_sensor, modo_manual, bomba_encendida)  # esto actualiza estado_de_la_bomba

            # Calcular porcentaje de agua para mostrar
            nivel_agua_pct = round(100 - (distancia_sensor * 100 / Largo_tanque))

            # Generar HTML con el estado actual
            html = generar_pagina(nivel_agua_pct, modo_manual, estado_de_la_bomba)

            respuesta = "HTTP/1.1 200 OK\r\n"
            respuesta += "Content-Type: text/html; charset=UTF-8\r\n"
            respuesta += "Content-Length: {}\r\n".format(len(html))
            respuesta += "Connection: close\r\n"
            respuesta += "\r\n"
            respuesta += html

            cliente.sendall(respuesta)
            utime.sleep(0.2)
            cliente.close()

        except KeyboardInterrupt:
            print('\nDeteniendo servidor...')
            break
        except OSError as e:
            print('OSError:', e)
            if 'cliente' in locals():
                cliente.close()
        except Exception as e:
            print('Error:', e)
            if 'cliente' in locals():
                cliente.close()
    s.close()



##########################################
#    Comienzo del programa principal     #
##########################################

WLAN = conectar_modo_STA(ssid, password)
if WLAN:
    _thread.start_new_thread(servidor_web, (WLAN,))


while True:
    distancia_sensor = medir_distancia_filtrada()
    nivel_agua = round(100-(distancia_sensor * 100 / Largo_tanque))
    print(f"El tanque esta al {nivel_agua}%")
    
    eleccion_de_modo(distancia_sensor, modo_manual, bomba_encendida)
    led_bomba.value(1 if estado_de_la_bomba else 0)  # Led encendido: bomba prendida, led apagado: bomba apagada
    utime.sleep(0.5)
