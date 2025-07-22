from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import JSONResponse
import sqlite3

router = APIRouter()

# Cria a tabela PESSOA caso não exista
def criar_tabela():
    conn = sqlite3.connect('app/pacientes.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pessoa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cpf TEXT NOT NULL UNIQUE,
            nome TEXT NOT NULL,
            data_nascimento TEXT NOT NULL,
            peso REAL,
            raca TEXT,
            profissao TEXT,
            telefone TEXT,
            tipo_corporal TEXT
        )
    ''')
    conn.commit()
    conn.close()

criar_tabela()

@router.post("/cadastrar-paciente")
async def cadastrar_paciente(request: Request):
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="JSON inválido"
        )

    cpf = data.get("cpf")
    nome = data.get("nome")
    data_nascimento = data.get("data_nascimento")
    peso = data.get("peso")
    raca = data.get("raca")
    profissao = data.get("profissao")
    telefone = data.get("telefone")
    tipo_corporal = data.get("tipo_corporal")

    # Campos obrigatórios
    if not cpf or not nome or not data_nascimento:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Campos obrigatórios faltando"
        )

    try:
        conn = sqlite3.connect('app/pacientes.db')
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO pessoa (
                cpf, nome, data_nascimento, peso, raca, profissao, telefone, tipo_corporal
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cpf, nome, data_nascimento, peso, raca, profissao, telefone, tipo_corporal
        ))

        conn.commit()
        conn.close()

        return JSONResponse(content={"mensagem": "Paciente cadastrado com sucesso!"})

    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="CPF já cadastrado"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
