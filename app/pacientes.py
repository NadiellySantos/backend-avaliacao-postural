from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import JSONResponse
import pymysql
pymysql.install_as_MySQLdb()

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

# Cria a tabela PESSOA caso não exista, agora com idade e sexo
def criar_tabela():
    conn = pymysql.connect(
        host='tccalignme.mysql.database.azure.com', # Host do Azure MySQL
        user='adminuser',                            # Usuário do Azure MySQL
        password='Gnbg6twvJp9cqFR',                  # Senha do Azure MySQL
        database='tccalignme',                       # Nome do banco
        port=3306,                                   # Porta padrão
        ssl_disabled=True  # ⬅️ Esta linha desabilita SSL
    )
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pessoa (
            id INTEGER AUTO_INCREMENT PRIMARY KEY,
            cpf VARCHAR(11) NOT NULL UNIQUE,
            nome TEXT NOT NULL,
            data_nascimento TEXT NOT NULL,
            peso REAL,
            raca TEXT,
            profissao TEXT,
            telefone TEXT,
            tipo_corporal TEXT,
            idade INTEGER,
            sexo TEXT
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
    idade = data.get("idade")  # novo campo
    sexo = data.get("sexo")    # novo campo

    if not cpf or not nome or not data_nascimento:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Campos obrigatórios faltando"
        )
    
    if not validar_cpf(cpf):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CPF inválido"
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

        cursor.execute("""
            INSERT INTO pessoa (
                cpf, nome, data_nascimento, peso, raca, profissao,
                telefone, tipo_corporal, idade, sexo
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            cpf, nome, data_nascimento, peso, raca, profissao,
            telefone, tipo_corporal, idade, sexo
        ))

        conn.commit()
        conn.close()

        return JSONResponse(content={"mensagem": "Paciente cadastrado com sucesso!"})

    except pymysql.IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="CPF já cadastrado"
        )
    except Exception as e:
        print("ERRO AO CADASTRAR PACIENTE:", e)  # 👈 loga no terminal
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
        
@router.get("/listar-pacientes")
def listar_pacientes():
    conn = pymysql.connect(
        host='tccalignme.mysql.database.azure.com', # Host do Azure MySQL
        user='adminuser',                            # Usuário do Azure MySQL
        password='Gnbg6twvJp9cqFR',                  # Senha do Azure MySQL
        database='tccalignme',                       # Nome do banco
        port=3306,                                   # Porta padrão
        ssl_disabled=True  # ⬅️ Esta linha desabilita SSL
    )
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, idade, sexo FROM pessoa")
    pacientes = cursor.fetchall()
    conn.close()

    return [{"id": p[0], "nome": p[1], "idade": p[2], "sexo": p[3]} for p in pacientes]