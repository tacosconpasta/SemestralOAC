from tkinter import Tk, Button, Label, messagebox, Entry, Frame
import socket
import threading
import json

#Constantes del juego
TABLERO_SIZE = 4
TOTAL_CELDAS = 64
JUGADOR1_SIMBOLO_X = 'X'
JUGADOR2_SIMBOLO_O = 'O'
JUGADOR1_VALOR_X = -1
JUGADOR2_VALOR_O = 1
CELDA_VACIA = 0

#Patrones de victoria: Cada patrón indica cómo deben alinearse 4 celdas para ganar
#Formato [Z, Y, X] donde:
#   1  = La coordenada NO cambia (permanece fija en la última jugada)
#   0  = La coordenada AUMENTA de 0 a 3 (creciente)
#  -1  = La coordenada DISMINUYE de 3 a 0 (decreciente)
PATRONES_VICTORIA = [
    [1, 1, 0],    # Horizontal: Z y Y fijos, X crece (0,1,2,3)
    [1, 0, 1],    # Vertical: Z y X fijos, Y crece (0,1,2,3)
    [0, 1, 1],    # Profundidad: Y y X fijos, Z crece (0,1,2,3)
    [1, 0, 0],    # Diagonal frontal principal: Z fijo, X=Y crecen juntos
    [1, -1, 0],   # Diagonal frontal secundaria: Z fijo, X crece y Y decrece (X+Y=3)
    [0, 0, 1],    # Diagonal vertical principal: X fijo, Y=Z crecen juntos
    [-1, 0, 1],   # Diagonal vertical secundaria: X fijo, Y crece y Z decrece (Y+Z=3)
    [0, 1, 0],    # Diagonal horizontal principal: Y fijo, X=Z crecen juntos
    [0, 1, -1],   # Diagonal horizontal secundaria: Y fijo, Z crece y X decrece (X+Z=3)
    [0, -1, -1],  # Diagonal cruzada 1: X=Y y ambos decrecen, Z crece (X=Y, X+Z=3)
    [0, -1, 0],   # Diagonal cruzada 2: X=Z crecen, Y decrece (X=Z, Y+Z=3)
    [0, 0, -1],   # Diagonal cruzada 3: Y=Z crecen, X decrece (Y=Z, X+Y=3)
    [0, 0, 0]     # Diagonal cruzada 4: X=Y=Z todas crecen juntas (diagonal perfecta 3D)
]

#Variables globales del estado del juego
tablero = None  #Matriz 3D [4][4][4]
botones = []  #Lista de los 64 botones de la interfaz gráfica
jugador_actual = 0  #Cuando es "0" = Jugador 1 (X), Cuando es "1" = Jugador 2 (O)
coordenada_x_jugada_actual = 0  # Coordenada X de la jugada actual
coordenada_y_jugada_actual = 0  # Coordenada Y de la jugada actual
coordenada_z_jugada_actual = 0  # Coordenada Z de la jugada actual
juego_terminado = False  #Indica si el juego ha terminado (alguien ganó)

#Variables de red
socket_cliente = None
mi_numero_jugador = None  #1 o 2
mi_simbolo = None  #'X' o 'O'
es_mi_turno = False
conectado = False

#Variables de interfaz
ventana = None
frame_conexion = None
entry_host = None #Input para el host
entry_port = None #Input para el puerto del host



#### REDES ####


#Conectar al servidor
def conectar_al_servidor():
    global socket_cliente, conectado
    
    #Obtener valor de las entradas
    host = entry_host.get()
    puerto = entry_port.get()
    
    #Si no se introdujo ningún valor
    if not host or not puerto:
        messagebox.showerror("Error", "Debe ingresar un host y un puerto")
        return
    
    ##VALIDACIÓN##
    
    #Intentar conexión
    try:
        #Parsear puerto de cadena => entero
        puerto = int(puerto)
        
        #Crear socket y conectar
        socket_cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_cliente.connect((host, puerto))
        
        #Si no se lanzó una excepción, la conexión fue exitosa
        conectado = True
        
        #Ocultar frame de inputs conexión
        frame_conexion.pack_forget()
        
        #Iniciar hilo para recibir mensajes del servidor, para no tapar la interfaz
        hilo_recibir = threading.Thread(target=recibir_mensajes_servidor, daemon=True)
        hilo_recibir.start()
        
        #Indicarle al usuario que falta otro usuario por conectarse, por mientras
        actualizar_label_estado("Conectado - Esperando oponente...", 'blue', 300, 5)
        
    except Exception as e:
        messagebox.showerror("Error de Conexión", f"No se pudo conectar: {e}")


#Recibe y procesa mensajes del servidor
def recibir_mensajes_servidor():
    global mi_numero_jugador, mi_simbolo, es_mi_turno, juego_terminado
    
    #Buffer para almacenar cadena del servidor
    buffer = ""
    
    try:
        #Mientras el usuario se mantenga conectado
        while conectado:
            #Recibir datos del servidor
            datos = socket_cliente.recv(1024).decode('utf-8')
            
            #Si no hay datos, salirse
            if not datos:
                break
            
            #De lo contrario, añadirle al buffer los datos
            buffer += datos
            
            #Procesar mensaje
            while '\n' in buffer:
                #Partir en cada salto de línea
                linea, buffer = buffer.split('\n', 1)
                
                #Si hay una linea
                if linea:
                    #Parsear la linea como json y asignar el json a mensaje
                    mensaje = json.loads(linea)
                    
                    #Procesar según tipo de mensaje

                    #Si se asignó número de jugador a este cliente
                    if mensaje['tipo'] == 'asignacion_jugador':
                        mi_numero_jugador = mensaje['numero_jugador']
                        mi_simbolo = mensaje['simbolo']

                        #Indicar estado a jugador de este cliente
                        ventana.after(0, lambda: label_identidad.config(
                            text=f"Eres el Jugador {mi_numero_jugador}\nFicha: {mi_simbolo}"
                        ))
                    
                    #Si se inició el juego
                    elif mensaje['tipo'] == 'iniciar_juego':
                        turno = mensaje['turno']
                        es_mi_turno = (turno == mi_numero_jugador - 1)
                        ventana.after(0, lambda: inicializar_juego())
                        ventana.after(0, lambda: actualizar_turno(turno))
                    
                    #Si se realizó una jugada
                    elif mensaje['tipo'] == 'jugada_realizada':
                        ventana.after(0, lambda m=mensaje: procesar_jugada_oponente(m))
                    
                    #Si se reinició el juego
                    elif mensaje['tipo'] == 'juego_reiniciado':
                        turno = mensaje['turno']
                        es_mi_turno = (turno == mi_numero_jugador - 1)
                        juego_terminado = False
                        ventana.after(0, lambda: inicializar_juego())
                        ventana.after(0, lambda: actualizar_turno(turno))
                    
                    #Si se desconectó el oponente
                    elif mensaje['tipo'] == 'oponente_desconectado':
                        ventana.after(0, lambda: messagebox.showinfo(
                            "Desconexión",
                            mensaje['mensaje']
                        ))
                        ventana.after(0, lambda: actualizar_label_estado(
                            "Oponente desconectado, se reinicia el juego",
                            'red', 300, 5
                        ))

                        #Reiniciar variables
                        mostrar_coordenadas_jugada_actual(0, 0, 0)
                    
                    #Si hubo un error
                    elif mensaje['tipo'] == 'error':
                        ventana.after(0, lambda m=mensaje: actualizar_label_estado(
                            m['mensaje'], 'red', 300, 5
                        ))
    
    except Exception as e:
        print(f"Error recibiendo mensajes: {e}")

#Procesar jugada que viene del servidor
def procesar_jugada_oponente(mensaje):
    #Variables a acceder en este método
    global coordenada_x_jugada_actual, coordenada_y_jugada_actual, coordenada_z_jugada_actual, es_mi_turno, juego_terminado
    
    #Jugador = numero de jugador
    jugador = mensaje['jugador']

    #Obtener coordenadas de la jugada
    x = mensaje['x']
    y = mensaje['y']
    z = mensaje['z']

    #Indica a quien le toca luego de esta jugada
    turno_siguiente = mensaje['turno_siguiente']
    
    #Actualizar coordenadas localmente
    coordenada_x_jugada_actual = x
    coordenada_y_jugada_actual = y
    coordenada_z_jugada_actual = z
    
    #Calcular índice del botón, en donde se realizó la jugada
    indice_boton = z * 16 + y * 4 + x
    
    #Actualizar tablero local y botón clickeado (por oponente)

    #Si el oponente es jugador1
    if jugador == 1:
        #Asignar simbolo de X a escribir en boton
        simbolo = JUGADOR1_SIMBOLO_X

        #Modificar valor del tablero local con el valor de X
        tablero[z][y][x] = JUGADOR1_VALOR_X

        #Renderizar X en botón
        botones[indice_boton].config(text=simbolo, font='arial 15', fg='blue')
    else:
        #Asignar simbolo de O a escribir en boton
        simbolo = JUGADOR2_SIMBOLO_O

        #Modificar valor del tablero local con el valor de O
        tablero[z][y][x] = JUGADOR2_VALOR_O

        #Renderizar O en el botón
        botones[indice_boton].config(text=simbolo, font='arial 15', fg='red')
    
    #Mostrar coordenadas
    mostrar_coordenadas_jugada_actual(x, y, z)
    
    #Verificar si el oponente ganó con esta jugada
    if verificar_ganador():
        actualizar_label_estado(f'Jugador {jugador} GANO', 'blue', 300, 5)
        juego_terminado = True
        return
    
    #Actualizar turno
    actualizar_turno(turno_siguiente)

#Actualiza el indicador de turno
def actualizar_turno(turno):
    global es_mi_turno
    
    #Si le toca al jugador de este cliente
    es_mi_turno = (turno == mi_numero_jugador - 1)
    
    #Actualizar a "Tu turno"
    if es_mi_turno:
        actualizar_label_estado('Tu turno', 'green', 500, 620)

    #Actualiza a "Turno de oponente"
    else:
        actualizar_label_estado('Turno del oponente', 'orange', 500, 620)

#Envia una jugada al servidor
def enviar_jugada_al_servidor(x, y, z):
    #Si no se está conectado, o el socket no tiene nada, devolver
    if not conectado or not socket_cliente:
        return
    
    #De lo contrario, preparar mensaje de jugada a enviar
    mensaje = {
        'tipo': 'jugada',
        'x': x,
        'y': y,
        'z': z
    }
    
    try:
        #Enviar mensjae de jugada a enviar
        socket_cliente.send((json.dumps(mensaje) + '\n').encode('utf-8'))
    except Exception as e:
        #No se pudo enviar
        print(f"Error enviando jugada: {e}")


#### FIN REDES ####




#### JUEGO ####


#Reinicia el tablero y todas las variables a su estado inicial para comenzar un juego nuevo
def inicializar_juego():
    global tablero, juego_terminado
    
    #Crear tablero 3D de 4x4x4 (64) lleno de celdas=0. 
    tablero = [[[CELDA_VACIA for _ in range(TABLERO_SIZE)] 
                   for _ in range(TABLERO_SIZE)] 
                  for _ in range(TABLERO_SIZE)]
    
    #Limpiar todos los botones: sin texto, color azul, fondo blanco
    for boton in botones:
        boton.config(text='', font='arial 15', fg='blue', bg='white')

    #Se limpia el juego_terminado de ronda anterior, si se reinició el juego con botón Salir
    juego_terminado = False

#Crea un botón, sin texto, en el tablero. tablero[indice_boton] = boton
def crear_boton(indice_boton):
    return Button(
        frame_tablero,
        text='',
        width=5,
        height=1,
        font=("Helvetica", 15),
        command=lambda: handle_click_boton(indice_boton)
    )

#Al hacer click en un boton
def handle_click_boton(indice_boton):
    #Se acceden a estas variables en este método
    global coordenada_x_jugada_actual, coordenada_y_jugada_actual, coordenada_z_jugada_actual

    #Si este cliente no está conectado
    if not conectado:
        actualizar_label_estado('No estás conectado', 'red', 300, 5)
        return
    
    #Si el juego terminó
    if juego_terminado:
        preguntar_continuar_o_salir()
        return

    #Si no es el turno del cliente actual e intentó hacer una jugada
    if not es_mi_turno:
        actualizar_label_estado('No es tu turno, las trampas son malas.', 'red', 300, 5)
        return
    
    #Convertir el índice lineal del botón (0-63) a sus coordenadas 3D (x, y, z)
    #Cada plano Z tiene 16 celdas (4x4), por eso dividimos entre 16
    coordenada_z_jugada_actual = indice_boton // 16
    
    #El residuo nos da la posición dentro del plano Z actual
    residuo = indice_boton % 16
    
    #Dentro del plano, cada fila Y tiene 4 celdas
    coordenada_y_jugada_actual = residuo // 4
    
    #El residuo final nos da la columna X
    coordenada_x_jugada_actual = residuo % 4

    #Verificar si la celda, a la cual se le hizo click, está vacía
    if tablero[coordenada_z_jugada_actual][coordenada_y_jugada_actual][coordenada_x_jugada_actual] != CELDA_VACIA:
        actualizar_label_estado('Celda ocupada. Las trampas son malas', 'red', 300, 5)
        return
    
    #Si todo está bien, enviar jugada al servidor
    enviar_jugada_al_servidor(
        coordenada_x_jugada_actual,
        coordenada_y_jugada_actual,
        coordenada_z_jugada_actual
    )
    
#Verifica todos los patrones de victoria posibles en la jugada actual
def verificar_ganador():
    for patron in PATRONES_VICTORIA:
        if verificar_linea_ganadora(patron):
            return True
    return False

def verificar_linea_ganadora(patron):
    """
    Verifica si hay 4 fichas del mismo jugador alineadas según el patrón ganador a analizar.
    
    Por ejemplo, si se acaba de jugar en X=2, Y=1, Z=3.
    Ahora necesitamos revisar si esa jugada completó una línea de 4 fichas. (Osea, si es ganadora)
    
    Para cada tipo de línea (horizontal, vertical, diagonal, etc.), se necesita:
    1. Identificar cuáles coordenadas se QUEDAN FIJAS (no cambian)
    2. Identificar cuáles coordenadas VARÍAN (cambian) para formar la línea
    
    EJEMPLO - Línea Horizontal:
    Si buscamos una línea horizontal (como ----), queremos revisar:
    - Misma fila Y (FIJA), no sube ni baja
    - Mismo plano Z (FIJA), no va en profundidad
    - Pero X cambia: revisamos X=0, X=1, X=2, X=3 (VARIABLE CRECIENTE) (izquierda->derecha)
    
    EJEMPLO - Diagonal Frontal:
    Si buscamos diagonal frontal (como /), queremos revisar:
    - Mismo plano Z (FIJA)
    - Pero X y Y cambian juntas: (0,0), (1,1), (2,2), (3,3) (AMBAS CRECIENTES)
    
    El patrón [modo_z, modo_y, modo_x] nos dice cómo se comporta cada una de las coordenadas:
    - modo = 1: significa que esa coordenada NO CAMBIA (se queda donde jugaste)
    - modo = 0: significa que esa coordenada CRECE (va de 0 a 3)
    - modo = -1: significa que esa coordenada DECRECE (va de 3 a 0)
    """

    #Asignar patrón a los modos. Recordar que patrón es una tripla [-1, 0, 1]
    modo_z, modo_y, modo_x = patron
    
    # PASO 1: Identificar cuáles coordenadas permanecen FIJAS
    # Una coordenada es FIJA cuando su modo = 1
    # Si es fija, guardamos el valor donde se jugó (coordenada_z_jugada_actual)
    # Si NO es fija, guardamos -1 para indicar "esta coordenada va a cambiar"
    
    # Ejemplo: Si modo_z = 1, entonces Z es fija, no cambiará, entonces guardamos Z=3 (jugada_actual = 3)
    # Ejemplo: Si modo_z = 0, entonces Z NO es fija y guardamos -1 (Z va a variar), luego vemos que hacer.
    coordenada_z_es_fija = coordenada_z_jugada_actual if modo_z > 0 else -1
    coordenada_y_es_fija = coordenada_y_jugada_actual if modo_y > 0 else -1
    coordenada_x_es_fija = coordenada_x_jugada_actual if modo_x > 0 else -1
    
    #PASO 2: Revisar las 4 celdas que forman la línea

    #Cada celda puede tener:
    #   -1 si tiene una X (Jugador 1)
    #   +1 si tiene una O (Jugador 2)
    #    0 si está vacía

    #Se sumará el valor dentro de cada celda en suma_linea (- - - -)
    
    #Si, al recorrer la dimensión, suma_linea = -4, significa: X+X+X+X = -1-1-1-1 = -4 (Jugador 1 gana)
    #Si, al recorrer la dimensión, suma_linea = +4, significa: O+O+O+O = +1+1+1+1 = +4 (Jugador 2 gana)
    #Cualquier otro valor significa que no hay ganador en esta línea, y que el juego continua.
    
    suma_linea = 0
    
    #Recorremos 4 veces porque necesitamos revisar exactamente el largo, ancho, o profundidad, del tablero.
    for i in range(TABLERO_SIZE):
        #Para cada iteración (i = 0, 1, 2, 3), calculamos dónde mirar
        #La función obtener_coordenada decide si usar el valor fijo o el valor variable
        z = obtener_coordenada(coordenada_z_jugada_actual, coordenada_z_es_fija, modo_z, i)
        y = obtener_coordenada(coordenada_y_jugada_actual, coordenada_y_es_fija, modo_y, i)
        x = obtener_coordenada(coordenada_x_jugada_actual, coordenada_x_es_fija, modo_x, i)
        
        #Sumamos el valor de la celda actual (0, -1, +1) a suma_línea
        suma_linea += tablero[z][y][x]
    
    #PASO 3: Verificar si hay un ganador
    #Si la suma es exactamente 4 o -4, ¡hay un ganador! Y se sabe que fue el que acaba de jugar
    if abs(suma_linea) == TABLERO_SIZE:
        #Resaltar la línea ganadora
        resaltar_linea_ganadora(patron, coordenada_z_es_fija, coordenada_y_es_fija, coordenada_x_es_fija)

        #Retornar cierto, alguien ganó
        return True
    
    #No hay ganador en esta línea específica
    return False

def obtener_coordenada(coordenada_actual, coordenada_fija, modo, indice_iteracion):
    """
    Calcula el valor de una coordenada para revisar una celda específica en la línea.
    
    EJEMPLO:
    Se jugó X=2, Y=1, Z=3 y se está revisando línea horizontal (----)
    Como es mencionado en verificar_linea_ganadora, en una línea horizontal, Y y Z no cambian, pero X sí cambia.
    
    Esta función se llama 4 veces en un for loop en verificar_linea_ganadora
    Por lo que, se verifica (i=0, i=1, i=2, i=3) para las 4 celdas:
    
    COORDENADA FIJA (modo = 1)
    - Siempre devuelve el mismo valor (donde jugaste)
    - Ejemplo: Para Y en línea horizontal
    - i=0 => devuelve Y=1
    - i=1 => devuelve Y=1
    - i=2 => devuelve Y=1
    - i=3 => devuelve Y=1
    - Resultado: Siempre se mira la fila Y=1
    
    COORDENADA CRECIENTE (modo = 0)
    - Va aumentando de 0 a 3
    - Ejemplo: Para X en línea horizontal
    - i=0 => devuelve X=0
    - i=1 => devuelve X=1
    - i=2 => devuelve X=2
    - i=3 => devuelve X=3
    - Resultado: Se revisa el ancho de izquierda a derecha
    
    COORDENADA DECRECIENTE (modo = -1)
    - Va disminuyendo de 3 a 0
    - Ejemplo: Para X en una diagonal invertida
    - i=0 => devuelve X=3 (calculado como 3-0=3)
    - i=1 => devuelve X=2 (calculado como 3-1=2)
    - i=2 => devuelve X=1 (calculado como 3-2=1)
    - i=3 => devuelve X=0 (calculado como 3-3=0)
    - Resultado: Revisamos el ancho de derecha a izquierda
    """
    
    #COORDENADA FIJA
    #Si coordenada_fija es mayor o igual a 0, significa que tiene un valor fijo
    #(Recordar que pusimos -1 cuando NO es fija)
    if coordenada_fija >= 0:
        #La coordenada NO cambia, siempre devolvemos donde se jugó (Y=1, Y=1, Y=1, Y=1)
        return coordenada_actual
    
    #Si la coordenada no es fija, cambia (es variable)
    #Si es DECRECIENTE (va de 3 a 0)
    elif modo < 0:
        # Fórmula para decrecer: empezar en 3 y restar el índice

        #Recordar que esta función está dentro de un for loop
        # i=0 => 3-0=3
        # i=1 => 3-1=2
        # i=2 => 3-2=1
        # i=3 => 3-3=0
        return 3 - indice_iteracion 
    
    #Si no es fija ni decrece, entonces CRECE (va de 0 a 3)
    else:
        #Simplemente devolvemos el índice actual
        # i=0 => 0
        # i=1 => 1
        # i=2 => 2
        # i=3 => 3
        return indice_iteracion

#Renderiza la línea ganadora
def resaltar_linea_ganadora(patron, coordenada_z_fija, coordenada_y_fija, coordenada_x_fija):
    #Asignar tripla a modos. [z, y, x] => [-1, 0, 1]
    modo_z, modo_y, modo_x = patron
    
    for i in range(TABLERO_SIZE):
        z = obtener_coordenada(coordenada_z_jugada_actual, coordenada_z_fija, modo_z, i)
        y = obtener_coordenada(coordenada_y_jugada_actual, coordenada_y_fija, modo_y, i)
        x = obtener_coordenada(coordenada_x_jugada_actual, coordenada_x_fija, modo_x, i)
        
        # Convertir coordenadas 3D de vuelta a índice lineal
        indice_boton = z * 16 + y * 4 + x
        
        #Determinar qué símbolo debe repintarse para mostrar quién ganó
        simbolo = tablero[z][y][x]
        simbolo_texto = JUGADOR1_SIMBOLO_X if simbolo == JUGADOR1_VALOR_X else JUGADOR2_SIMBOLO_O
        
        # Aplicar colores de victoria: amarillo sobre rojo
        botones[indice_boton].config(
            text=simbolo_texto,
            font='arial 15',
            fg='yellow',
            bg='red'
        )

#Renderiza la jugada actual en el tablero, dado (x,yz)
def mostrar_coordenadas_jugada_actual(x, y, z):
    label_x.config(text=f'X={x}')
    label_y.config(text=f'Y={y}')
    label_z.config(text=f'Z={z}')

#Actualiza el mensaje de estado
def actualizar_label_estado(texto, color, x, y):
    label_estado.config(text=texto, fg=color)

#Finalizar juego, o continuar a otra ronda
def preguntar_continuar_o_salir():
    respuesta = messagebox.askyesno("FINALIZAR", "¿Deseas reiniciar el Juego? \n\n(Sólo se puede reiniciar cuando hay un ganador, no sería justo reiniciar cuando vas perdiendo, tramposo.)")

    #Si se quiere reiniciar y el juego ya se acabó
    if respuesta and juego_terminado:
        #Enviar solicitud de reinicio al servidor
        if conectado and socket_cliente:
            mensaje = {'tipo': 'reiniciar_juego'}
            socket_cliente.send((json.dumps(mensaje) + '\n').encode('utf-8'))

#Configuración de la ventana principal
ventana = Tk()
ventana.title('Tic Tac Toe 3D')
ventana.geometry("1040x720+100+5")
ventana.resizable(True, True)

#Frame principal
frame_principal = Frame(ventana)
frame_principal.pack(fill='both', expand=True)

#Frame izquierdo (estado + coordenadas)
frame_izquierdo = Frame(frame_principal, width=250)
frame_izquierdo.pack(side='left', fill='y', padx=10, pady=10)


#Frame derecho (acciones)
frame_derecho = Frame(frame_principal, width=120)
frame_derecho.pack(side='right', fill='y', padx=10, pady=10)
frame_derecho.pack_propagate(False)


#Frame central (tablero)
frame_centro = Frame(frame_principal)
frame_centro.pack(side='left', expand=True, fill='both', padx=10, pady=10)


## INPUT REDES ##

#Frame de conexión
frame_conexion = Frame(frame_izquierdo)
frame_conexion.pack(pady=20)

#Obtener host
Label(frame_conexion, text="Host:", font='arial 15').grid(row=0, column=0, padx=5)
entry_host = Entry(frame_conexion, font='arial 15', width=15)
entry_host.insert(0, "srv595743.hstgr.cloud")
entry_host.grid(row=0, column=1, padx=5)

#Obtener Puerto
Label(frame_conexion, text="Puerto:", font='arial 15').grid(row=1, column=0, padx=5, pady=10)
entry_port = Entry(frame_conexion, font='arial 15', width=15)
entry_port.insert(0, "5555")
entry_port.grid(row=1, column=1, padx=5, pady=10)

#Botón para conectar
Button(
    frame_conexion,
    text="Conectar",
    font='arial 15',
    command=conectar_al_servidor
).grid(row=2, column=0, columnspan=2, pady=10)

## FIN INPUT REDES ##



## Interfaz de Juego ##{

#Frame para el tablero
frame_tablero = Frame(frame_centro)
frame_tablero.pack(expand=True)

#Frame para botones superiores
frame_superior = Frame(frame_derecho)
frame_superior.pack(anchor='n', pady=100)

#Frame de estado del juego
frame_estado = Frame(frame_izquierdo, width=200, height=400)
frame_estado.pack(fill='x', pady=20)
frame_estado.pack_propagate(False)


#Label de estado (UN SOLO LABEL)
label_estado = Label(
    frame_estado,
    text="No conectado",
    font='arial 16',
    fg='black',
    wraplength=220,
    justify='center'
)
label_estado.pack(pady=10)

# Label fijo para mostrar quién eres
label_identidad = Label(
    frame_izquierdo,
    text="",
    font='arial 16 bold',
    fg='black',
    wraplength=220,
    justify='center'
)
label_identidad.pack(pady=10)


#Frame de coordenadas
frame_coordenadas = Frame(frame_izquierdo)
frame_coordenadas.pack(pady=20)

label_x = Label(frame_coordenadas, text='X=0', font='arial 18', fg='green')
label_x.pack(anchor='w')

label_y = Label(frame_coordenadas, text='Y=0', font='arial 18', fg='green')
label_y.pack(anchor='w')

label_z = Label(frame_coordenadas, text='Z=0', font='arial 18', fg='green')
label_z.pack(anchor='w')

#Crear los 64 botones del tablero (4x4x4 = 64 celdas)
for i in range(TOTAL_CELDAS):
    botones.append(crear_boton(i))

#Organizar los botones en la interfaz gráfica formando un cubo 3D visual
#Se recorre de arriba (z=3) hacia abajo (z=0) para que visualmente parezca un cubo
indice_boton = 0
for z in range(3, -1, -1):
    for y in range(TABLERO_SIZE):
        for x in range(TABLERO_SIZE):
            #Separar verticalmente cada plano Z
            fila = y + z * 4  

            #Separar horizontalmente cada plano Z
            columna = x + (3 - z) * 4
            
            botones[indice_boton].grid(
                row=fila,
                column=columna,
                padx=2,
                pady=2,
                sticky='nsew'
            )
            indice_boton += 1

#Hacer que el grid del tablero sea responsivo
for i in range(16):
    frame_tablero.columnconfigure(i, weight=1)
    frame_tablero.rowconfigure(i, weight=1)

#Crear botón de salida en la esquina superior derecha
boton_salir = Button(
    frame_superior,
    text='Restart/Salir',
    width=25,
    height=1,
    font=("Helvetica", 15),
    command=preguntar_continuar_o_salir
)
boton_salir.pack()

# Iniciar el primer juego
inicializar_juego()

# Mantener la ventana abierta y esperando interacción del usuario
ventana.mainloop()