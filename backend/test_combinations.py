import os
import tweepy
from dotenv import load_dotenv

load_dotenv()

def main():
    ck = "WXYXKSGpolkvb4SWAJC7BscG5"
    cs = "aJ2AK6BcMkxkIqUMWfBc1ExpKZZ0tgMNOWJ7a3D0lJfc37DLQP"
    at = "2047827061063000064-XFZShEocNdzmjPNk3BhzJF1BB2nO0N"
    ats = "YCvUa9DUoR58ESFoG36nCIIAZtuEWqTAMTUIsJlOt7VAK"

    # Criar variacoes para 'l' na API Key
    ck_variations = [
        ck,
        ck.replace("polk", "po1k"),
        ck.replace("polk", "poIk")
    ]

    # Criar variacoes para o '0' (zero), 'O' (letra O), 'l' (L minusculo), '1' e 'I' no API Secret
    cs_variations = [
        cs,
        cs.replace("3D0lJfc", "3D01Jfc"),
        cs.replace("3D0lJfc", "3D0IJfc"),
        cs.replace("3D0lJfc", "3DOlJfc"),
        cs.replace("3D0lJfc", "3DO1Jfc"),
        cs.replace("3D0lJfc", "3DOIJfc")
    ]

    print("🔍 Testando combinacoes de caracteres para API Key e API Secret no X...")
    found = False
    
    for v_ck in ck_variations:
        for v_cs in cs_variations:
            try:
                client = tweepy.Client(
                    consumer_key=v_ck,
                    consumer_secret=v_cs,
                    access_token=at,
                    access_token_secret=ats
                )
                # Testar conexao obtendo o usuario logado
                me = client.get_me()
                print("\n🎉 SUCESSO! Combinacao correta encontrada!")
                print(f"API_KEY (CK): {v_ck}")
                print(f"API_SECRET (CS): {v_cs}")
                if me and me.data:
                    print(f"Usuario Conectado: @{me.data.username}")
                found = True
                break
            except Exception as e:
                err_msg = str(e)
                # Se for outro erro que nao 401 Unauthorized, logamos
                if "Unauthorized" not in err_msg:
                    print(f"Erro diferente: {err_msg}")
        if found:
            break

    if not found:
        print("\n❌ Nenhuma combinacao funcionou.")
        print("Isso geralmente significa que a API Key (Consumer Key) tambem precisa ser regerada para atualizar as permissoes de escrita do aplicativo.")

if __name__ == "__main__":
    main()
