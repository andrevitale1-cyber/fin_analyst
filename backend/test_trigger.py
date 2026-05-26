import sys
import os
from dotenv import load_dotenv

# Adiciona o diretório backend ao path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from agents.x_replier_agent import XReplierAgent

def test():
    try:
        agent = XReplierAgent()
        print("Instanciou o XReplierAgent.")
        result = agent.run_auto_replier(limit=1)
        print("Executou run_auto_replier com sucesso!")
        print(f"Resultado: {result}")
    except Exception as e:
        print("\n[EXCEÇÃO DETECTADA]:")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test()
