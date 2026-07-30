from fastapi import APIRouter, Depends, HTTPException
from auth import current_user
from database import get_pool
from schemas import ProjectCreate, ProjectUpdate

router = APIRouter()


@router.get('/projects')
async def list_projects(user=Depends(current_user)):
    pool = get_pool()
    rows = await pool.fetch(
        "SELECT id, nome, idioma, genero, criado_em FROM projects WHERE user_id=$1 ORDER BY criado_em DESC",
        user['sub'],
    )
    return [dict(r) for r in rows]


@router.post('/projects', status_code=201)
async def create_project(payload: ProjectCreate, user=Depends(current_user)):
    pool = get_pool()
    row = await pool.fetchrow(
        "INSERT INTO projects (user_id, nome, idioma, genero) VALUES ($1, $2, $3, $4) "
        "RETURNING id, nome, idioma, genero, criado_em",
        user['sub'], payload.nome, payload.idioma, payload.genero,
    )
    return dict(row)


@router.get('/projects/{project_id}')
async def get_project(project_id: str, user=Depends(current_user)):
    pool = get_pool()
    row = await pool.fetchrow(
        "SELECT id, nome, idioma, genero, criado_em FROM projects WHERE id=$1 AND user_id=$2",
        project_id, user['sub'],
    )
    if not row:
        raise HTTPException(404, 'Projeto não encontrado')
    return dict(row)


@router.put('/projects/{project_id}')
async def update_project(project_id: str, payload: ProjectUpdate, user=Depends(current_user)):
    pool = get_pool()
    existing = await pool.fetchrow("SELECT id FROM projects WHERE id=$1 AND user_id=$2", project_id, user['sub'])
    if not existing:
        raise HTTPException(404, 'Projeto não encontrado')
    row = await pool.fetchrow(
        "UPDATE projects SET nome=COALESCE($1, nome), idioma=COALESCE($2, idioma), genero=COALESCE($3, genero) "
        "WHERE id=$4 RETURNING id, nome, idioma, genero, criado_em",
        payload.nome, payload.idioma, payload.genero, project_id,
    )
    return dict(row)


@router.delete('/projects/{project_id}', status_code=204)
async def delete_project(project_id: str, user=Depends(current_user)):
    pool = get_pool()
    result = await pool.execute("DELETE FROM projects WHERE id=$1 AND user_id=$2", project_id, user['sub'])
    if result == 'DELETE 0':
        raise HTTPException(404, 'Projeto não encontrado')
