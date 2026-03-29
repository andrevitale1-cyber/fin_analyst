import os
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    # O Render fornece a URL do banco automaticamente na variável DATABASE_URL
    # Se estiver rodando local, você precisa configurar essa variável no seu .env
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    if not DATABASE_URL:
        raise ValueError("A variável DATABASE_URL não foi encontrada!")

    # Conecta ao PostgreSQL
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    return conn