"""Cliente OpenAI compartilhado pela análise de documentos e rascunhos do X."""
import io
import os

import httpx
from pypdf import PdfReader


class OpenAIError(RuntimeError):
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


class OpenAIClient:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.model = os.getenv("OPENAI_MODEL", "gpt-4.1")

    def _request(self, client, path, **kwargs):
        try:
            response = client.post(path, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            code = exc.response.status_code
            raise OpenAIError(f"Erro na API OpenAI (HTTP {code}).", status_code=code) from None
        except httpx.TimeoutException:
            raise TimeoutError("Tempo limite da API OpenAI excedido.") from None
        except (httpx.RequestError, ValueError):
            raise OpenAIError("Não foi possível obter uma resposta da API OpenAI.") from None

    def _client(self):
        if not self.api_key:
            raise OpenAIError("Chave OPENAI_API_KEY não encontrada")
        return httpx.Client(
            base_url="https://api.openai.com/v1/", timeout=90,
            headers={"Authorization": f"Bearer {self.api_key}"},
        )

    def _chat(self, client, content, system="", max_tokens=12000):
        result = self._request(client, "responses", json={
            "model": self.model,
            "instructions": system or "Responda somente ao pedido do usuário usando os dados fornecidos.",
            "input": [{"role": "user", "content": content}],
            "max_output_tokens": max_tokens,
            "store": False,
        })
        if result.get("status") == "incomplete":
            raise OpenAIError("A resposta da IA foi truncada. Tente um documento menor.")
        text = "".join(part.get("text", "")
                       for item in result.get("output", []) if item.get("type") == "message"
                       for part in item.get("content", []) if part.get("type") == "output_text")
        if not text.strip():
            raise OpenAIError("A IA retornou uma resposta vazia ou inválida.")
        return text

    def chat_text(self, prompt, system=""):
        with self._client() as client:
            return self._chat(client, prompt, system, max_tokens=1000)

    def search_pdf_links(self, query, document_type="report"):
        """Uma pesquisa web retorna candidatos; o fetcher valida o documento baixado."""
        target = ("full earnings-call transcripts, in HTML or PDF, preferably from investor relations. Never return earnings releases, summaries, audio-only pages or paywalled content"
                  if document_type == "transcript" else
                  "official earnings-release PDFs or official investor-relations result pages that link to them")
        with self._client() as client:
            result = self._request(client, "responses", json={
                "model": self.model,
                "input": query + '\nReturn only JSON: [{"title":"...","url":"https://..."}]. Find up to ' + ("5" if document_type == "transcript" else "8") + ' ' + target + '. Do not invent URLs.',
                "tools": [{"type": "web_search", "search_context_size": "low"}],
                "tool_choice": "required",
                "max_output_tokens": 700,
                "store": False,
            }, timeout=30 if document_type == "transcript" else 90)
        text = "".join(part.get("text", "")
                       for item in result.get("output", []) if item.get("type") == "message"
                       for part in item.get("content", []) if part.get("type") == "output_text")
        import json
        try:
            links = json.loads(text.strip().removeprefix("```json").removesuffix("```").strip())
            if not isinstance(links, list):
                raise ValueError
            return [item for item in links[:5 if document_type == "transcript" else 8] if isinstance(item, dict) and isinstance(item.get("url"), str)]
        except (ValueError, TypeError):
            if document_type == "transcript":
                raise OpenAIError("A pesquisa de transcrições retornou uma resposta inválida.") from None
            return []

    def analyze_transcript(self, prompt, text):
        if not text.strip():
            raise OpenAIError("Transcrição sem texto para análise.")
        with self._client() as client:
            return self._chat(client, [{"type": "input_text", "text": prompt + "\n--- TRANSCRIPT ---\n" + text[:180000]}], max_tokens=4000)

    @staticmethod
    def extract_text(pdf_bytes):
        try:
            text = ""
            for page in PdfReader(io.BytesIO(pdf_bytes)).pages:
                text += (page.extract_text() or "") + "\n"
                if len(text) >= 180000:
                    break
            if not text.strip():
                raise ValueError
            return text[:180000]
        except Exception:
            raise OpenAIError("Não foi possível ler o PDF. Envie um PDF com texto selecionável.") from None

    def analyze_document(self, prompt, pdf_bytes=None, pdf_text=""):
        with self._client() as client:
            if pdf_bytes:
                try:
                    uploaded = self._request(client, "files", data={"purpose": "user_data"},
                                             files={"file": ("report.pdf", pdf_bytes, "application/pdf")})
                    return self._chat(client, [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_file", "file_id": uploaded["id"]},
                    ])
                except OpenAIError as exc:
                    if exc.status_code in (401, 403, 429):
                        raise
                    pdf_text = self.extract_text(pdf_bytes)
                except (KeyError, TimeoutError):
                    # Se o upload/anexo falhar, tenta o texto selecionável do PDF.
                    pdf_text = self.extract_text(pdf_bytes)
            if not pdf_text.strip():
                raise OpenAIError("Documento sem texto para análise. Faça o upload manual de um PDF.")
            return self._chat(client, [{"type": "input_text", "text": prompt + "\n--- TEXTO DO PDF ---\n" + pdf_text[:180000]}])
