from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import JSONResponse
import mysql.connector

router = APIRouter()

# Criar a tabela se não existir
def criar_tabela():
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='admin',
        database='alignme'
    )
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS avaliacao_medica (
            id_avaliacao INTEGER AUTO_INCREMENT PRIMARY KEY,
            id_paciente INTEGER NOT NULL,
            id_foto_frontal INTEGER NOT NULL,
            id_foto_sagital INTEGER NOT NULL,
            medidas_frontal TEXT,
            medidas_sagital TEXT,
            altura DOUBLE,
            resultado_avaliacao TEXT,
            data_avaliacao TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

criar_tabela()

@router.post("/cadastrar-avaliacao")
async def cadastrar_avaliacao(request: Request):
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="JSON inválido")

    id_paciente = data.get("id_paciente")
    id_foto_frontal = data.get("id_foto_frontal")
    id_foto_sagital = data.get("id_foto_sagital")
    medidas_frontal = data.get("medidas_frontal")
    medidas_sagital = data.get("medidas_sagital")
    altura = data.get("altura")
    resultado = data.get("resultado_avaliacao")
    data_avaliacao = data.get("data_avaliacao")

    # Validação
    if not id_paciente or not id_foto_frontal or not id_foto_sagital or not data_avaliacao:
        raise HTTPException(
            status_code=400,
            detail="Campos obrigatórios: id_paciente, id_foto_frontal, id_foto_sagital, data_avaliacao"
        )

    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='admin',
            database='alignme'
        )
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO avaliacao_medica (
                id_paciente, id_foto_frontal, id_foto_sagital,
                medidas_frontal, medidas_sagital,
                altura, resultado_avaliacao, data_avaliacao
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            id_paciente,
            id_foto_frontal,
            id_foto_sagital,
            medidas_frontal,
            medidas_sagital,
            altura,
            resultado,
            data_avaliacao
        ))
        conn.commit()
        conn.close()

        return JSONResponse(content={"mensagem": "Avaliação cadastrada com sucesso!"})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
