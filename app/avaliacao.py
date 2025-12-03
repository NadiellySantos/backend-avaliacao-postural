from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
import pymysql
import os

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
                database=os.getenv('LOCAL_DB_NAME', 'alignme')
            )
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        raise

# ✅ Função para criar a tabela automaticamente
def criar_tabela():
    try:
        # ✅ ALTERADO: Usa a nova função get_connection()
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS avaliacao_medica (
                id_avaliacao INTEGER AUTO_INCREMENT PRIMARY KEY,
                id_paciente INTEGER NOT NULL,
                foto_frontal LONGTEXT,
                foto_sagital LONGTEXT,
                medidas_frontal TEXT,
                medidas_sagital TEXT,
                angulos_sagital TEXT,
                altura DOUBLE,
                resultado_avaliacao TEXT,
                data_avaliacao TEXT NOT NULL
            )
            """)
        conn.commit()
        print("✅ Tabela 'avaliacao_medica' verificada/criada com sucesso.")
    except Exception as e:
        print("❌ Erro ao criar/verificar tabela:", e)
    finally:
        if conn.is_connected():
            conn.close()


criar_tabela()


@router.post("/cadastrar-avaliacao")
async def cadastrar_avaliacao(request: Request):
    try:
        data = await request.json()
        print("📦 Dados recebidos no backend:", data)
    except Exception as e:
        print("❌ Erro ao ler JSON:", e)
        raise HTTPException(status_code=400, detail="JSON inválido")

    id_paciente = data.get("id_paciente")
    foto_frontal = data.get("foto_frontal")
    foto_sagital = data.get("foto_sagital")
    medidas_frontal = data.get("medidas_frontal")
    medidas_sagital = data.get("medidas_sagital")
    altura = data.get("altura")
    resultado = data.get("resultado_avaliacao")
    data_avaliacao = data.get("data_avaliacao")
    angulos_sagital = data.get("angulos_sagital")

    # ✅ Converte altura para float se possível
    try:
        altura = float(altura) if altura not in (None, "", "null") else None
    except ValueError:
        altura = None

    # ✅ Validação dos campos obrigatórios
    if not id_paciente or not foto_frontal or not foto_sagital or not data_avaliacao:
        print("⚠️ Campos obrigatórios faltando.")
        raise HTTPException(
            status_code=400,
            detail="Campos obrigatórios: id_paciente, foto_frontal, foto_sagital, data_avaliacao"
        )

    # ✅ Inserção no banco de dados
    try:
        # ✅ ALTERADO: Usa a nova função get_connection()
        conn = get_connection()
        
        with conn.cursor() as cursor:
           cursor.execute("""
                INSERT INTO avaliacao_medica (
                    id_paciente, foto_frontal, foto_sagital,
                    medidas_frontal, medidas_sagital, angulos_sagital,
                    altura, resultado_avaliacao, data_avaliacao
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                id_paciente,
                foto_frontal,
                foto_sagital,
                medidas_frontal,
                medidas_sagital,
                angulos_sagital,   # ← NOVO
                altura,
                resultado,
                data_avaliacao
            ))

        conn.commit()
        print("✅ Avaliação cadastrada com sucesso no banco!")
        return JSONResponse(content={"mensagem": "Avaliação cadastrada com sucesso!"})

    except mysql.connector.Error as err:
        print("❌ Erro do MySQL:", err)
        raise HTTPException(status_code=500, detail=f"Erro MySQL: {err}")

    except Exception as e:
        print("❌ Erro inesperado:", e)
        raise HTTPException(status_code=500, detail=f"Erro interno: {e}")

    finally:
        if conn.is_connected():
            conn.close()