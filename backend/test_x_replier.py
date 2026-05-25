import sys
import os
import json

# Adiciona o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.x_replier_agent import XReplierAgent

def run_test():
    print("[TEST] Iniciando Testes do X Auto-Reply Promotion Bot...")
    
    agent = XReplierAgent()
    
    # 1. Garante que o Mock Mode está ativo para segurança dos testes locais
    print(f"Status do Mock Mode: {agent.mock_mode}")
    if not agent.mock_mode:
        print("Chaves reais do X detectadas. Forçando MOCK MODE temporário para segurança do teste.")
        agent.mock_mode = True
        
    # 2. Inserir dados temporários no banco de dados local para WEGE3, PETR4 e MSFT
    # para simular relatórios reais gerados pelos usuários
    print("Preparando cenario de teste no banco de dados...")
    conn = None
    cur = None
    try:
        conn = agent.get_db_connection()
        cur = conn.cursor()
        
        # Limpa execuções antigas de mock para resetar o cenário
        cur.execute("DELETE FROM x_bot_history WHERE tweet_id LIKE 'mock_%'")
        
        # Mock de dados para WEGE3
        wege_data = {
            "data": {
                "nota_geral": 4.8,
                "receita_nota": 5.0,
                "rentabilidade_nota": 5.0,
                "divida_nota": 4.5,
                "lucro_nota": 4.5,
                "tese_investimento": "Crescimento continuo no exterior com forte lideranca em motores industriais de alta eficiencia."
            }
        }
        # Mock de dados para MSFT
        msft_data = {
            "data": {
                "nota_geral": 5.0,
                "receita_nota": 5.0,
                "rentabilidade_nota": 5.0,
                "divida_nota": 5.0,
                "lucro_nota": 5.0,
                "tese_investimento": "Forte avanco do Azure e IA generativa sustentando margens e fluxo de caixa operacional resiliente."
            }
        }
        
        # Insere WEGE3
        cur.execute(
            "INSERT INTO historico (empresa, ano, trimestre, data_criacao, resultado_json, user_id) VALUES (%s, %s, %s, NOW(), %s, %s)",
            ("WEGE3", "2025", "4T", json.dumps(wege_data), "clerk_test_123")
        )
        # Insere MSFT
        cur.execute(
            "INSERT INTO historico (empresa, ano, trimestre, data_criacao, resultado_json, user_id) VALUES (%s, %s, %s, NOW(), %s, %s)",
            ("MSFT", "2026", "2T", json.dumps(msft_data), "clerk_test_123")
        )
        
        conn.commit()
        print("Dados simulados criados com sucesso no banco de dados!")
    except Exception as e:
        print(f"Erro ao preparar banco para testes: {e}")
    finally:
        if cur: cur.close()
        if conn: conn.close()

    # 3. Executar o robô de auto-replies
    print("\nExecutando loop de respostas automaticas em Mock Mode...")
    result = agent.run_auto_replier(limit=4)
    
    print("\nRESULTADO DOS TESTES:")
    print(f"  - Total de tweets processados com sucesso: {result['replies_processed']}")
    print(f"  - Modo Simulacao Ativo: {result['mock_mode']}")
    
    print("\nDetalhes das Respostas Geradas:")
    for idx, r in enumerate(result["replies"]):
        print(f"\n[{idx + 1}] Resposta para @{r['username']}:")
        print(f"    - Tweet Original: '{r['tweet_text']}'")
        print(f"    - Resposta do Bot ({len(r['reply_text'])} chars): '{r['reply_text']}'")
        
        # Validação de regras estritas
        assert len(r['reply_text']) <= 280, f"Erro: Resposta {idx + 1} excedeu 280 caracteres!"
        assert agent.platform_url in r['reply_text'] or agent.promo_tweet_url in r['reply_text'], f"Erro: Link da plataforma/promocao ausente na resposta {idx + 1}!"
        print(f"    - Validacoes de tamanho e link: APROVADAS! OK")

    print("\nTodos os testes unitarios e de integracao foram concluidos com sucesso!")
    print("Os tweets simulados foram arquivados com sucesso no log: backend/x_tweets.log")

if __name__ == "__main__":
    run_test()
