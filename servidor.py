import socket
import threading
import json

#Constantes 
HOST = '0.0.0.0' #Escuchar en todas las interfaces de red 
PORT = 5555
JUGADOR1_SIMBOLO = 'X'
JUGADOR2_SIMBOLO = 'O'

#Lista de sockets de clientes conectados
clientes_conectados = [] 

#[jugador1: 0; jugador2: 1];
turno_actual = 0  

#Tablero del servidor, registra movimientos y los envia a los clientes
tablero_servidor = [[[0 for _ in range(4)] for _ in range(4)] for _ in range(4)]

#Bandera de juego
juego_iniciado = False 

#Envia un mensaje a todos los clientes conectados (mensaje, clienteAExcluir)
#Por defecto, no se excluye a ningun cliente
def emitir_mensaje(mensaje, excluir_cliente=None):
    #Convertir mensjae a json
    mensaje_json = json.dumps(mensaje) + '\n'
    
    #Por cada cliente conectado
    for cliente in clientes_conectados:
        #Si hay un cliente a excluir y es este, no enviar
        if excluir_cliente and cliente == excluir_cliente:
            continue
        
        #Enviar el json
        try:
            cliente.send(mensaje_json.encode('utf-8'))

        except:
            # Si falla el envío, remover este cliente
            if cliente in clientes_conectados:
                clientes_conectados.remove(cliente)


def manejar_cliente(socket_cliente, numero_jugador):
    """
    Maneja la comunicación con un cliente específico.
    
    Esta función se ejecuta en un hilo separado para cada cliente.
    Recibe los mensajes del cliente y los procesa.
    """
    global turno_actual, tablero_servidor, juego_iniciado
    
    print(f"Jugador {numero_jugador} conectado")
    
    #Enviar al cliente su número de jugador
    mensaje_bienvenida = {
        'tipo': 'asignacion_jugador',
        'numero_jugador': numero_jugador,
        'simbolo': JUGADOR1_SIMBOLO if numero_jugador == 1 else JUGADOR2_SIMBOLO
    }

    #Enviar mensaje de bienvenida a cliente
    socket_cliente.send((json.dumps(mensaje_bienvenida) + '\n').encode('utf-8'))
    
    #Si ya hay 2 jugadores, y el juego no ha empezado, iniciar el juego
    if len(clientes_conectados) == 2 and not juego_iniciado:
        juego_iniciado = True
        mensaje_inicio = {
            'tipo': 'iniciar_juego',
            'turno': turno_actual
        }

        #Enviar mensaje de inicio
        emitir_mensaje(mensaje_inicio)
        print("Juego iniciado!")
    
    #Parte de escucha
    try:
        #Buffer para acumular datos
        buffer = ""
        
        #Escuchar
        while True:
            #Recibir datos del cliente
            datos = socket_cliente.recv(1024).decode('utf-8')
            
            #Si no hay datos
            if not datos:
                #Cliente desconectado
                break
            
            #Agregar datos al buffer
            buffer += datos
            
            #Procesar mensaje completo (separado por \n)
            while '\n' in buffer:
                linea, buffer = buffer.split('\n', 1)
                
                #Si la linea no está vacia
                if linea:
                    #Cargar json
                    mensaje = json.loads(linea)
                    
                    #Procesar según el tipo de mensaje
                    if mensaje['tipo'] == 'jugada':
                        procesar_jugada(mensaje, socket_cliente, numero_jugador)
                    
                    #Si el tipo es reiniciar juego, se reinicia el juego (Añadir confirmación de otro cliente)
                    elif mensaje['tipo'] == 'reiniciar_juego':
                        reiniciar_juego()
    
    except Exception as e:
        print(f"Error con Jugador {numero_jugador}: {e}")
    
    #Si se desconectó un jugador
    finally:
        #Cliente desconectado - notificar al otro jugador
        print(f"Jugador {numero_jugador} desconectado")
        
        #Remover cliente desconectado de clientes
        if socket_cliente in clientes_conectados:
            clientes_conectados.remove(socket_cliente)
        
        #cerrar conexión con el cliente
        socket_cliente.close()
        
        #Notificar al otro jugador que su oponente se desconectó
        mensaje_desconexion = {
            'tipo': 'oponente_desconectado',
            'mensaje': f'Jugador {numero_jugador} se desconectó'
        }

        emitir_mensaje(mensaje_desconexion)
        
        #Resetear el estado del juego
        juego_iniciado = False

#Procesa jugada de cliente
def procesar_jugada(mensaje, socket_cliente, numero_jugador):
    global turno_actual, tablero_servidor
    
    #Si la jugada viene de un jugador, cuyo turno no es el actual
    if numero_jugador - 1 != turno_actual:
        #Crear mensaje de invalidación
        mensaje_error = {
            'tipo': 'error',
            'mensaje': 'No es tu turno'
        }
        #Enviar el mensaje de invalidación
        socket_cliente.send((json.dumps(mensaje_error) + '\n').encode('utf-8'))
        return
    
    #De lo contrario, si la jugada es válida (le toca al jugador de esta jugada)
    #Extraer información de la jugada
    x = mensaje['x']
    y = mensaje['y']
    z = mensaje['z']
    
    #Si la celda ya está ocupada en el tablero
    if tablero_servidor[z][y][x] != 0:
        #Constuir mensaje
        mensaje_error = {
            'tipo': 'error',
            'mensaje': 'Celda ocupada'
        }
        #Enviar mensjae de invalidación
        socket_cliente.send((json.dumps(mensaje_error) + '\n').encode('utf-8'))
        return
    
    #Si todo está bien...
    #El valor a guardar, en el tablero, es:
    #  -1 si es Jugador2
    #   1 si es Jugador1
    valor = -1 if numero_jugador == 1 else 1

    #Registrar la jugada en el tablero del servidor
    tablero_servidor[z][y][x] = valor
    
    #Cambiar el turno al jugador opuesto
    turno_actual = 1 - turno_actual
    
    #Crear mensaje de jugada a enviar a todos los clientes
    mensaje_jugada = {
        'tipo': 'jugada_realizada',
        'jugador': numero_jugador,
        'x': x,
        'y': y,
        'z': z,
        'turno_siguiente': turno_actual
    }

    #Retransmitir la jugada a todos los clientes
    emitir_mensaje(mensaje_jugada)
    
    #Imprimir jugada como log
    print(f"Jugador {numero_jugador} jugó en ({x}, {y}, {z})")

#Reinicia el estado del juego
def reiniciar_juego():
    global turno_actual, tablero_servidor
    
    #Resetear el tablero
    tablero_servidor = [[[0 for _ in range(4)] for _ in range(4)] for _ in range(4)]
    
    #El Jugador 1 siempre comienza
    turno_actual = 0
    
    #Notificar a todos los clientes
    mensaje_reinicio = {
        'tipo': 'juego_reiniciado',
        'turno': turno_actual
    }
    emitir_mensaje(mensaje_reinicio)
    
    print("Juego reiniciado")

#Inicia el servidor, acepta máximo 2 clientes
def iniciar_servidor():
    #Crear socket del servidor
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    #Permitir reutilizar la dirección inmediatamente
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    #Enlazar el socket al host y puerto deseados
    servidor.bind((HOST, PORT))
    
    #Escuchar conexiones entrantes (máximo 2 en espera)
    servidor.listen(2)
    servidor.settimeout(1.0)
    
    #Logging
    print(f"Servidor iniciado en {HOST}:{PORT}")
    print("Esperando jugadores...")
    
    #Asignar Jugador1 a primer cliente
    numero_jugador = 1
    
    try:
        #Escuchar
        while True:
            try:
              #Si se conecta un cliente
              socket_cliente, direccion = servidor.accept()
            except socket.timeout:
              continue  # vuelve al loop, permite Ctrl+C
            
            #Si es un 3er cliente, es invalido
            if len(clientes_conectados) >= 2:
                #Crear mensaje de rechazo
                mensaje_rechazo = {
                    'tipo': 'servidor_lleno',
                    'mensaje': 'El servidor ya tiene 2 jugadores'
                }
                #Enviar rechazo
                socket_cliente.send((json.dumps(mensaje_rechazo) + '\n').encode('utf-8'))
                #Cerrar conexión con este 3er cliente
                socket_cliente.close()
                continue
            
            #Si es 1 o 2do cliente,
            #Agregar cliente a la lista
            clientes_conectados.append(socket_cliente)
            
            #Crear un hilo para manejar este cliente
            hilo_cliente = threading.Thread(
                target=manejar_cliente,
                args=(socket_cliente, numero_jugador)
            )

            hilo_cliente.daemon = True  #El hilo se cierra cuando el programa principal termina
            hilo_cliente.start() #Empezar hilo
            
            #Le toca al siguiente cliente, el Jugador2
            numero_jugador += 1
            
            #Cuando hayan ya 2 jugadores conectados, reiniciar contador para siguientes clientes
            if numero_jugador > 2:
                numero_jugador = 1
    
    #Al interrumpir con teclado
    except KeyboardInterrupt:
        print("\nCerrando servidor...")
    
    #Siempre cerrar el servidor
    finally:
        servidor.close()


if __name__ == "__main__":
    iniciar_servidor()