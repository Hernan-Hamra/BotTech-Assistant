import warnings # Importa el módulo 'warnings' para controlar los mensajes de advertencia.
from google.adk import Agent # Importa la clase 'Agent' del SDK de Gemini (ADK - Agent Development Kit).
from .config import Config # Importa la clase Config desde el módulo de configuración local.
from .prompts import GLOBAL_INSTRUCTION, INSTRUCTION # Importa las instrucciones globales y específicas del agente.
from .shared_libraries.callbacks import ( # Importa funciones de callback (funciones que se ejecutan en ciertos momentos).
    rate_limit_callback, # Callback para manejar límites de tasa (previene exceso de llamadas a la API).
    before_agent,      # Callback que se ejecuta antes de que el agente procese una solicitud.
    before_tool,       # Callback que se ejecuta antes de que una herramienta sea invocada.
    after_tool         # Callback que se ejecuta después de que una herramienta ha terminado su ejecución.
)
from .tools.tools import (
    search_products,
    add_item_to_quote,
    view_quote,
    remove_item_from_quote,
    clear_quote
)

# Filtra las advertencias de usuario relacionadas con el módulo 'pydantic'.
# Esto es común en entornos de desarrollo para suprimir mensajes que no afectan la funcionalidad.
warnings.filterwarnings("ignore", category=UserWarning, module=".*pydantic.*")

# Instancia la clase Config para cargar la configuración del agente desde el archivo de configuración.
configs = Config()

# Define e inicializa la instancia principal del Agente (BotTech Assistant).
root_agent = Agent(
    # Modelo de IA que utilizará el agente (ej. 'gemini-pro'). Definido en la configuración.
    model=configs.agent_settings.model,
    
    # Instrucción global para el agente. Define su propósito general y comportamiento fundamental.
    # Esta es una instrucción de alto nivel que el agente siempre debe recordar.
    global_instruction=GLOBAL_INSTRUCTION,
    
    # Instrucción específica para la tarea actual o la fase del agente.
    # Puede ser más detallada y cambiar según el contexto de la conversación.
    instruction=INSTRUCTION,
    
    # El nombre del agente, útil para logs o identificaciones.
    name=configs.agent_settings.name,
    
    # Lista de herramientas que este agente tiene permiso para usar.
    # En esta fase, solo incluye 'search_products_csv' para el asesoramiento.
    tools=[
        search_products,
        add_item_to_quote,
        view_quote,
        remove_item_from_quote,
        clear_quote
    ],
    
    # Configuración de los callbacks: funciones que se ejecutarán automáticamente
    # en diferentes puntos del ciclo de vida de la interacción del agente.
    before_tool_callback=before_tool,      # Se ejecuta antes de llamar a cualquier herramienta.
    after_tool_callback=after_tool,        # Se ejecuta después de que cualquier herramienta ha terminado.
    before_agent_callback=before_agent,    # Se ejecuta antes de que el agente procese la entrada del usuario.
    before_model_callback=rate_limit_callback, # Se ejecuta antes de hacer una llamada al modelo de IA,
                                                # útil para controlar la tasa de uso de la API.
)