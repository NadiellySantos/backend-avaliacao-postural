from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import JSONResponse
import mysql.connector
from pydantic import BaseModel
import bcrypt
import os  # ← ADICIONADO

router = APIRouter()

# ✅ MESMA FUNÇÃO DE CONEXÃO DO OUTRO ARQUIVO
def get_connection():
    """Conecta ao banco usando variáveis de ambiente"""
    try:
        # Primeiro tenta variáveis de ambiente do Azure App Service
        host = os.environ.get('DB_HOST')
        user = os.environ.get('DB_USER')
        password = os.environ.get('DB_PASSWORD')
        database = os.environ.get('DB_NAME')
        port = int(os.environ.get('DB_PORT', 3306))
        
        if all([host, user, password, database]):
            # Conecta ao Azure
            return pymysql.connect(
                host=host,
                user=user,
                password=password,
                database=database,
                port=port,
                ssl={'check_hostname': False}
            )
        else:
            # Fallback para desenvolvimento local (.env)
            from dotenv import load_dotenv
            load_dotenv()
            
            return pymysql.connect(
                host=os.getenv('LOCAL_DB_HOST', 'localhost'),
                user=os.getenv('LOCAL_DB_USER', 'root'),
                password=os.getenv('LOCAL_DB_PASSWORD', 'admin'),
                database=os.getenv('LOCAL_DB_NAME', 'tccalignme')
            )
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        raise

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
        # ✅ ALTERADO: usa a nova função get_connection()
        conn = get_connection()
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
