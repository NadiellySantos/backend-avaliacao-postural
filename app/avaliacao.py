from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import JSONResponse
import mysql.connector

router = APIRouter()

# Criar a tabela se não existir
def criar_tabela():
    conn = mysql.connector.connect(
        host = 'localhost',
        user = 'root',
        password = 'admin',
        database = 'alignme'
    )
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS avaliacao_medica (
            id_avaliacao INTEGER AUTO_INCREMENT PRIMARY KEY,
            id_foto INTEGER NOT NULL,
            cpf VARCHAR(11) NOT NULL,
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

    id_foto = data.get("id_foto")
    cpf = data.get("cpf")
    altura = data.get("altura")
    resultado = data.get("resultado_avaliacao")
    data_avaliacao = data.get("data_avaliacao")

    if not id_foto or not cpf or not data_avaliacao:
        raise HTTPException(status_code=400, detail="Campos obrigatórios: id_foto, cpf e data_avaliacao")

    try:
        conn = mysql.connector.connect(
        host = 'localhost',
        user = 'root',
        password = 'admin',
        database = 'alignme'
    )
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO avaliacao_medica (id_foto, cpf, altura, resultado_avaliacao, data_avaliacao)
            VALUES (?, ?, ?, ?, ?)
        """, (id_foto, cpf, altura, resultado, data_avaliacao))
        conn.commit()
        conn.close()

        return JSONResponse(content={"mensagem": "Avaliação cadastrada com sucesso!"})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
