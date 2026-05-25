import os
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    # O Render fornece a URL do banco automaticamente na variável DATABASE_URL
    # Se estiver rodando local, você precisa configurar essa variável no seu .env
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    if not DATABASE_URL:
        raise ValueError("A variável DATABASE_URL não foi encontrada!")

    # Conecta ao PostgreSQL (limpa ?schema= se presente para evitar erros no psycopg2 local)
    if "?schema=" in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.split("?schema=")[0]
        
    conn = psycopg2.connect(DATABASE_URL)
    return conn