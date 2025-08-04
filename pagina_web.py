import utime # type: ignore
import network # type: ignore
import socket

ssid = 'OverSys-2.4GHz'
password = '010101ACAC'
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

def generar_pagina(modo_manual, bomba_encendida):
    modo_texto = "Manual" if modo_manual else "Automático"
    bomba_texto = "Encendida" if bomba_encendida else "Apagada"
    
    html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Control de Bomba - ESP32</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="refresh" content="10">
    <style>
        body {{ font-family: Arial; text-align: center; background-color: #f2f2f2; }}
        h1 {{ color: #333; }}
        .estado {{ font-size: 1.2em; margin: 10px 0; }}
        button {{
            padding: 10px 20px;
            font-size: 1em;
            margin: 5px;
            border: none;
            border-radius: 8px;
            background-color: #4CAF50;
            color: white;
        }}
        .off {{ background-color: #f44336; }}
    </style>
</head>
<body>
    <h1>Panel de Control</h1>
    <p class="estado"><strong>Modo actual:</strong> {}</p>
    <p class="estado"><strong>Estado bomba:</strong> {}</p>
    
    <form action="/" method="get">
        <button name="modo" value="manual">Modo Manual</button>
        <button name="modo" value="auto">Modo Automático</button><br><br>
        <button name="bomba" value="on">Encender Bomba</button>
        <button name="bomba" value="off" class="off">Apagar Bomba</button>
    </form>
</body>
</html>
""".format(modo_texto, bomba_texto)
    return html


def servidor_web(wlan):
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(5)
    print(f'Servidor activo en: http://{wlan.ifconfig()[0]}')
    
    while True:
        try:
            cliente, addr = s.accept()
            print('Se conecto un usuario desde la IP %s' % str(addr))
            request = cliente.recv(1024)
            request = str(request)
            
            
            respuesta = "HTTP/1.1 200 OK\r\n"
            respuesta += "Content-Type: text/html; charset=UTF-8\r\n"
            respuesta += "Content-Length: {}\r\n".format(len(generar_pagina()))
            respuesta += "Connection: close\r\n"
            respuesta += "\r\n"
            respuesta += generar_pagina()
            cliente.sendall(respuesta)
            utime.sleep(0.5)
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
    






WLAN = conectar_modo_STA(ssid, password)
if WLAN:
    servidor_web(WLAN)