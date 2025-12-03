from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import JSONResponse
import pymysql
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

# Cria a tabela PESSOA caso não exista, agora com idade e sexo
def criar_tabela():
    conn = get_connection()  # ← ALTERADO: usa nova função
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
        conn = get_connection()  # ← ALTERADO: usa nova função
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
    conn = get_connection()  # ← ALTERADO: usa nova função
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, idade, sexo FROM pessoa")
    pacientes = cursor.fetchall()
    conn.close()

    return [{"id": p[0], "nome": p[1], "idade": p[2], "sexo": p[3]} for p in pacientes]