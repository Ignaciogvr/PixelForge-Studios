import os
import pandas as pd
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.agents import AgentType, Tool, initialize_agent
from langchain.chains import RetrievalQA
from langchain.memory import ConversationBufferMemory
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent

# =====================================================================
# PIXELFORGE STUDIOS - AGENTE DE INTELIGENCIA ARTIFICIAL (RAG PIPELINE)
# =====================================================================
# Este script implementa la arquitectura de un Agente Inteligente capaz
# de combinar recuperación de información semántica (RAG en texto) y 
# consulta de datos estructurados (CSV) para el equipo de desarrollo.
# =====================================================================

# NOTA PARA EJECUCIÓN: Reemplazar por clave válida o cargar desde .env
# os.environ['OPENAI_API_KEY'] = 'TU_API_KEY'

def inicializar_sistema():
    print("[1/5] Inicializando el motor LLM...")
    # Usamos temperatura 0 para garantizar respuestas deterministas y evitar alucinaciones
    llm = ChatOpenAI(temperature=0, model_name='gpt-4')

    print("[2/5] Cargando y fragmentando documentos de texto (Chunking)...")
    # El TextSplitter es fundamental en RAG para no saturar la ventana de contexto del LLM
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        length_function=len
    )

    # Cargar y procesar GDD
    loader_gdd = TextLoader('../data/gdd.txt', encoding='utf-8')
    docs_gdd = text_splitter.split_documents(loader_gdd.load())
    
    # Cargar y procesar Guía de Código
    loader_codigo = TextLoader('../data/codigo_guia.txt', encoding='utf-8')
    docs_codigo = text_splitter.split_documents(loader_codigo.load())

    print("[3/5] Construyendo la base de datos vectorial (FAISS)...")
    embeddings = OpenAIEmbeddings()
    vectorstore_gdd = FAISS.from_documents(docs_gdd, embeddings)
    vectorstore_codigo = FAISS.from_documents(docs_codigo, embeddings)

    # Configurar los recuperadores (Retrievers)
    retriever_gdd = vectorstore_gdd.as_retriever(search_kwargs={"k": 3})
    retriever_codigo = vectorstore_codigo.as_retriever(search_kwargs={"k": 3})

    # Cadenas de QA (RetrievalQA) para los documentos no estructurados
    qa_gdd = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever_gdd)
    qa_codigo = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever_codigo)

    print("[4/5] Configurando agentes para análisis de datos estructurados (CSV)...")
    df_bugs = pd.read_csv('../data/bugs.csv')
    df_balance = pd.read_csv('../data/balance.csv')

    # Agentes especializados en Pandas para interactuar con DataFrames
    agente_bugs = create_pandas_dataframe_agent(llm, df_bugs, verbose=False, agent_type=AgentType.OPENAI_FUNCTIONS, allow_dangerous_code=True)
    agente_balance = create_pandas_dataframe_agent(llm, df_balance, verbose=False, agent_type=AgentType.OPENAI_FUNCTIONS, allow_dangerous_code=True)

    print("[5/5] Integrando herramientas en el Agente Enrutador principal...")
    tools = [
        Tool(
            name='Base_Conocimiento_GDD',
            func=qa_gdd.run,
            description='ÚTIL PARA: Entender el lore, reglas del juego, diseño, mecánicas, comportamientos de IA y economía. NO usar para código.'
        ),
        Tool(
            name='Base_Conocimiento_Codigo',
            func=qa_codigo.run,
            description='ÚTIL PARA: Consultar estándares de programación, arquitectura, manejo de memoria, físicas, y cómo programar algo en Unity.'
        ),
        Tool(
            name='Base_Datos_Jira_Bugs',
            func=agente_bugs.run,
            description='ÚTIL PARA: Buscar el estado, responsable o descripción de un bug reportado. Puede buscar por ID (ej. PF-1001) o palabras clave.'
        ),
        Tool(
            name='Base_Datos_Balance',
            func=agente_balance.run,
            description='ÚTIL PARA: Consultar estadísticas numéricas exactas (HP, daño, probabilidad de crítico, etc) de jugadores o enemigos.'
        )
    ]

    # IE2: Formulación de Prompts - Prompt optimizado para restringir alucinaciones y forzar trazabilidad
    prompt_sistema = """
    Eres el asistente técnico de Inteligencia Artificial para PixelForge Studios.
    Tu objetivo es ayudar a programadores, diseñadores y testers a resolver dudas operativas 
    combinando información del GDD, Código, Bugs y Balance.
    
    REGLAS ESTRICTAS DE RESPUESTA:
    1. CERO ALUCINACIONES: Si la respuesta no está en tus herramientas, debes decir exactamente: "La información solicitada no se encuentra en la documentación actual del proyecto."
    2. TRAZABILIDAD: Siempre cita la fuente de tu respuesta indicando qué documento o base de datos usaste (ej: "Según el GDD...", "Revisando el reporte de Jira...", "La guía de código indica...").
    3. ESTRUCTURA: Responde de forma técnica, directa, y usando viñetas (bullet points) para listar la información.
    4. SÍNTESIS: Si te preguntan por un bug que involucra diseño y código, debes usar ambas herramientas (Base_Conocimiento_GDD y Base_Conocimiento_Codigo) y combinar la respuesta.
    """

    # Añadimos memoria para que el agente recuerde el contexto de la conversación
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    agente_principal = initialize_agent(
        tools, 
        llm, 
        agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION, 
        verbose=True,
        memory=memory,
        agent_kwargs={'system_message': prompt_sistema}
    )
    
    return agente_principal

def iniciar_consola():
    print("\n" + "="*50)
    print("  PIXELFORGE AI AGENT - TERMINAL DE DESARROLLO")
    print("="*50)
    try:
        agente = inicializar_sistema()
        print("\n[+] Sistema Listo. (Escribe 'salir' para terminar)")
        while True:
            pregunta = input('\nDesarrollador> ')
            if pregunta.lower() in ['salir', 'exit', 'quit']:
                print("Cerrando sistema...")
                break
            
            # Ejecutar consulta
            try:
                respuesta = agente.run(pregunta)
                print('\n[Respuesta del Agente]:')
                print('-' * 40)
                print(respuesta)
                print('-' * 40)
            except Exception as e:
                print(f"\n[Error en la consulta]: {e}")
                
    except Exception as e:
        print(f'\n[ERROR CRÍTICO AL INICIAR]: {e}')
        print('Asegúrate de haber instalado las dependencias (pip install langchain pandas faiss-cpu openai)')
        print('y de tener configurada tu OPENAI_API_KEY.')

if __name__ == '__main__':
    iniciar_consola()
