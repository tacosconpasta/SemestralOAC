from tkinter import Tk, Button, Label, messagebox

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

#Reinicia el tablero y todas las variables a su estado inicial para comenzar un juego nuevo
def inicializar_juego():
    global tablero, jugador_actual, juego_terminado
    
    #Crear tablero 3D de 4x4x4 (64) lleno de celdas=0. 
    tablero = [[[CELDA_VACIA for _ in range(TABLERO_SIZE)] 
                   for _ in range(TABLERO_SIZE)] 
                  for _ in range(TABLERO_SIZE)]
    
    #Limpiar todos los botones: sin texto, color azul, fondo blanco
    for boton in botones:
        boton.config(text='', font='arial 15', fg='blue', bg='white')
    
    #El Jugador 1 (X) siempre comienza
    jugador_actual = 0
    
    #Se limpia el juego_terminado de ronda anterior, si se reinició el juego con botón Salir
    juego_terminado = False
    
    #Mostrar mensaje de turno del Jugador 1
    actualizar_label_estado(f'Jugador {jugador_actual + 1}', 'green', 500, 620)

#Crea un botón, sin texto, en el tablero. tablero[indice_boton] = boton
def crear_boton(indice_boton):
    return Button(
        ventana,
        text='',
        width=5,
        height=1,
        font=("Helvetica", 15),
        command=lambda: handle_click_boton(indice_boton)
    )

#Al hacer click en un boton
def handle_click_boton(indice_boton):
    #Se acceden a estas variables en este método
    global jugador_actual, coordenada_x_jugada_actual, coordenada_y_jugada_actual, coordenada_z_jugada_actual, juego_terminado
    
    #Convertir el índice lineal del botón (0-63) a sus coordenadas 3D (x, y, z)
    #Cada plano Z tiene 16 celdas (4x4), por eso dividimos entre 16
    coordenada_z_jugada_actual = indice_boton // 16
    
    #El residuo nos da la posición dentro del plano Z actual
    residuo = indice_boton % 16
    
    #Dentro del plano, cada fila Y tiene 4 celdas
    coordenada_y_jugada_actual = residuo // 4
    
    #El residuo final nos da la columna X
    coordenada_x_jugada_actual = residuo % 4
    
    #Actualizar la visualización de las coordenadas en pantalla
    mostrar_coordenadas_jugada_actual(coordenada_x_jugada_actual, coordenada_y_jugada_actual, coordenada_z_jugada_actual)
    
    #Si el juego ya terminó, preguntar si quiere jugar de nuevo
    if juego_terminado:
        preguntar_continuar_o_salir()
        return
    
    #Verificar si la celda ya está ocupada por alguna jugada anterior.
    #Si está ocupada, marcar como jugada inválida
    if tablero[coordenada_z_jugada_actual][coordenada_y_jugada_actual][coordenada_x_jugada_actual] != CELDA_VACIA:
        actualizar_label_estado('Jugada Inválida', 'red', 300, 5)
        return
    
    #Limpiar cualquier mensaje de error previo
    actualizar_label_estado('                          ', 'gray', 300, 5)
    
    #Si el jugador actual es 0, registrar su jugada (Marcar casilla/boton con X)
    if jugador_actual == 0:
        #Simbolo a mostrar
        simbolo_a_mostrar = JUGADOR1_SIMBOLO_X

        #tablero[x][y][z] = valor de X (NO simbolo)
        tablero[coordenada_z_jugada_actual][coordenada_y_jugada_actual][coordenada_x_jugada_actual] = JUGADOR1_VALOR_X

        #Mostrar en botón clickeado
        botones[indice_boton].config(text=simbolo_a_mostrar, font='arial 15', fg='blue')
    
    #Si el jugador es el Jugador 2
    else:
        #Simbolo a mostrar
        simbolo_a_mostrar = JUGADOR2_SIMBOLO_O

        #tablero[x][y][z] = valor de O (NO simbolo)
        tablero[coordenada_z_jugada_actual][coordenada_y_jugada_actual][coordenada_x_jugada_actual] = JUGADOR2_VALOR_O

        #Mostrar en botón clickeado
        botones[indice_boton].config(text=simbolo_a_mostrar, font='arial 15', fg='red')
    
    #Verificar si esta jugada ACTUAL generó un ganador
    if verificar_ganador():
        #Si la jugada actual ganó, entonces, mostrar en estado
        actualizar_label_estado(f'Jugador {jugador_actual + 1} GANO', 'blue', 300, 5)

        #Marcar el juego como terminado
        juego_terminado = True
        #Retornar
        return

    #Togglea al otro jugador (0 se vuelve 1, 1 se vuelve 0) [Jugador1 = 0; Jugador2 = 1]
    jugador_actual = 1 - jugador_actual
    
    #Mostrar mensaje de turno del siguiente jugador
    actualizar_label_estado(
        f'Esperando jugada de Jugador {jugador_actual + 1}',
        'green',
        500,
        620
    )

#Verifica todos los patrones de victoria posibles en la jugada actual
def verificar_ganador():
    for patron in PATRONES_VICTORIA:
        if verificar_linea_ganadora(patron):
            return True
    return False

def verificar_linea_ganadora(patron):
    """
    Verifica si hay 4 fichas del mismo jugador alineadas según el patrón dado.
    
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
    modo_z, modo_y, modo_x = patron
    
    for i in range(TABLERO_SIZE):
        z = obtener_coordenada(coordenada_z_jugada_actual, coordenada_z_fija, modo_z, i)
        y = obtener_coordenada(coordenada_y_jugada_actual, coordenada_y_fija, modo_y, i)
        x = obtener_coordenada(coordenada_x_jugada_actual, coordenada_x_fija, modo_x, i)
        
        # Convertir coordenadas 3D de vuelta a índice lineal
        indice_boton = z * 16 + y * 4 + x
        
        # Determinar qué símbolo mostrar según quién ganó
        simbolo = JUGADOR1_SIMBOLO_X if jugador_actual == 0 else JUGADOR2_SIMBOLO_O
        
        # Aplicar colores de victoria: amarillo sobre rojo
        botones[indice_boton].config(
            text=simbolo,
            font='arial 15',
            fg='yellow',
            bg='red'
        )

#Renderiza la jugada actual en el tablero, dado (x,yz)
def mostrar_coordenadas_jugada_actual(x, y, z):
    Label(ventana, text=f'X={x}', font='arial 20', fg='green').place(x=20, y=50)
    Label(ventana, text=f'Y={y}', font='arial 20', fg='green').place(x=20, y=100)
    Label(ventana, text=f'Z={z}', font='arial 20', fg='green').place(x=20, y=150)

#Actualiza el mensaje de estado
def actualizar_label_estado(texto, color, x, y):
    label = Label(ventana, text=texto, font='arial 20', fg=color)
    label.place(x=x, y=y)

#Finalizar juego, o continuar a otra ronda
def preguntar_continuar_o_salir():
    respuesta = messagebox.askyesno("FINALIZAR", "¿Quieres continuar?")
    if respuesta and juego_terminado:
        inicializar_juego()
    elif not respuesta:
        ventana.destroy()


#Configuración de la ventana principal
ventana = Tk()
ventana.title('Tic Tac Toe 3D')
ventana.geometry("1040x720+100+5")
ventana.resizable(False, False)

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
            
            botones[indice_boton].grid(row=fila, column=columna)
            indice_boton += 1

#Crear botón de salida en la esquina superior derecha
boton_salir = Button(
    ventana,
    text='Exit',
    width=5,
    height=1,
    font=("Helvetica", 15),
    command=preguntar_continuar_o_salir
)
boton_salir.grid(row=0, column=10)

# Iniciar el primer juego
inicializar_juego()

# Mantener la ventana abierta y esperando interacción del usuario
ventana.mainloop()