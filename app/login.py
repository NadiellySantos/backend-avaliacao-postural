from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import JSONResponse
import pymysql
pymysql.install_as_MySQLdb()
from pydantic import BaseModel
import bcrypt

router = APIRouter()

class LoginInput(BaseModel):
    email: str
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

    email = data.get("email")
    senha = data.get("senha")

    print(f"Tentando login com E-mail: {email} e senha: {senha} ")

    if not email or not senha:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="E-mail e senha são obrigatórios"
        )

    try:
        conn = pymysql.connect(
            host='tccalignme.mysql.database.azure.com', # Host do Azure MySQL
            user='adminuser',                            # Usuário do Azure MySQL
            password='Gnbg6twvJp9cqFR',                  # Senha do Azure MySQL
            database='tccalignme',                       # Nome do banco
            port=3306,                                   # Porta padrão
            ssl_disabled=True  # ⬅️ Esta linha desabilita SSL
        )
        cursor = conn.cursor()
        # Buscar só pelo email (sem senha)
        cursor.execute("SELECT nome, senha FROM medico WHERE email = %s", (email,))
        usuario = cursor.fetchone()
        conn.close()

        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="E-mail ou senha inválidos"
            )
        
        nome, senha_hash = usuario
        senha_hash_bytes = senha_hash.encode('utf-8')

        # Verifica senha
        if bcrypt.checkpw(senha.encode('utf-8'), senha_hash_bytes):
            return JSONResponse(content={
                "mensagem": "Login realizado com sucesso",
                "nome": nome,
                "token": "fake-token-123"
            })
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="E-mail ou senha inválidos"
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )