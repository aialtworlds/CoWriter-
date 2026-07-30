from fastapi import APIRouter, Depends, HTTPException
from auth import current_user
from database import get_pool
from schemas import ChapterCreate
from checks.helpers import count_words

try:
    from langdetect import detect
except Exception:
    detect = None

router = APIRouter()


async def _assert_project_owner(pool, project_id: str, user_id: str):
    row = await pool.fetchrow("SELECT id, idioma FROM projects WHERE id=$1 AND user_id=$2", project_id, user_id)
    if not row:
        raise HTTPException(404, 'Projeto não encontrado')
    return row


async def _assert_chapter_owner(pool, chapter_id: str, user_id: str):
    row = await pool.fetchrow(
        "SELECT c.id, c.project_id, c.titulo, c.texto_bruto, c.idioma_detectado, c.criado_em, p.idioma as project_idioma "
        "FROM chapters c JOIN projects p ON p.id = c.project_id "
        "WHERE c.id=$1 AND p.user_id=$2",
        chapter_id, user_id,
    )
    if not row:
        raise HTTPException(404, 'Capítulo não encontrado')
    return row


@router.get('/projects/{project_id}/chapters')
async def list_chapters(project_id: str, user=Depends(current_user)):
    pool = get_pool()
    await _assert_project_owner(pool, project_id, user['sub'])
    rows = await pool.fetch(
        "SELECT id, titulo, idioma_detectado, criado_em FROM chapters WHERE project_id=$1 ORDER BY criado_em DESC",
        project_id,
    )
    return [dict(r) for r in rows]


@router.post('/projects/{project_id}/chapters', status_code=201)
async def create_chapter(project_id: str, payload: ChapterCreate, user=Depends(current_user)):
    pool = get_pool()
    project = await _assert_project_owner(pool, project_id, user['sub'])
    idioma_detectado = project['idioma']
    if detect and payload.texto_bruto.strip():
        try:
            idioma_detectado = detect(payload.texto_bruto[:2000])
        except Exception:
            idioma_detectado = project['idioma']
    row = await pool.fetchrow(
        "INSERT INTO chapters (project_id, titulo, texto_bruto, idioma_detectado) VALUES ($1, $2, $3, $4) "
        "RETURNING id, titulo, idioma_detectado, criado_em",
        project_id, payload.titulo, payload.texto_bruto, idioma_detectado,
    )
    result = dict(row)
    result['palavras'] = count_words(payload.texto_bruto)
    return result


@router.get('/chapters/{chapter_id}')
async def get_chapter(chapter_id: str, user=Depends(current_user)):
    pool = get_pool()
    row = await _assert_chapter_owner(pool, chapter_id, user['sub'])
    result = dict(row)
    result['palavras'] = count_words(result['texto_bruto'])
    return result


@router.delete('/chapters/{chapter_id}', status_code=204)
async def delete_chapter(chapter_id: str, user=Depends(current_user)):
    pool = get_pool()
    await _assert_chapter_owner(pool, chapter_id, user['sub'])
    await pool.execute("DELETE FROM chapters WHERE id=$1", chapter_id)
