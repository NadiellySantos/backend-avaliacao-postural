from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import JSONResponse
import pymysql
pymysql.install_as_MySQLdb()
import bcrypt
import re

router = APIRouter()

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
    conn = pymysql.connect(
        host='tccalignme.mysql.database.azure.com', # Host do Azure MySQL
        user='adminuser',                            # Usuário do Azure MySQL
        password='Gnbg6twvJp9cqFR',                  # Senha do Azure MySQL
        database='tccalignme',                       # Nome do banco
        port=3306,                                   # Porta padrão
        ssl={'check_hostname': False}
    )    
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
        conn = pymysql.connect(
            host='tccalignme.mysql.database.azure.com', # Host do Azure MySQL
            user='adminuser',                            # Usuário do Azure MySQL
            password='Gnbg6twvJp9cqFR',                  # Senha do Azure MySQL
            database='tccalignme',                       # Nome do banco
            port=3306,                                   # Porta padrão
            ssl={'check_hostname': False}
        )
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
    conn = pymysql.connect(
        host='tccalignme.mysql.database.azure.com', # Host do Azure MySQL
        user='adminuser',                            # Usuário do Azure MySQL
        password='Gnbg6twvJp9cqFR',                  # Senha do Azure MySQL
        database='tccalignme',                       # Nome do banco
        port=3306,                                   # Porta padrão
        ssl={'check_hostname': False}
    )
    cursor = conn.cursor()
    cursor.execute("SELECT id_medico, nome, data_nascimento, especialidade, sexo FROM medico")
    medicos = cursor.fetchall()
    conn.close()

    return [{"id_medico": p[0], "nome": p[1], "data_nascimento": p[2], "especialidade": p[3], "sexo": p[4]} for p in medicos]