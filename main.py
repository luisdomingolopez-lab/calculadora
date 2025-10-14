import os
import json # Nuevo módulo para persistencia
from datetime import datetime, date
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, ListProperty, BooleanProperty
from kivy.lang import Builder
from kivy import platform
from kivy.core.window import Window 

# Asegurar que el diseño sea más compacto si se ejecuta en PC
if platform != 'android':
    Window.size = (350, 650)

# --- CONFIGURACIÓN DE RUTA DE DATOS (CRÍTICO para JSON) ---

DB_FILE = "tasa_data.json" # Nombre del archivo JSON

# --- Funciones de Persistencia JSON ---

def load_data():
    """Carga los datos del archivo JSON o devuelve una lista vacía."""
    if not os.path.exists(DB_FILE):
        return []
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []
        except Exception:
            return []

def save_data(data):
    """Guarda la lista de datos en el archivo JSON."""
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def get_next_id(data):
    """Obtiene el siguiente ID consecutivo para nuevos registros."""
    return max([item.get('id', 0) for item in data], default=0) + 1

# Inicialización mínima: asegura que el archivo exista con una tasa por defecto si está vacío
def json_init_check():
    data = load_data()
    if not data:
        # Crea una tasa inicial si el archivo está vacío
        guardar_nueva_tasa(1.0)

def obtener_tasa_activa():
    """Obtiene la última tasa activa (el primer registro en la lista)."""
    data = load_data()
    return data[0]['tasa'] if data else None

def obtener_todas_las_tasas():
    """Devuelve la lista completa de registros en formato de tupla (ID, fecha, tasa)."""
    data = load_data()
    # Mantiene el formato de tupla que Kivy esperaba de SQLite
    return [(item['id'], item['fecha'], item['tasa']) for item in data]

def guardar_nueva_tasa(nueva_tasa: float):
    """Guarda una nueva tasa al inicio de la lista."""
    data = load_data()
    
    nuevo_registro = {
        "id": get_next_id(data),
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tasa": nueva_tasa
    }
    
    # Añadir al inicio para que el más nuevo sea el primero
    data.insert(0, nuevo_registro)
    save_data(data)

def modificar_tasa(id_tasa: int, nuevo_valor: float):
    """Modifica el valor de la tasa por su ID."""
    data = load_data()
    encontrado = False
    for item in data:
        if item.get('id') == id_tasa:
            item['tasa'] = nuevo_valor
            encontrado = True
            break
    if encontrado:
        save_data(data)
        return True
    return False

def borrar_tasa(id_tasa: int):
    """Borra un registro por su ID."""
    data = load_data()
    len_antes = len(data)
    # Filtra la lista para excluir el ID dado
    data_nueva = [item for item in data if item.get('id') != id_tasa]
    
    if len(data_nueva) < len_antes:
        save_data(data_nueva)
        return True
    return False

# --- ESTRUCTURA DE INTERFAZ KIVY (Lenguaje KV) ---

KV = """
<MainLayout>:
    orientation: 'vertical'
    spacing: '10dp'
    padding: '10dp'
    
    # ---------------------- TASA ACTIVA ----------------------
    BoxLayout:
        orientation: 'vertical'
        size_hint_y: None
        height: '80dp'
        Label:
            text: 'TASA ACTIVA HOY'
            font_size: '20sp'
            size_hint_y: None
            height: '30dp'
        Label:
            text: root.tasa_activa_text
            font_size: '35sp'
            color: 0.1, 0.5, 0.1, 1 # Verde
            bold: True
    
    # ---------------------- SECCIÓN DE CONVERSIÓN ----------------------
    BoxLayout:
        orientation: 'vertical'
        spacing: '5dp'
        padding: '10dp'
        size_hint_y: None
        height: '240dp' 
        canvas.before:
            Color:
                rgba: 0.95, 0.95, 0.95, 1
            Rectangle:
                pos: self.pos
                size: self.size
        
        Label:
            text: 'CONVERSIÓN'
            font_size: '18sp'
            color: 0, 0, 0, 1
            size_hint_y: None
            height: '30dp'
            
        # BOTÓN PARA INVERTIR EL CÁLCULO
        Button:
            text: root.inversion_button_text 
            size_hint_y: None
            height: '40dp'
            background_color: 0.1, 0.1, 0.5, 1 # Azul distintivo
            on_release: root.toggle_inversion()
                
        BoxLayout:
            size_hint_y: None
            height: '40dp'
            Label:
                id: input_label
                text: root.input_label_text # Dinámico: 'Monto BS:' o 'Monto USD:'
                size_hint_x: 0.3
                color: 0, 0, 0, 1
            TextInput:
                id: monto_input
                multiline: False
                input_type: 'number'
                hint_text: '0.00'
                size_hint_x: 0.7
                on_text_validate: root.calcular_conversion()

        BoxLayout:
            size_hint_y: None
            height: '40dp'
            Label:
                id: result_label
                text: root.result_label_text # Dinámico: 'Monto USD:' o 'Monto BS:'
                size_hint_x: 0.3
                color: 0, 0, 0, 1
            Label:
                id: final_result
                text: root.final_result_text
                size_hint_x: 0.7
                font_size: '25sp'  
                bold: True          
                color: 0.1, 0.5, 0.1, 1 # Color verde

        Button:
            text: 'CALCULAR'
            size_hint_y: None
            height: '40dp'
            on_release: root.calcular_conversion()

    # ---------------------- SECCIÓN DE GESTIÓN ----------------------
    BoxLayout:
        orientation: 'vertical'
        spacing: '5dp'
        padding: '10dp'
        size_hint_y: 1
        canvas.before:
            Color:
                rgba: 0.85, 0.85, 0.85, 1
            Rectangle:
                pos: self.pos
                size: self.size

        Label:
            text: 'GESTIÓN DE TASA DIARIA'
            font_size: '16sp'
            color: 0, 0, 0, 1
            size_hint_y: None
            height: '30dp'

        Spinner:
            id: tasa_spinner
            text: 'Seleccione una Tasa'
            values: root.tasa_options
            on_text: root.tasa_seleccionada(self.text)
            size_hint_y: None
            height: '40dp'

        TextInput:
            id: valor_modificar_input
            multiline: False
            input_type: 'number'
            hint_text: 'Nuevo valor (Guardar/Modificar)'
            text: root.tasa_modificar_text
            size_hint_y: None
            height: '40dp'

        Label:
            text: 'ID seleccionado: ' + root.id_seleccionado
            id: id_label
            color: 0, 0, 0, 1
            size_hint_y: None
            height: '20dp'

        BoxLayout:
            size_hint_y: None
            height: '40dp'
            spacing: '5dp'
            Button:
                text: 'AGREGAR'
                on_release: root.guardar_nueva_tasa()
                background_color: 0, 0.7, 0, 1
                font_size: '12sp'
            Button:
                text: 'MODIFICAR'
                on_release: root.modificar_tasa()
                background_color: 0, 0, 0.7, 1
                font_size: '12sp'
            Button:
                text: 'BORRAR'
                on_release: root.borrar_tasa()
                background_color: 0.7, 0, 0, 1
                font_size: '12sp'
"""

class MainLayout(BoxLayout):
    # Kivy Properties
    tasa_activa_text = StringProperty("Cargando...")
    final_result_text = StringProperty("0.00")
    tasa_options = ListProperty([])
    tasa_modificar_text = StringProperty("")
    id_seleccionado = StringProperty("N/A")
    tasa_map = {} 
    
    # Propiedades para la inversión (Estado y Etiquetas)
    inversion_activa = BooleanProperty(False)
    input_label_text = StringProperty('Monto BS:') 
    result_label_text = StringProperty('Monto USD:')
    inversion_button_text = StringProperty("INVERTIR CÁLCULO (BS <--> USD)")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # --- CAMBIO CRÍTICO: NO SE NECESITA CONEXIÓN SQLITE ---
        # Inicializa el archivo JSON si es necesario
        json_init_check() 
        # Ya no se usa self.conn
            
        self.toggle_inversion_state(self.inversion_activa)
        self.actualizar_datos()
        
    # --- MÉTODOS DE CÁLCULO Y GESTIÓN (SIN EL PARÁMETRO 'conn') ---
        
    def toggle_inversion(self):
        """Invierte el estado de inversión al presionar el botón."""
        self.toggle_inversion_state(not self.inversion_activa)

    def toggle_inversion_state(self, active):
        """Actualiza el estado de inversión y las etiquetas."""
        self.inversion_activa = active
        
        if active:
            # Modo: USD a BS (Multiplicación)
            self.input_label_text = 'Monto USD:'
            self.result_label_text = 'Monto BS:'
        else:
            # Modo: BS a USD (División)
            self.input_label_text = 'Monto BS:'
            self.result_label_text = 'Monto USD:'
            
        # Limpiar resultados al cambiar el modo
        self.ids.monto_input.text = ""
        self.final_result_text = "0.00"

    def actualizar_datos(self):
        # 1. Tasa Activa (Llamada sin 'conn')
        tasa_actual = obtener_tasa_activa()
        self.tasa_activa_text = f"{tasa_actual:.2f}" if tasa_actual else "N/A"
        
        # 2. Opciones de Tasa (Spinner) (Llamada sin 'conn')
        tasas = obtener_todas_las_tasas()
        options = []
        self.tasa_map = {}
        for id_tasa, fecha, tasa_valor in tasas:
            display_text = f"ID: {id_tasa} | {fecha.split(' ')[0]} | Tasa: {tasa_valor:.2f}"
            options.append(display_text)
            self.tasa_map[display_text] = {'id': id_tasa, 'tasa': tasa_valor}
            
        self.tasa_options = options
        self.id_seleccionado = "N/A"
        self.tasa_modificar_text = ""
        self.ids.tasa_spinner.text = 'Seleccione una Tasa'

    def calcular_conversion(self):
        try:
            monto_input = float(self.ids.monto_input.text)
            tasa_actual = obtener_tasa_activa() # Llamada sin 'conn'
            
            if tasa_actual and monto_input >= 0:
                if self.inversion_activa:
                    result = monto_input * tasa_actual
                else:
                    result = monto_input / tasa_actual
                    
                self.final_result_text = f"{result:.2f}"
            else:
                self.final_result_text = "Error de Tasa"
                
        except ValueError:
            self.final_result_text = "Monto Inválido"

    def tasa_seleccionada(self, text):
        if text in self.tasa_map:
            data = self.tasa_map[text]
            self.id_seleccionado = str(data['id'])
            self.tasa_modificar_text = str(data['tasa'])
        else:
            self.id_seleccionado = "N/A"
            self.tasa_modificar_text = ""

    def guardar_nueva_tasa(self):
        try:
            nuevo_valor = float(self.ids.valor_modificar_input.text)
            if nuevo_valor > 0:
                guardar_nueva_tasa(nuevo_valor) # Llamada sin 'conn'
                self.actualizar_datos()
                self.ids.valor_modificar_input.text = ""
            else:
                print("Valor de tasa inválido")
        except ValueError:
            print("Entrada de valor inválida")

    def modificar_tasa(self):
        try:
            id_tasa = int(self.id_seleccionado)
            nuevo_valor = float(self.ids.valor_modificar_input.text)
            
            if self.id_seleccionado != "N/A" and nuevo_valor > 0:
                modificar_tasa(id_tasa, nuevo_valor) # Llamada sin 'conn'
                self.actualizar_datos()
            else:
                print("Debe seleccionar un ID y proveer un valor válido.")
        except ValueError:
            print("Valor o ID inválido.")
            
    def borrar_tasa(self):
        try:
            id_tasa = int(self.id_seleccionado)
            if self.id_seleccionado != "N/A":
                borrar_tasa(id_tasa) # Llamada sin 'conn'
                self.actualizar_datos()
            else:
                print("Debe seleccionar un ID para borrar.")
        except ValueError:
            print("ID inválido.")


class TasaApp(App):
    def build(self):
        Builder.load_string(KV)
        return MainLayout()

if __name__ == '__main__':
    TasaApp().run()