import os
import time
import httpx
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, jwk

SUPABASE_URL = os.environ['SUPABASE_URL']
JWKS_URL = f"{SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"
bearer = HTTPBearer(auto_error=False)
_cache = {'jwks': None, 'ts': 0.0}


async def get_jwks():
    if _cache['jwks'] and time.time() - _cache['ts'] < 600:
        return _cache['jwks']
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(JWKS_URL)
        r.raise_for_status()
        _cache.update({'jwks': r.json(), 'ts': time.time()})
    return _cache['jwks']


async def current_user(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    if not creds or creds.scheme.lower() != 'bearer':
        raise HTTPException(401, 'Bearer token required')

    token = creds.credentials
    header = jwt.get_unverified_header(token)
    kid = header.get('kid')
    alg = header.get('alg', 'HS256')

    if alg.startswith('HS'):
        secret = os.environ.get('SUPABASE_JWT_SECRET')
        if not secret:
            raise HTTPException(500, 'Auth not configured')
        try:
            claims = jwt.decode(token, secret, algorithms=[alg], options={'verify_aud': False})
        except Exception:
            raise HTTPException(401, 'Invalid or expired token')
    else:
        jwks = await get_jwks()
        key = next((k for k in jwks['keys'] if k.get('kid') == kid), None)
        if not key:
            raise HTTPException(401, 'Invalid token key')
        public_key = jwk.construct(key).to_pem()
        try:
            claims = jwt.decode(token, public_key, algorithms=[alg], options={'verify_aud': False})
        except Exception:
            raise HTTPException(401, 'Invalid or expired token')

    if not claims.get('sub'):
        raise HTTPException(401, 'Missing subject')
    return claims
