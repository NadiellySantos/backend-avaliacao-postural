from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import JSONResponse
import sqlite3

router = APIRouter()

class LoginInput(BaseModel):
    cpf: str
    senha: str

@router.post("/login")
async def login(request: Request):
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="JSON inválido"
        )

    cpf = data.get("cpf")
    senha = data.get("senha")

    print(f"Tentando login com CPF: {cpf} e senha: {senha} ")

    if not cpf or not senha:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CPF e senha são obrigatórios"
        )

    try:
        conn = sqlite3.connect("app/pacientes.db")
        cursor = conn.cursor()
        cursor.execute("SELECT nome FROM medico WHERE cpf = ? AND senha = ?", (cpf, senha))
        usuario = cursor.fetchone()
        conn.close()

        if usuario:
            return JSONResponse(content={
                "mensagem": "Login realizado com sucesso",
                "nome": usuario[0],
                "token": "fake-token-123" 
            })
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="CPF ou senha inválidos"
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )