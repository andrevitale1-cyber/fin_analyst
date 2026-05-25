from fastapi import APIRouter, Form, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List
import os
import json
import datetime
from agents.x_replier_agent import XReplierAgent
import psycopg2

router = APIRouter(prefix="/api/x", tags=["X Bot Promotion"])

class ManualTweetRequest(BaseModel):
    text: str

def get_db_connection():
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return psycopg2.connect(db_url, sslmode='require')
    else:
        return psycopg2.connect(
            host="localhost",
            database="dados_analise",
            user="postgres",
            password="password",
            port="5432"
        )

@router.post("/trigger-run")
async def trigger_auto_replier(limit: int = 3):
    """
    Executa manualmente uma varredura para responder a posts do X.
    Funciona em Mock Mode por padrão caso as credenciais não estejam configuradas.
    """
    try:
        agent = XReplierAgent()
        result = agent.run_auto_replier(limit=limit)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao executar robô do X: {str(e)}"
        )

@router.get("/history")
async def get_bot_history():
    """
    Retorna o histórico de todas as interações e respostas enviadas pelo robô.
    """
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, tweet_id, usuario_autor, texto_original, resposta_enviada, data_resposta FROM x_bot_history ORDER BY id DESC")
        rows = cur.fetchall()
        
        history = []
        for r in rows:
            history.append({
                "id": r[0],
                "tweet_id": r[1],
                "username": r[2],
                "original_text": r[3],
                "reply_text": r[4],
                "replied_at": str(r[5])
            })
        return history
    except Exception as e:
        print(f"Erro ao obter histórico do banco: {e}")
        return []
    finally:
        if cur: cur.close()
        if conn: conn.close()

@router.post("/post-manual")
async def post_manual_tweet(request: ManualTweetRequest):
    """
    Permite fazer um tweet manual de divulgação (ou gravá-lo no log em Mock Mode).
    """
    if not request.text or len(request.text.strip()) == 0:
        raise HTTPException(status_code=400, detail="O texto do tweet não pode ser vazio.")
        
    if len(request.text) > 280:
        raise HTTPException(status_code=400, detail=f"O tweet excede o limite de 280 caracteres do X (total: {len(request.text)}).")

    agent = XReplierAgent()
    
    if agent.mock_mode:
        # Grava no log simulado
        log_dir = "backend" if os.path.exists("backend") else "."
        log_file_path = os.path.join(log_dir, "x_tweets.log")
        
        log_entry = (
            f"=========================================\n"
            f"DATA: {datetime.datetime.now().isoformat() if 'datetime' in globals() else 'AGORA'}\n"
            f"STATUS: MANUAL SIMULATED TWEET SUCCESS\n"
            f"TEXTO DO TWEET ({len(request.text)} chars):\n{request.text}\n"
            f"=========================================\n\n"
        )
        try:
            with open(log_file_path, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Erro ao salvar arquivo de log de tweets manuais: {e}")

        return {
            "status": "success",
            "mock_mode": True,
            "message": f"Tweet manual simulado e gravado no log local: {log_file_path}",
            "text": request.text
        }
    else:
        try:
            agent.client.create_tweet(text=request.text)
            return {
                "status": "success",
                "mock_mode": False,
                "message": "Tweet publicado com sucesso na conta conectada!",
                "text": request.text
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Falha ao enviar tweet real: {str(e)}"
            )
