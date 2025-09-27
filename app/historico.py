from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import JSONResponse
import mysql.connector

router = APIRouter()

@router.post("/listar-avaliacao")
async def listar_avaliacao(request: Request):
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="JSON inválido"
        )
    
    cpf = data.get("cpf")

    if not cpf:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Campos obrigatórios faltando"
        )
    
    try:
        conn = mysql.connector.connect(
        host = 'localhost',
        user = 'root',
        password = 'admin',
        database = 'alignme'
        )
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id_foto, cpf, altura, resultado_avaliacao, data_avaliacao FROM avaliacao_medica WHERE cpf = ?
        """, (cpf,
        ))
        
        avaliacao_medica = cursor.fetchall()
        conn.close()

        return {"avaliacoes": [{"id_foto": p[0], "cpf": p[1], "altura": p[2], "resultado_avaliacao": p[3], "data_avaliacao": p[4]} for p in avaliacao_medica]}

    except mysql.connector.IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="CPF não encontrado"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )