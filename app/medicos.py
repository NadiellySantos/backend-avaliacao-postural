from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import JSONResponse
import pymysql
import bcrypt
import re
import os  # ← ADICIONADO

pymysql.install_as_MySQLdb()
router = APIRouter()

# ✅ NOVA FUNÇÃO DE CONEXÃO (ÚNICA ALTERAÇÃO)
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

# ✅ RESTANTE DO CÓDIGO PERMANECE EXATAMENTE IGUAL
# Validação de CPF
def validar_cpf(cpf: str) -> bool:
    cpf = ''.join(filter(str.isdigit, cpf))

    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False

    for i in range(9, 11):
        soma = sum(int(cpf[j]) * ((i + 1) - j) for j in range(i))
        digito = (soma * 10) % 11
        if digito == 10:
            digito = 0
        if digito != int(cpf[i]):
            return False
    return True

# Validação da senha
def validar_senha(senha: str) -> bool:
    return (
        len(senha) >= 8 and
        re.search(r"[A-Z]", senha) and
        re.search(r"[a-z]", senha) and
        re.search(r"\d", senha) and
        re.search(r"[@$!%*#?&]", senha)
    )

# Cria a tabela MEDICO caso não exista
def criar_tabela():
    conn = get_connection()  # ← ALTERADO: usa nova função
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS medico (
            id_medico INTEGER AUTO_INCREMENT PRIMARY KEY,
            cpf VARCHAR(11) NOT NULL UNIQUE,
            nome TEXT NOT NULL,
            data_nascimento TEXT NOT NULL,
            especialidade TEXT,
            telefone TEXT,
            crm TEXT NOT NULL,
            sexo TEXT,
            email TEXT,
            senha TEXT NOT NULL
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
    sexo = data.get("sexo")
    email = data.get("email")
    senha_hash = data.get("senha")

    if not cpf or not nome or not data_nascimento or not crm or not senha_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Campos obrigatórios faltando"
        )
    
    if not validar_cpf(cpf):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CPF inválido"
        )

    if not validar_senha(senha_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A senha deve conter no mínimo 8 caracteres, incluindo letra maiúscula, minúscula, número e caractere especial."
        )

    senha = bcrypt.hashpw(senha_hash.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    try:
        conn = get_connection()  # ← ALTERADO: usa nova função
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO medico (
                cpf, nome, data_nascimento, especialidade,
                telefone, crm, sexo, email, senha
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            cpf, nome, data_nascimento, especialidade,
            telefone, crm, sexo, email, senha
        ))

        conn.commit()
        conn.close()

        return JSONResponse(content={"mensagem": "Médico cadastrado com sucesso!"})

    except pymysql.IntegrityError as e:
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
    conn = get_connection()  # ← ALTERADO: usa nova função
    cursor = conn.cursor()
    cursor.execute("SELECT id_medico, nome, data_nascimento, especialidade, sexo FROM medico")
    medicos = cursor.fetchall()
    conn.close()

    return [{"id_medico": p[0], "nome": p[1], "data_nascimento": p[2], "especialidade": p[3], "sexo": p[4]} for p in medicos]