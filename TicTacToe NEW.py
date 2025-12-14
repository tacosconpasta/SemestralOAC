from tkinter import *
from tkinter import messagebox

def crearBoton(valor,i):  # Creacion de botones
        return Button(tablero,text=valor,width=5,height=1,font=("Helvetica",15),
                      command=lambda:botonClick(i))

def seguir_o_finalizar(): # Seguir o finalizar
    resp = messagebox.askyesno("FINALIZAR", "¿Quieres continuar?")
    if resp:
       if g:
           inicio()
    else:
       tablero.destroy()
    return resp

def botonClick(i): # Coordenadas donde se presiono la casilla a jugar
    global X,Y,Z,texto,g,jugador     
    Z=int(i/16)  
    y=i%16
    Y=int(y/4)
    X=y%4
    Label(tablero, text='X='+str(X), font='arial, 20', fg='green').place(x=20,y=50)
    Label(tablero, text='Y='+str(Y), font='arial, 20', fg='green').place(x=20,y=100)
    Label(tablero, text='Z='+str(Z), font='arial, 20', fg='green').place(x=20,y=150)
    if g: # Finaliza el juego o reinicia otro
        seguir_o_finalizar()
        return
    if jugadas[Z][Y][X]==0: # Se puede jugar 
        texto=Label(tablero, text='                          ',font='arial, 20', fg='gray') # white
        texto.place(x=300, y=5)
        if jugador==0: # Jugo el jugador I
            texto = 'X'
            jugadas[Z][Y][X]=-1
            botones[i].config(text=texto, font='arial 15',fg='blue')
        else: # ugo el jugador II
            texto = 'O'
            jugadas[Z][Y][X]=1
            botones[i].config(text=texto, font='arial 15',fg='red')
        for j in range(13):  # Recorre las 13 jugadas
            if jugada_13(j): # Retorna TRUE hay ganador
                texto=Label(tablero,text='Jugador '+str(jugador+1)+' GANO',font='arial, 20', fg='blue')
                texto.place(x=300, y=5)
                g=1
                return
        if not g:  # Cambia de jugador
            jugador = not jugador
            texto=Label(tablero, text='Esperando jugada de Jugador '+str(jugador+1),font='arial, 20', fg='green')
            texto.place(x=500, y=620)
    else:
        texto=Label(tablero, text='Jugada Inválida ',font='arial, 20', fg='green')
        texto.place(x=300, y=5)
  
def jugada_13(c):  #  C[1,0,-1] 1=No Varia, 0=varia 0,1,2,3, -1=Varia 3,2,1,0
    temporalZ = C[c][0]
    temporalY = C[c][1]
    temporalX = C[c][2]
    z1 = Z if temporalZ>0 else -1  #temporalZ = C[c][0] = [Z,Y,X]
    y1 = Y if temporalY>0 else -1 
    x1 = X if temporalX>0 else -1
    s=0
    for i in range(4):
        z = Z if z1>=0 else 3-i if temporalZ else i # z=Z si Z no varia, z=i=0,1,2,3, z=(3-i)=3,2,1,0      
        y = Y if y1>=0 else 3-i if temporalY else i # y=Y si Y no varia, y=i=0,1,2,3, y=(3-i)=3,2,1,0
        x = X if x1>=0 else 3-i if temporalX else i # x=X si X no varia, x=i=0,1,2,3, x=(3-i)=3,2,1,0      
        s+=jugadas[z][y][x] #        |                 |
    if (s<4 and s>-4):      # s <= -4| s > -4  && 4 > s| s >= 4
        return False        # g=1ero |  g=No Ganador   | g=2do
    else:
        for i in range(4):  # Hay un ganador
            z = Z if z1>=0 else 3-i if temporalZ else i # z=Z si Z no varia, z=i=0,1,2,3, z=(3-i)=3,2,1,0
            y = Y if y1>=0 else 3-i if temporalY else i # y=Y si Y no varia, y=i=0,1,2,3, y=(3-i)=3,2,1,0
            x = X if x1>=0 else 3-i if temporalX else i # x=X si X no varia, x=i=0,1,2,3, x=(3-i)=3,2,1,0  
            botones[z*16+y*4+x].config(text=texto, font='arial 15',fg='yellow',bg='red') # letras amarillas fondo rojo
        return True

def inicio():  # Inicia las variables y los arreglos
    global g,ganador
    for z in range(4):
        for y in range(4):
            for x in range(4):
                jugadas[z][y][x]=0
                botones[z*16+y*4+x].config(text='',font='arial 15',fg='blue',bg='white')
    X = Y= Z = g = jugador = 0
    texto=Label(tablero, text='Jugador '+str(jugador+1),font='arial, 20', fg='green') # Jugador I
    texto.place(x=500, y=620)

# Aqui empieza el programa Raiz

jugadas = [[[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0]],  #Si las jugadas estan en cero (0) entonces
           [[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0]],  #se puede dar click en esa casilla
           [[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0]],
           [[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0]]]

#  C[1,0,-1] 1=No Varia, 0=varia 0,1,2,3, -1=Varia 3,2,1,0
C = [[1,1,0], #1- Horizontales - Z y Y no varía, x=> 0,1,2,3       4    3
     [1,0,1], #2- Verticales   - Z y X no varía, y=> 0,1,2,3       2    1
     [0,1,1], #3- Profundidad  - Y y X no varía, z=> 0,1,2,3
     [1,0,0], #4- Diagonal frontal1 - Z no varía, x=> 0,1,2,3, X==Y
     [1,-1,0],#5- Diagonal frontal2 - Z no varía, x=> 0,1,2,3 i y=> 3,2,1,0, X+Y==3
     [0,0,1], #6- Diagonal Vertical1- X no varía, z i y=> 0,1,2,3, Y==Z
     [-1,0,1],#7- Diagonal Vertical2- X no varía, y=> 0,1,2,3 i z=> 3,2,1,0, Y+Z==3
     [0,1,0], #8- Diagonal Horizonl1- Y no varía, z y x=> 0,1,2,3, X==Z
     [0,1,-1],#9- Diagonal Horizonl2- Y no varía, z=> 0,1,2,3 i x=> 3,2,1,0, X+Z==3
     [0,-1,-1],#10 Diagonal cruzada1- z=> 0,1,2,3 i x i y=> 3,2,1,0, X==Y & X+Z==3
     [0,-1,0], #11 Diagonal cruzada2- z i x=> 0,1,2,3 i y=> 3,2,1,0,  X==Z & Y+Z==3
     [0,0,-1], #12 Diagonal cruzada3- y i z=> 0,1,2,3 i x=> 3,2,1,0, Y==Z & X+Y==3
     [0,0,0]]  #13 Diagonal cruzada4- x, y i z=> 0,1,2,3, X==Y==Z

X = Y= Z = g = jugador = 0
botones=[]
tablero=Tk()
tablero.title('Tic Tac Toe 3D')
tablero.geometry("1040x720+100+5")
tablero.resizable(0, 0)
for b in range(64):
    botones.append(crearBoton(' ',b))        
contador=0
for z in range(3,-1,-1):
    for y in range(4):
        for x in range(4):
            botones[contador].grid(row=y+z*4,column=x+(3-z)*4)
            contador+=1
inicio()
botonexit = Button(tablero,text='Exit',width=5,height=1,font=("Helvetica",15),
                   command=seguir_o_finalizar)
botonexit.grid(row=0,column=10)

tablero.mainloop()