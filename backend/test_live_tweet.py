import os
from dotenv import load_dotenv
from agents.x_replier_agent import XReplierAgent

load_dotenv()

def main():
    print("🐦 Iniciando teste de publicacao real no X...")
    agent = XReplierAgent()
    print(f"Status do Mock Mode: {agent.mock_mode}")

    if agent.mock_mode:
        print("Erro: O agente ainda esta em Mock Mode. Verifique suas credenciais no .env!")
        return

    test_text = "Testando a nova resposta do robo do @Finanalyser_ai divulgando o post oficial de lancamento: https://x.com/Finanalyser_ai/status/2047846896727687269 🚀"
    print(f"Tentando publicar tweet real: '{test_text}'")
    try:
        agent.client.create_tweet(text=test_text)
        print("🎉 SUCESSO! O tweet foi publicado em tempo real na sua conta do X!")
    except Exception as e:
        print(f"❌ Falha ao publicar tweet: {e}")

if __name__ == "__main__":
    main()
