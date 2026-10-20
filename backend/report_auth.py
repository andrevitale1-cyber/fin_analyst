"""Verify Clerk sessions before accessing the report library."""
from functools import lru_cache
import os

from fastapi import Header, HTTPException
import jwt


class SessionUser(str):
    def __new__(cls, user_id, *, token="", plan=None):
        user = super().__new__(cls, user_id)
        user.token, user.plan = token, plan
        return user


@lru_cache(maxsize=4)
def signing_keys(issuer):
    return jwt.PyJWKClient(issuer + "/.well-known/jwks.json", timeout=10)


def require_report_user(authorization: str = Header(default="")) -> str:
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token or len(token) > 16000:
        raise HTTPException(401, "Faça login para acessar os relatórios.")
    issuer = os.getenv("CLERK_ISSUER", "https://clerk.finanalyser.com.br").rstrip("/")
    origins = os.getenv("CLERK_AUTHORIZED_PARTIES", "https://finanalyser.com.br,https://www.finanalyser.com.br").split(",")
    try:
        key = signing_keys(issuer).get_signing_key_from_jwt(token)
        claims = jwt.decode(token, key.key, algorithms=["RS256"], issuer=issuer,
                            options={"require": ["exp", "iat", "nbf", "sub", "azp"], "verify_aud": False}, leeway=5)
        if claims["azp"] not in [origin.strip() for origin in origins] or not str(claims["sub"]).startswith("user_"):
            raise jwt.InvalidTokenError()
        metadata = claims.get("metadata") or claims.get("public_metadata") or {}
        plan = metadata.get("plan") if isinstance(metadata, dict) else None
        return SessionUser(claims["sub"], token=token, plan=plan if plan in ("free", "premium") else None)
    except jwt.PyJWKClientConnectionError:
        raise HTTPException(503, "Não foi possível verificar sua sessão. Tente novamente.") from None
    except jwt.PyJWTError:
        raise HTTPException(401, "Sessão inválida ou expirada. Entre novamente.") from None
