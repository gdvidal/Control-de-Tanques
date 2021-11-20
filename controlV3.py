from opcua import ua, Client
import threading
import time

def funcion_handler(node, val):
    key = node.get_parent().get_display_name().Text
    print('key: {} | val: {}'.format(key, val))

class SubHandler(object):

    """
    Subscription Handler. To receive events from server for a subscription
    data_change and event methods are called directly from receiving thread.
    Do not do expensive, slow or network operation there. Create another
    thread if you need to do such a thing
    """

    def datachange_notification(self, node, val, data):
        thread_handler = threading.Thread(target=funcion_handler, args=(node, val))  # Se realiza la descarga por un thread
        thread_handler.start()

    def event_notification(self, event):
        print("Python: New event", event)


class Cliente():
    def __init__(self, direccion, suscribir_eventos, SubHandler, modo = False):
        
        #crear thread aparte para la funcion "control automatico"
        self.thread_control = threading.Thread(target=self.control_automatico, daemon=True)
        
        self.direccion = direccion
        self.client = Client(direccion)
        self.alturas = {'H1': 0, 'H2': 0, 'H3':0, 'H4':0}
        self.temperaturas = {'T1': 0, 'T2': 0, 'T3':0, 'T4':0}
        self.valvulas = {'valvula1':0, 'valvula2':0}
        self.razones = {'razon1':0, 'razon2': 0}
        self.subscribir_eventos = suscribir_eventos
        self.periodo = 100 # cantidad de milisegundos para revisar las variables subscritas
        self.SubHandlerClass = SubHandler

        ###VARIABLES PARA EL CONTROL
        self.modo_automatico = modo
        self._ref1 = 0
        self._ref2 = 0

        self._volt_1 = 0
        self._volt_2 = 0
        self._gamma1 = 0
        self._gamma2 = 0
        self.kp1 = 0
        self.kp2 = 0
        self.kd1 = 0
        self.kd2 = 0
        self.ki1 = 0
        self.ki2 = 0
        self.windup1 = 100
        self.windup2 = 100

    def Instanciacion(self):
        self.root = self.client.get_root_node()
        self.objects = self.client.get_objects_node()
        self.Tanques = self.objects.get_child(['2:Proceso_Tanques','2:Tanques'])
        self.Valvulas = self.objects.get_child(['2:Proceso_Tanques', '2:Valvulas'])
        self.Razones = self.objects.get_child(['2:Proceso_Tanques', '2:Razones'])


        # Obtención de las alturas
        self.alturas['H1'] = self.Tanques.get_child(['2:Tanque1', '2:h'])
        self.alturas['H2'] = self.Tanques.get_child(['2:Tanque2', '2:h'])
        self.alturas['H3'] = self.Tanques.get_child(['2:Tanque3', '2:h'])
        self.alturas['H4'] = self.Tanques.get_child(['2:Tanque4', '2:h'])

        # Obtención de temperaturas
        self.temperaturas['T1'] = self.Tanques.get_child(['2:Tanque1', '2:T'])
        self.temperaturas['T2'] = self.Tanques.get_child(['2:Tanque2', '2:T'])
        self.temperaturas['T3'] = self.Tanques.get_child(['2:Tanque3', '2:T'])
        self.temperaturas['T4'] = self.Tanques.get_child(['2:Tanque4', '2:T'])

        # Obtención de los pumps
        self.valvulas['valvula1'] = self.Valvulas.get_child(['2:Valvula1', '2:u'])
        self.valvulas['valvula2'] = self.Valvulas.get_child(['2:Valvula2', '2:u'])

        # Obtención de los switches
        self.razones['razon1'] = self.Razones.get_child(['2:Razon1', '2:gamma'])
        self.razones['razon2'] = self.Razones.get_child(['2:Razon2', '2:gamma'])

        # Evento (alarma en este caso)
        if self.subscribir_eventos:
            self.myevent = self.root.get_child(["0:Types", "0:EventTypes", "0:BaseEventType", "2:Alarma_nivel"])#Tipo de evento
            self.obj_event = self.objects.get_child(['2:Proceso_Tanques', '2:Alarmas', '2:Alarma_nivel'])#Objeto Evento
            self.handler_event = self.SubHandlerClass()
            self.sub_event = self.client.create_subscription(self.periodo, self.handler_event)#Subscripción al evento
            self.handle_event = self.sub_event.subscribe_events(self.obj_event, self.myevent)




    def subscribir_cv(self): # Subscripción a las variables controladas
        self.handler_cv = self.SubHandlerClass()
        self.sub_cv = self.client.create_subscription(self.periodo, self.handler_cv)
        for key, var in self.alturas.items():
            self.sub_cv.subscribe_data_change(var)
        for key, var in self.temperaturas.items():
            self.sub_cv.subscribe_data_change(var)


    def subscribir_mv(self): # Subscripación a las variables manipuladas
        self.handler_mv = self.SubHandlerClass()
        self.sub_mv = self.client.create_subscription(self.periodo, self.handler_mv)
        for key, var in self.valvulas.items():
            self.sub_mv.subscribe_data_change(var)
        for key, var in self.razones.items():
            self.sub_mv.subscribe_data_change(var)


    def conectar(self):
        try:
            self.client.connect()
            self.objects = self.client.get_objects_node()
            print('Cliente OPCUA se ha conectado')
            self.Instanciacion()
            self.thread_control.start() #inicializa thread

        except:
            self.client.disconnect()
            print('Cliente no se ha podido conectar')

    def control_automatico(self):
        error_acumulado1 = 0
        error_acumulado2 = 0
        error_pasado1 = 0
        error_pasado2 = 0

        while True:

            if self.modo_automatico:
                

                error_1 = self.ref1 - self.alturas['H1'].get_value()
                error_2 = self.ref2 - self.alturas['H2'].get_value()

                error_acumulado1 += error_1
                error_acumulado2 += error_2

                if error_acumulado1 < - self.windup1:
                    error_acumulado1 = -self.windup1
                elif error_acumulado1 > self.windup1:
                    error_acumulado2 = self.windup1

                if error_acumulado2 < - self.windup2:
                    error_acumulado2 = -self.windup2
                elif error_acumulado2 > self.windup2:
                    error_acumulado2 = self.windup2


                error_diferencial1 = -(error_1 - error_pasado1)
                error_diferencial2 = -(error_2 - error_pasado2)

                salida1 = error_1 * self.kp1 + error_acumulado1 * self.ki1 + error_diferencial1 * self.kd1
                salida2 = error_2 * self.kp2 + error_acumulado2 * self.ki2 + error_diferencial2 * self.kd2

                self.volt_1 = salida1
                self.volt_2 = salida2

                error_pasado1 = error_1
                error_pasado2 = error_2

            time.sleep(self.periodo / 10000)

    @property
    def volt_1(self):
        return self.valvulas['valvula1'].get_value()

    @property
    def volt_2(self):
        return self.valvulas['valvula2'].get_value()

    @volt_1.setter
    def volt_1(self, value):
        if value is None:
            return
        if value < -1:
            #self.volt_1 = -1
            self.valvulas['valvula1'].set_value(-1)
        elif value > 1:
            #self.volt_1 = 1
            self.valvulas['valvula1'].set_value(1)
        else:
            #self.volt_1 = value
            self.valvulas['valvula1'].set_value(value)
            
            print("set value V1")

    @volt_2.setter
    def volt_2(self, value):
        if value is None:
            return
        if value < -1:
            #self.volt_2 = -1
            self.valvulas['valvula2'].set_value(-1)
        elif value > 1:
            #self.volt_2 = 1
            self.valvulas['valvula2'].set_value(1)
        else:
            #self.volt_2 = value
            self.valvulas['valvula2'].set_value(value)
            
            print("set value V2")


    @property
    def gamma1(self):
        return self.razones['razon1'].get_value()

    @property
    def gamma2(self):
        return self.razones['razon2'].get_value()

    @gamma1.setter
    def gamma1(self, value):
        if value is None:
            return
        if value < 0:
            #self.gamma1 = 0
            self.razones['razon1'].set_value(0)
        elif value > 1:
            #self.gamma1 = 1
            self.razones['razon1'].set_value(1)
        else:
            #self.gamma1 = value
            self.razones['razon1'].set_value(value)

    @gamma2.setter
    def gamma2(self, value):
        if value is None:
            return
        if value < 0:
            #self.gamma2 = 0
            self.razones['razon2'].set_value(0)
        elif value > 1:
            #self.gamma2 = 1
            self.razones['razon2'].set_value(1)
        else:
            #self.gamma2 = value
            self.razones['razon2'].set_value(value)

    @property
    def ref1(self):
        return self._ref1
    @ref1.setter
    def ref1(self, value):
        
        if value is None:
            return
        if value < 0:
            self._ref1 = 0
        else:
            self._ref1 = value
            
            print("set ref1")

    @property
    def ref2(self):
        return self._ref2

    @ref2.setter
    def ref2(self, value):
        print(value)
        if value is None:
            return
        if value < 0:
            self._ref2 = 0
        else:
            self._ref2 = value





#cliente = Cliente("opc.tcp://localhost:4840/freeopcua/server/", suscribir_eventos=True, SubHandlerClass=SubHandler)
#cliente.conectar()
#cliente.subscribir_mv() # Se subscribe a las variables manipuladas
