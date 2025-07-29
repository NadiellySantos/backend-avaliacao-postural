from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import JSONResponse
import sqlite3

router = APIRouter()

# Cria a tabela MEDICO caso não exista
def criar_tabela():
    conn = sqlite3.connect('app/pacientes.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS medico (
            id_medico INTEGER PRIMARY KEY AUTOINCREMENT,
            cpf TEXT NOT NULL UNIQUE,
            nome TEXT NOT NULL,
            data_nascimento TEXT NOT NULL,
            especialidade TEXT,
            telefone TEXT,
            crm TEXT NOT NULL,
            sexo TEXT
        )
    ''')
    conn.commit()
    conn.close()

criar_tabela()

@router.post("/cadastrar-medico")
async def cadastrar_medico(request: Request):
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
    especialidade = data.get("especialidade")
    telefone = data.get("telefone")
    crm = data.get("crm")
    sexo = data.get("sexo")    # novo campo

    if not cpf or not nome or not data_nascimento or not crm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Campos obrigatórios faltando"
        )

    try:
        conn = sqlite3.connect('app/pacientes.db')
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO medico (
                cpf, nome, data_nascimento, especialidade,
                telefone, crm, sexo
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            cpf, nome, data_nascimento, especialidade,
            telefone, crm, sexo
        ))

        conn.commit()
        conn.close()

        return JSONResponse(content={"mensagem": "Médico cadastrado com sucesso!"})

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
        
@router.get("/listar-medicos")
def listar_medicos():
    conn = sqlite3.connect('app/pacientes.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id_medico, nome, data_nascimento, especialidade, sexo FROM medico")
    medicos = cursor.fetchall()
    conn.close()

    return [{"id_medico": p[0], "nome": p[1], "data_nascimento": p[2], "especialidade": p[3], "sexo": p[4]} for p in medicos]
