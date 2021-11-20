import numpy as np
from scipy.integrate import odeint
import scipy.integrate as integrator
import matplotlib.pyplot as plt
import pygame
import time
import sys
#from cliente import Cliente # cliente OPCUA
from controlV3 import Cliente #cliente Control
import random
import threading

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import pandas as pd
from dash.dependencies import Output, Input, State
import plotly
import plotly.express as px
import plotly.graph_objs as go
from plotly import subplots
import dash_bootstrap_components as dbc
import json
import datetime
from collections import deque
import os
import itertools


# Función que se suscribe
def funcion_handler(node, val):
    key = node.get_parent().get_display_name().Text
    variables_manipuladas[key] = val # Se cambia globalmente el valor de las variables manipuladas cada vez que estas cambian
    print('key: {} | val: {}'.format(key, val))


class SubHandler(object): # Clase debe estar en el script porque el thread que comienza debe mover variables globales
    def datachange_notification(self, node, val, data):
        thread_handler = threading.Thread(target=funcion_handler, args=(node, val))  # Se realiza la descarga por un thread
        thread_handler.start()

    def event_notification(self, event):
        
        global eventoAlarm
        
        eventoAlarm = event
        


frecMax = 1 # [Hz]
periodo_interfaz = 500  # [ms]


app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "EXP1"
  
colors = {
    'background': '#111111',  # negro
    'background1': '#FFFFFF', # blanco
    'background2': '#B6B6B6', # gris
    'gris-claro':'#eeeeee',
    'text': '#7FDBFF',   # celeste
    'text1': '#FFFFFF', #blanco
    'text2': '#111111'}  #negro


#INTERFAZ
app.layout = dbc.Container(
    [
     
     html.H3(["Interfaz de Control de Tanques", dbc.Badge("!", className="ml-1")]),
     html.Hr(),
     
     dcc.Interval(id='interval-component', interval=int(1/frecMax*periodo_interfaz), n_intervals=0), #0.5 seg
     
     #ALARMA SECCIÓN
     html.Div([
            html.H2(id='Alarm-msje', style={'textAlign':'center', 'color': colors['text2'], 'paddingBottom':'40px'}, children=['']),
        
     ]),
               
   html.P("", className="card-text"),                         
     
     dbc.Tabs([
         
         #Pestaña 1:
         dbc.Tab(label="Monitoreo", tab_id="", children= [
             
             html.P("", className="card-text"),
                 
             #Valor Actual de la Altura de los Tanques     
             html.Div(id='get-alturas', style={'display':'none','color': colors['text2']}),
             html.Div(id='update-alturas'),
             
             html.P("", className="card-text"),
             # Grafico de Altura de Tanques
             
             html.H3(["Monitoreo de Tanques"]),
             
             dcc.Graph(id='live-graph-tank'),
            
             html.P("", className="card-text"), 
             
             html.Div(id='', style={'paddingBottom':'30px', 'textAlign': 'center'}, children=[
                        
                 dbc.Button('Guardar Datos', color="info", className="mr-1",id='save-data', n_clicks=0),      # boton de guardado
                 
                 html.Span(id="output-muestras", style={'display':'none',"verticalAlign": "middle"}),
                 html.Span(id="output-save", style={"verticalAlign": "middle"}),
                 
                 html.Span(id="", style={"verticalAlign": "middle"}),
                  
                        html.P("", className="card-text"),
                        html.P(id="output-formato", style={'display':'none',"verticalAlign": "middle"}),
                        
                        # Casillas para seleccionar el formato del archivo a guardar
                        dcc.RadioItems(id='formato', options=[
                            {'label':'.csv ', 'value':'csv'}, 
                            {'label':'.npy ', 'value':'npy'}, 
                            {'label':'.txt ', 'value':'txt'}], 
                            value='csv'),
                
                html.P("", className="card-text"),
                #inputs referencias
                 dbc.InputGroup(
                    [dbc.InputGroupAddon("Almacenar:", addon_type="prepend"), dbc.Input(id="muestras",
                    placeholder="Indique Nro. de Muestras (Máximo 1000)")]
                ),
                    
            ]),
            
            
         ]),
         
         #Pestaña 2:
         dbc.Tab(label="Control", tab_id="", children=[
             
             
             dbc.Tabs([
                 
                 html.P("", className="card-text"),
                 
                 #CONTROL MANUAL
                 dbc.Tab(label="Control Manual", tab_id="", children= [
                     
                     html.P("", className="card-text"),
                     
                      dbc.Row(
                        [
                            #columna 1: Input Valvulas y Razones
                            dbc.Col([
                                
                                            html.Div(
                                    [
                                        dbc.Input(id="input-v1", placeholder="Valor Válvula 1", type="text"),
                                        html.P("", className="card-text"),
                                        #html.Br()
                                         
                                    ]
                                ),
                                            
                                html.P("", className="card-text"),
                                
                                 html.Div(
                                    [
                                        dbc.Input(id="input-v2", placeholder="Valor Válvula 2", type="text"),
                                        html.P("", className="card-text"),
                                        #html.Br(),
                                        
                                    ]
                                ),
                                 
                                 html.P("", className="card-text"),
                                 
                                 html.Div(
                                    [
                                        dbc.Input(id="input-r1", placeholder="Valor Razón 1", type="text"),
                                        html.P("", className="card-text"),
                                        #html.Br(),
                                        
                                    ]
                                ),
                                 
                                 html.P("", className="card-text"),
                                 
                                 html.Div(
                                    [
                                        dbc.Input(id="input-r2", placeholder="Valor Razón 2", type="text"),
                                        html.P("", className="card-text"),
                                        #html.Br(),
                                        
                                    ]
                                ),
                                     
                            ]),
                            
                            #columna 2: Botones Valvulas y Razones
                            dbc.Col([
                                
                                #boton 1
                                 html.Div(
                                    [
                                        dbc.Button(
                                            "Cambiar Válvula 1", color="primary",id="set-v1", className="mr-2", n_clicks=0
                                        ),
                                        html.Span(id="set-manual-v1", style={'display':'none',"verticalAlign": "middle"}),
                                        html.Span(id="v1-out", style={"verticalAlign": "middle"}),
                                    ]
                                    ),
                                 html.P("", className="card-text"),
                                 html.P("", className="card-text"),
                                 
                                 html.Div(
                                    [
                                        dbc.Button('Cambiar Válvula 2', color="primary", className="mr-1",id='set-v2', n_clicks=0),
                                        html.Span(id="set-manual-v2", style={'display':'none',"verticalAlign": "middle"}),
                                        html.Span(id="v2-out", style={"verticalAlign": "middle"}),
                                    ]
                                    ),
                                 html.P("", className="card-text"),
                                 html.P("", className="card-text"),
                                 
                                 html.Div(
                                    [
                                        dbc.Button('Cambiar Razón 1', color="dark", className="mr-1",id='set-r1', n_clicks=0), 
                                        html.Span(id="set-manual-r1", style={'display':'none',"verticalAlign": "middle"}),
                                        html.Span(id="r1-out", style={"verticalAlign": "middle"}),
                                    ]
                                    ),
                                 
                                 html.P("", className="card-text"),
                                 html.P("", className="card-text"),
                                 
                                 html.Div(
                                    [
                                        dbc.Button('Cambiar Razón 2', color="dark", className="mr-1",id='set-r2', n_clicks=0), 
                                        html.Span(id="set-manual-r2", style={'display':'none',"verticalAlign": "middle"}),
                                        html.Span(id="r2-out", style={"verticalAlign": "middle"}),
                                    ]
                                    ),
                    
                                
                            ]),
                                   
                            
                    ]),
                     
                     
                  html.P("", className="card-text"),
                  
                 # Grafico del voltaje aplicado a las valvulas
                 html.P("", className="card-text"),
                 
                 html.H3(["Voltaje Aplicado a las Válvulas"]),
                 
                 html.Div(id='get-valvulas-plot', style={'display':'none','color': colors['text2']}),
                 
                 dcc.Graph(id='live-valvululas-plot'),
                
                 html.P("", className="card-text")
                 
    
                 ]), #fin control manual
                 
                 
                 
                 #CONTROL AUTOMATICO
                 dbc.Tab(label="Control Automático", tab_id="", children= [
                     
                     html.P("", className="card-text"),
                     
                     #MODO AUTOMATICO: ENCENDER
                     html.H4(["Activar Control Automático"]),
                     
                     html.Div(
                       [
                           dbc.Button('Encender/Apagar', color="dark", className="mr-1",id='on_control_auto', n_clicks=0), 
                           html.Span(id="state_control", style={"verticalAlign": "middle"}),
                           #html.Span(id="set-manual-r2", style={'display':'none',"verticalAlign": "middle"}),
                           #html.Span(id="r2-out", style={"verticalAlign": "middle"}),
                       ]
                       ),
                     

                    
                    html.P("", className="card-text"),
                    html.P("", className="card-text"),
                     
                     html.H4(["Ingresar Referencia"]),
                     
                     html.P("", className="card-text"),
                     
                     dbc.Row(
                        [
                            #columna 1: Referencias
                            dbc.Col([
                                
                                #inputs referencias
                                 dbc.InputGroup(
                                    [dbc.InputGroupAddon("Tanque 1:", addon_type="prepend"), dbc.Input(id="ref-t1",
                                    placeholder="Referencia Tanque 1")]
                                ),
                                 
                                 html.P("", className="card-text"),
                                 
                                 dbc.InputGroup(
                                    [dbc.InputGroupAddon("Tanque 2:", addon_type="prepend"), dbc.Input(id="ref-t2",
                                    placeholder="Referencia Tanque 2")]
                                ),
                                 
                                 html.P("", className="card-text"),
                                 
                                
                                #Parametros controlador pid
                                html.H4(["Parámetros Controlador PID"]),
                                
                                html.P("", className="card-text"),
                                 
                                 dbc.InputGroup(
                                    [dbc.InputGroupAddon("Kp 1:", addon_type="prepend"), dbc.Input(id="pid-kp1",
                                    placeholder="Acción Proporcional")]
                                ),
                                 
                                 html.P("", className="card-text"),
                                 
                                 dbc.InputGroup(
                                    [dbc.InputGroupAddon("Kd 1:", addon_type="prepend"), dbc.Input(id="pid-kd1",
                                    placeholder="Acción Derivativa")]
                                ),
                                 
                                 html.P("", className="card-text"),
                                 
                                 dbc.InputGroup(
                                    [dbc.InputGroupAddon("Ki 1:", addon_type="prepend"), dbc.Input(id="pid-ki1",
                                    placeholder="Acción Integral")]
                                ),
                                 
                                 html.P("", className="card-text"),
                                 
                                 dbc.InputGroup(
                                    [dbc.InputGroupAddon("Kp 2:", addon_type="prepend"), dbc.Input(id="pid-kp2",
                                    placeholder="Acción Integral")]
                                ),
                                 
                                 html.P("", className="card-text"),
                                 
                                 dbc.InputGroup(
                                    [dbc.InputGroupAddon("Kd 2:", addon_type="prepend"), dbc.Input(id="pid-kd2",
                                    placeholder="Acción Integral")]
                                ),
                                 
                                 html.P("", className="card-text"),
                                 
                                 dbc.InputGroup(
                                    [dbc.InputGroupAddon("Ki 2:", addon_type="prepend"), dbc.Input(id="pid-ki2",
                                    placeholder="Acción Integral")]
                                ),
                                 
                                 html.P("", className="card-text"),
                                 
                                 dbc.InputGroup(
                                    [dbc.InputGroupAddon("AntiWindup 1:", addon_type="prepend"), dbc.Input(id="pid-windup1",
                                    placeholder="Ingresar Valor AntiWindup 1")]
                                ),
                                 
                                 html.P("", className="card-text"),
                                 
                                 dbc.InputGroup(
                                    [dbc.InputGroupAddon("AntiWindup 2:", addon_type="prepend"), dbc.Input(id="pid-windup2",
                                    placeholder="Ingresar Valor AntiWindup 2")]
                                ),
                                
                                
                                ]),
      
                            
                            #columna 2: botones
                            dbc.Col([
                                #boton 1
                                 html.Div(
                                    [
                                        dbc.Button(
                                            "Cambiar Ref. 1", color="warning",id="set-ref1", className="mr-2", n_clicks=0
                                        ),
                                        html.Span(id="b-output-ref1", style={'display':'none',"verticalAlign": "middle"}),
                                        html.Span(id="output-ref1", style={"verticalAlign": "middle"}),
                                    ]
                                    ),
                                 html.P("", className="card-text"),
                                 html.P("", className="card-text"),
                                 
                                 html.Div(
                                    [
                                        dbc.Button('Cambiar Ref. 2', color="warning", className="mr-1",id='set-ref2', n_clicks=0),
                                        html.Span(id="b-output-ref2", style={'display':'none',"verticalAlign": "middle"}),
                                        html.Span(id="output-ref2", style={"verticalAlign": "middle"}),
                                    ]
                                    ),
                                 html.P("", className="card-text"),
                                 html.P("", className="card-text"),
                                
                                
                                html.P("", className="card-text"),
                                
                                #botones controlador
                                html.H4("Botones Controlador"),
                                
                                html.P("", className="card-text"),
                                
                                html.Div(
                                    [
                                        dbc.Button('Cambiar Kp 1', color="info", className="mr-1",id='set-kp1', n_clicks=0),
                                        html.Span(id="b-output-kp1", style={'display':'none',"verticalAlign": "middle"}),
                                        html.Span(id="output-kp1", style={"verticalAlign": "middle"}),
                                    ]
                                    ),
                                 html.P("", className="card-text"),
                                 html.P("", className="card-text"),
                                 
                                 html.Div(
                                    [
                                        dbc.Button('Cambiar Kd 1', color="info", className="mr-1",id='set-kd1', n_clicks=0), 
                                        html.Span(id="b-output-kd1", style={'display':'none',"verticalAlign": "middle"}),
                                        html.Span(id="output-kd1", style={"verticalAlign": "middle"}),
                                    ]
                                    ),
                                 
                                 html.P("", className="card-text"),
                                 html.P("", className="card-text"),
                                 
                                 html.Div(
                                    [
                                        dbc.Button('Cambiar Ki 1', color="info", className="mr-1",id='set-ki1', n_clicks=0), 
                                        html.Span(id="b-output-ki1", style={'display':'none',"verticalAlign": "middle"}),
                                        html.Span(id="output-ki1", style={"verticalAlign": "middle"}),
                                    ]
                                    ),
                                 
                                 html.P("", className="card-text"),
                                 html.P("", className="card-text"),
                                 
                                 html.Div(
                                    [
                                        dbc.Button('Cambiar Kp 2', color="info", className="mr-1",id='set-kp2', n_clicks=0), 
                                        html.Span(id="b-output-kp2", style={'display':'none',"verticalAlign": "middle"}),
                                        html.Span(id="output-kp2", style={"verticalAlign": "middle"}),
                                    ]
                                    ),
                                 
                                 html.P("", className="card-text"),
                                 html.P("", className="card-text"),
                                 
                                 html.Div(
                                    [
                                        dbc.Button('Cambiar Kd 2', color="info", className="mr-1",id='set-kd2', n_clicks=0), 
                                        html.Span(id="b-output-kd2", style={'display':'none',"verticalAlign": "middle"}),
                                        html.Span(id="output-kd2", style={"verticalAlign": "middle"}),
                                    ]
                                    ),
                                 
                                 html.P("", className="card-text"),
                                 html.P("", className="card-text"),
                                 
                                 html.Div(
                                    [
                                        dbc.Button('Cambiar Ki 2', color="info", className="mr-1",id='set-ki2', n_clicks=0), 
                                        html.Span(id="b-output-ki2", style={'display':'none',"verticalAlign": "middle"}),
                                        html.Span(id="output-ki2", style={"verticalAlign": "middle"}),
                                    ]
                                    ),
                                 
                                 html.P("", className="card-text"),
                                 html.P("", className="card-text"),
                                 
                                 html.Div(
                                    [
                                        dbc.Button('Cambiar AntiWindup 1', color="info", className="mr-1",id='set-windup1', n_clicks=0), 
                                        html.Span(id="b-output-windup1", style={'display':'none',"verticalAlign": "middle"}),
                                        html.Span(id="output-windup1", style={"verticalAlign": "middle"}),
                                    ]
                                    ),
                                 
                                 html.P("", className="card-text"),
                                 html.P("", className="card-text"),
                                 
                                 html.Div(
                                    [
                                        dbc.Button('Cambiar AntiWindup 2', color="info", className="mr-1",id='set-windup2', n_clicks=0), 
                                        html.Span(id="b-output-windup2", style={'display':'none',"verticalAlign": "middle"}),
                                        html.Span(id="output-windup2", style={"verticalAlign": "middle"}),
                                    ]
                                    ),
                                
  
                            ]), #fin col
                            
                        ]), #fin row
                 
                     
                     
                     ]) #fin control automático
                 
             ]) #fin tabs
         
         ]) #fin pestaña 2
     
    ]) #fin tabs principales
         
]) #fin app layout
          

#FUNCIONES              
                            
'''    callback 
funciona monitoreando la clase Dash, al actiarse ejecuta la funcion ubicada debajo de ella
para ser activada chequea lo que ocurre con sus inputs, donde el primer valor es el id asociado
y el segundo es el parametro de interes a leer (parametro entregado a la funcion a ejecutar).
Al entrar en la funcion retornara lo definido a la seccion indicada en output, donde el primer 
parametro es el id de la seccion donde se retornara y el segundo es el paramtro en el cual se retornara

* funciones con input interval-component se actualizan con el avance del "clock"
'''

#obtiene valores de las alturas de los tanques
@app.callback(Output('get-alturas', 'children'), [Input('interval-component', 'n_intervals')]) #actualización periodica
def Get_Alturas(n):
    #global evento
    # Se actualiza con el clock el estado de las alturas de los tanques
    h1 = cliente.alturas['H1'].get_value()
    h2 = cliente.alturas['H2'].get_value()
    h3 = cliente.alturas['H3'].get_value()
    h4 = cliente.alturas['H4'].get_value()
    alturas = {'h1':h1, 'h2': h2, 'h3': h3, 'h4': h4}
    return json.dumps(alturas)
                            

#obtener valores de las valvulas para graficar
@app.callback(Output('get-valvulas-plot', 'children'), [Input('interval-component', 'n_intervals')]) #actualización periodica
def Get_Valvulas(n):
    
    
    valv1=cliente.valvulas['valvula1'].get_value()
    valv2=cliente.valvulas['valvula2'].get_value()
    
    valvulas = {'v1':valv1, 'v2': valv2}
    
    return json.dumps(valvulas)

                        

# Se actualiza el texto que indica la altura de los tanques en la interfaz
@app.callback(Output('update-alturas', 'children'), [Input('get-alturas', 'children')])
def UpdateText(alturas):
    alturas = json.loads(alturas)
    
    return [
        
        dash_table.DataTable(
                    #id='table_alturas',
                    columns=[
                        {'name': 'Altura Actual Tanque 1 (cm)', 'id': 'Altura Actual Tanque 1','type':'numeric', 'editable':False},
                        {'name': 'Altura Actual Tanque 2 (cm)', 'id': 'Altura Actual Tanque 2','type':'numeric', 'editable':False},
                        {'name': 'Altura Actual Tanque 3 (cm)', 'id': 'Altura Actual Tanque 3','type':'numeric', 'editable':False},
                        {'name': 'Altura Actual Tanque 4 (cm)', 'id': 'Altura Actual Tanque 4','type':'numeric', 'editable':False}
                        
                    ],
                        
    
                    data=[
                        {
                            
                            "Altura Actual Tanque 1": round(alturas['h1'], 2),
                            "Altura Actual Tanque 2": round(alturas['h2'], 2),
                            "Altura Actual Tanque 3": round(alturas['h3'], 2),
                            "Altura Actual Tanque 4": round(alturas['h4'], 2),
                            
                            
                            }
                        ]
                    
                ),
        
    ]

#GRÁFICOS alturas
@app.callback(Output('live-graph-tank', 'figure'), [Input('get-alturas', 'children')])
def UpdateGraph(alturas):
    
    global h1,h2,h3,h4
    global axis_time
    
    alturas = json.loads(alturas)
    axis_time.append(datetime.datetime.now())
    
    # Alturas estanques
    h1.append(alturas['h1'])
    h2.append(alturas['h2'])
    h3.append(alturas['h3'])
    h4.append(alturas['h4'])

    # Graficos de cada estanque para mostrar en tiempo real
    plot1 = go.Scatter(x=list(axis_time), y=list(h1), name='Tanque 1', mode='lines')
    plot2 = go.Scatter(x=list(axis_time), y=list(h2), name='Tanque 2', mode='lines')
    plot3 = go.Scatter(x=list(axis_time), y=list(h3), name='Tanque 3', mode='lines')
    plot4 = go.Scatter(x=list(axis_time), y=list(h4), name='Tanque 4', mode='lines')

    #Matriz 2x2 para 4 gráficos
    fig = plotly.tools.make_subplots(rows=2, cols=2, vertical_spacing=0.3, horizontal_spacing=0.1,
                                     subplot_titles=('Altura Tanque 3', 'Altura Tanque 4', 'Altura Tanque 1', 'Altura Tanque 2'), print_grid=True)
    
    #Estilo
    fig['layout']['margin'] = {
        'l': 10, 'r': 10, 'b': 30, 't': 30
    }
    fig['layout']['legend'] = {'x': -0.1, 'y': 1, 'xanchor': 'right'}
    fig['layout']['plot_bgcolor'] = colors['gris-claro']
    fig['layout']['paper_bgcolor'] = colors['background1']
    fig['layout']['font']['color'] = colors['text2']
    
    fig.update_layout(legend_title_text = "Leyenda:")
    fig.update_xaxes(title_text="hhh:mm:ss")
    fig.update_yaxes(title_text="centímetros")
    
    # se agregan los 4 graficos a los espacios asignados en las subfiguras
    fig.append_trace(plot3, 1, 1)
    fig.append_trace(plot4, 1, 2)
    fig.append_trace(plot1, 2, 1)
    fig.append_trace(plot2, 2, 2)
    
    return fig     


#obtener inputs control manual de la interfaz
@app.callback(Output('set-manual-v1', 'children'), [Input('input-v1','value')]) 
def Get_ManualV1(value):
    
    global v1_m
    
    if value!=None: 
        v1_m= float(value)
    
    return value

@app.callback(Output('set-manual-v2', 'children'), [Input('input-v2','value')]) 
def Get_ManualV2(value):
    
    global v2_m
    
    if value!=None:
        v2_m= float(value)
    
    return value

@app.callback(Output('set-manual-r1', 'children'), [Input('input-r1','value')]) 
def Get_ManualR1(value):
    
    global r1_m
    
    if value!=None:
        r1_m= float(value)
    
    return value

@app.callback(Output('set-manual-r2', 'children'), [Input('input-r2','value')]) 
def Get_ManualR2(value):
    
    global r2_m
    
    if value!=None:
        r2_m= float(value)
    
    return value


#cambiar valores control manual
@app.callback(Output('v1-out', 'children'), [Input('set-v1', 'n_clicks')]) 
def Set_ManualV1(n):
    
    #global v1_m
    
    if n is None:
        return ""
    else:
        
        cliente.valvulas['valvula1'].set_value(v1_m)
        
        return f"Valor Actualizado a {v1_m}"

@app.callback(Output('v2-out', 'children'), [Input('set-v2', 'n_clicks')]) 
def Set_ManualV2(n):
        
    if n is None:
        return ""
    else:
        
        cliente.valvulas['valvula2'].set_value(v2_m)
        
        return f"Valor Actualizado a {v2_m}"

@app.callback(Output('r1-out', 'children'), [Input('set-r1', 'n_clicks')]) 
def Set_ManualR1(n):
    
    
    if n is None:
        return ""
    else:
        
        cliente.razones['razon1'].set_value(r1_m)
        
        return f"Valor Actualizado a {r1_m}"
    
@app.callback(Output('r2-out', 'children'), [Input('set-r2', 'n_clicks')]) 
def Set_ManualR2(n):
    
    
    if n is None:
        return ""
    else:
        
        cliente.razones['razon2'].set_value(r2_m)
        
        return f"Valor Actualizado a {r2_m}"


#Gráfico Voltajes de las Válvulas
@app.callback(Output('live-valvululas-plot', 'figure'), [Input('get-valvulas-plot', 'children')])
def ValvulasPlot(valvulas):
    
    global valv_1, valv_2
    global axis_time_v
    
    valvulas= json.loads(valvulas)
    axis_time_v.append(datetime.datetime.now())
    
    valv_1.append(valvulas['v1'])
    valv_2.append(valvulas['v2'])
    
    plot_v1= go.Scatter(x=list(axis_time_v), y=list(valv_1), name='Valvula 1', mode='lines')
    plot_v2= go.Scatter(x=list(axis_time_v), y=list(valv_2), name='Valvula 2', mode='lines')
    
    fig= go.Figure()
    
    fig['layout']['margin'] = {
        'l': 10, 'r': 10, 'b': 30, 't': 30
    }
    fig['layout']['legend'] = {'x': -0.1, 'y': 1, 'xanchor': 'right'}
    fig['layout']['plot_bgcolor'] = colors['gris-claro']
    fig['layout']['paper_bgcolor'] = colors['background1']
    fig['layout']['font']['color'] = colors['text2']
    
    fig.update_layout(legend_title_text = "Leyenda:")
    fig.update_xaxes(title_text="hhh:mm:ss")
    fig.update_yaxes(title_text="Voltaje")
    
    
    fig.add_trace(plot_v1)
    fig.add_trace(plot_v2)
    
    
    return fig
    


# Evento Alarma mediante OPC

#De acuerdo con el archivo 'TanquesNamespace' el evento alarma se activa
#cuando el nivel del tanque es inferior a 10 cm (L151-153)
#El formato del msje de la alarma también fue extraído de allí.

@app.callback(Output('Alarm-msje', 'children'), [Input('interval-component', 'n_intervals')])
def AlarmaMsje(n):
    
    global eventoAlarm 
    
    msje_t1= ''
    msje_t2=''
    msje_t3=''
    msje_t4=''
    
    if eventoAlarm!=0: #si es != de 0 entonces quiere decir que el tipo de evento es la alarma.
        
        mensaje= eventoAlarm.Message.Text.split(':')
        
        estado_alarma = 'Alarma Activa'
        aviso = "danger"
        text_t1='Tanque 1{}'
        text_t2='Tanque 2{}'
        text_t3='Tanque 3{}'
        text_t4='Tanque 4{}'
        
        count_1=0
        count_2=0
        count_3=0
        count_4=0
        
        #agregar mensaje del tanque donde ocurrio la alarma y el nivel actual.
        if int(mensaje[1][7]) == 1:
            msje_t1 = ': altura={}[cm]'.format(round(float(mensaje[2]),2))
            count_1+=1
            
        
        if int(mensaje[1][7]) == 2:
        
            msje_t2 = ': altura={}[cm]'.format(round(float(mensaje[2]),2))
            count_2+=1
 
        
        if int(mensaje[1][7]) == 3:

            msje_t3 = ': altura={}[cm]'.format(round(float(mensaje[2]),2))
            count_3+=1
            
        
        if int(mensaje[1][7]) == 4:
            msje_t4 = ': altura={}[cm]'.format(round(float(mensaje[2]),2))
            count_4+=1
            
        
        if count_1 ==0:
            text_t1 =''
            
        if count_2 ==0:
            text_t2 =''
            
        if count_3 ==0:
            text_t3 =''
            
        if count_4 ==0:
            text_t4 =''
            
    
    else: #no exite evento no asociado a alarma
        estado_alarma = 'Alarma Inactiva'
        aviso = "success"
        text_t1=''
        text_t2=''
        text_t3=''
        text_t4=''
        
    
    eventoAlarm=0

    
    return [
                
                dbc.Badge('{}'.format(estado_alarma) ,color=aviso, className="mr-1"),
                html.Span(text_t1.format(msje_t1)),
                html.Span(text_t2.format(msje_t2)),
                html.Span(text_t3.format(msje_t3)),
                html.Span(text_t4.format(msje_t4))
            ]
        

    
    
####funciones control automático
@app.callback(Output('state_control', 'children'), [Input('on_control_auto', 'n_clicks')]) 
def ModoControl(n):
    
        
    if n is None:
        return ""
    
    elif (n%2)==0:
        cliente.modo_automatico = False
        
    else:
        cliente.modo_automatico=True
        #cliente.control_automatico()
        
    estado_control = cliente.modo_automatico
    
    return f"Control Automático {estado_control}"


# #funciones referencias-guardar input
@app.callback(Output('b-output-ref1', 'children'), [Input('ref-t1', 'value')]) 
def SetRef1(value):
    
    global r1
    
    if value!=None:
        r1= float(value)
        
    return value
        
    
@app.callback(Output('b-output-ref2', 'children'), [Input('ref-t2', 'value')]) 
def SetRef2(value):
    global r2
    
    if value!=None:
        r2= float(value)
        
    return value


# #funciones parametros controlador
@app.callback(Output('b-output-kp1', 'children'), [Input('pid-kp1', 'value')]) 
def SetKp1(value):
    global kp1
    
    if value!=None:
        kp1= float(value)
        
    return value

@app.callback(Output('b-output-kd1', 'children'), [Input('pid-kd1', 'value')]) 
def SetKd1(value):
    global kd1
    
    if value!=None:
        kd1= float(value)
        
    return value

@app.callback(Output('b-output-ki1', 'children'), [Input('pid-ki1', 'value')]) 
def SetKi1(value):
    global ki1
    
    if value!=None:
        ki1= float(value)
        
    return value


@app.callback(Output('b-output-kp2', 'children'), [Input('pid-kp2', 'value')]) 
def SetKp2(value):
    global kp2
    
    if value!=None:
        kp2= float(value)
        
    return value

@app.callback(Output('b-output-kd2', 'children'), [Input('pid-kd2', 'value')]) 
def SetKd2(value):
    global kd2
    
    if value!=None:
        kd2= float(value)
        
    return value

@app.callback(Output('b-output-ki2', 'children'), [Input('pid-ki2', 'value')]) 
def SetKi2(value):
    global ki2
    
    if value!=None:
        ki2= float(value)
        
    return value

@app.callback(Output('b-output-windup1', 'children'), [Input('pid-windup1', 'value')]) 
def SetAntiwindup1(value):
    global windup1
    
    if value!=None:
        windup1= float(value)
        
    return value

@app.callback(Output('b-output-windup2', 'children'), [Input('pid-windup2', 'value')]) 
def SetAntiwindup2(value):
    global windup2
    
    if value!=None:
        windup2= float(value)
        
    return value

# ######BOTONES CONTROLADOR
# #funciones referencias
@app.callback(Output('output-ref1', 'children'), [Input('set-ref1', 'n_clicks')]) 
def BSetRef1(n):
    
    if n is None:
        return ""
    else:
        cliente.ref1 = r1
        return f"Valor Actualizado a {r1}"
    
@app.callback(Output('output-ref2', 'children'), [Input('set-ref2', 'n_clicks')]) 
def BSetRef2(n):
    
    if n is None:
        return ""
    else:
        cliente.ref2 = r2
        
        return f"Valor Actualizado a {r2}"


# #funciones parametros controlador
@app.callback(Output('output-kp1', 'children'), [Input('set-kp1', 'n_clicks')]) 
def BSetKp1(n):
    
    if n is None:
        return ""
    else:
        cliente.kp1= kp1
        
        return f"Valor Actualizado a {kp1}"

@app.callback(Output('output-kd1', 'children'), [Input('set-kd1', 'n_clicks')]) 
def BSetKd1(n):
    
    if n is None:
        return ""
    else:
        cliente.kd1= kd1
        
        return f"Valor Actualizado a {kd1}"

@app.callback(Output('output-ki1', 'children'), [Input('set-ki1', 'n_clicks')]) 
def BSetKi1(n):
    
    if n is None:
        return ""
    else:
        cliente.ki1= ki1
        
        return f"Valor Actualizado a {ki1}"


@app.callback(Output('output-kp2', 'children'), [Input('set-kp2', 'n_clicks')]) 
def BSetKp2(n):
    
    if n is None:
        return ""
    else:
        cliente.kp2= kp2
        
        return f"Valor Actualizado a {kp2}"

@app.callback(Output('output-kd2', 'children'), [Input('set-kd2', 'n_clicks')]) 
def BSetKd2(n):
    
    if n is None:
        return ""
    else:
        cliente.kd2= kd2
        
        return f"Valor Actualizado a {kd2}"

@app.callback(Output('output-ki2', 'children'), [Input('set-ki2', 'n_clicks')]) 
def BSetKi2(n):
    
    if n is None:
        return ""
    else:
        cliente.ki2= ki2
        
        return f"Valor Actualizado a {ki2}"


@app.callback(Output('output-windup1', 'children'), [Input('set-windup1', 'n_clicks')]) 
def BSetWindUp1(n):
    
    if n is None:
        return ""
    else:
        cliente.windup1= windup1
        
        return f"Valor Actualizado a {windup1}"

@app.callback(Output('output-windup2', 'children'), [Input('set-windup2', 'n_clicks')]) 
def BSetWindUp2(n):
    
    if n is None:
        return ""
    else:
        cliente.windup2= windup2
        
        return f"Valor Actualizado a {windup2}"

#GUARDAR DATOS
@app.callback(Output('output-muestras', 'children'), [Input('muestras', 'value')]) 
def Muestras(value):
    
    global muestras
    
    if value is None:
        return''
        
    else:
    
        muestras= int(value)
        
        return muestras

#formato
@app.callback(Output("output-formato", "children"),Input("formato", "value"))
def on_form_change(format_value):
    global formato_save
    
    formato_save=format_value
    
    return formato_save
    
#accion guardar muestras
@app.callback(Output('output-save', 'children'), [Input('save-data', 'n_clicks')]) 
def BotonData(n):
    
    if n is None:
        return ""
    
    elif n ==0:
        return ""
    
    else:
    
        nombre= 'muestras-guardadas.'+ formato_save
        f=open(nombre,'w')
        
        listas_h = [h1,h2,h3,h4,axis_time]
        
        for i in range(5):
            
            lista_aux=[]
            n_datos= len(listas_h[i])
            
            if (i<4):
                f.write("Tanque" + str(i+1)+ ":\n")
            else:
                f.write("Tiempo:\n")
                
            lista_aux= listas_h[i]
            
            if (n_datos > muestras):    
                
                lista_rec=[]
                lista_rec= list(itertools.islice(lista_aux,(n_datos-muestras),n_datos))
                #lista_aux[n_datos-muestras:]
                texto= ",".join(str(x) for x in lista_rec)
                f.write(texto + "\n")
                
                
            else:
    
                texto= ",".join(str(x) for x in list(lista_aux))
                f.write(texto + "\n")
                
        f.close()
        
        return f"Datos Guardados! ({n})" 
            
        

#MAIN: run app               
if __name__ == "__main__":
    
    eventoAlarm=0
    
    # Se instancia el cliente para establever la comunicacion con el servidor,
    # suscribiendo de inmediato a la alarma
    cliente = Cliente("opc.tcp://localhost:4840/freeopcua/server/", suscribir_eventos=True, SubHandler=SubHandler)
    cliente.conectar()
    # Variables para graficos de tanques
    axis_time = deque(maxlen=1000)
    h1 = deque(maxlen=1000)
    h2 = deque(maxlen=1000)
    h3 = deque(maxlen=1000)
    h4 = deque(maxlen=1000)
    valv_1=deque(maxlen=100)
    valv_2=deque(maxlen=100)
    axis_time_v=deque(maxlen=100)
    v1_m= cliente.valvulas['valvula1'].get_value()
    v2_m= cliente.valvulas['valvula2'].get_value()
    r1_m= cliente.razones['razon1'].get_value()
    r2_m= cliente.razones['razon2'].get_value()
    r1= cliente.alturas['H1'].get_value()
    r2= cliente.alturas['H2'].get_value()
    kp1=50
    kd1=0
    ki1=100
    kp2=50
    kd2=0
    ki2=100
    windup1=0
    windup2=0
    formato_save=''
    muestras=0
    
    app.run_server(debug=True)   
