from fastapi import APIRouter, Depends, HTTPException
from auth import current_user
from ai.claude_client import claude

router = APIRouter()


@router.get('/ai/ping')
async def ai_ping(user=Depends(current_user)):
    try:
        resposta = claude.generate(
            system='Responda apenas com a palavra pedida, sem explicações.',
            prompt='Responda exatamente: OK',
            max_tokens=16,
        )
        return {'model': claude.model, 'resposta': resposta.strip()}
    except Exception as e:
        raise HTTPException(502, f'Erro ao chamar Anthropic: {e}')
