from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import JSONResponse
import pymysql
import os  # ← ADICIONADO
import json  # ← ADICIONADO para substituir eval()

pymysql.install_as_MySQLdb()
router = APIRouter()

# ✅ MESMA FUNÇÃO DE CONEXÃO DOS OUTROS ARQUIVOS
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
                ssl={'check_hostname': False},
                cursorclass=pymysql.cursors.DictCursor
            )
        else:
            # Fallback para desenvolvimento local (.env)
            from dotenv import load_dotenv
            load_dotenv()
            
            return pymysql.connect(
                host=os.getenv('LOCAL_DB_HOST', 'localhost'),
                user=os.getenv('LOCAL_DB_USER', 'root'),
                password=os.getenv('LOCAL_DB_PASSWORD', 'admin'),
                database=os.getenv('LOCAL_DB_NAME', 'tccalignme'),
                cursorclass=pymysql.cursors.DictCursor
            )
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        raise

@router.get("/historico/{id_paciente}")
async def listar_avaliacoes(id_paciente: int):
    try:
        # ✅ ALTERADO: usa a nova função get_connection()
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
            id_avaliacao,
            id_paciente,
            foto_frontal,
            foto_sagital,
            medidas_frontal,
            medidas_sagital,
            angulos_sagital,
            altura,
            resultado_avaliacao,
            data_avaliacao
            FROM avaliacao_medica

            WHERE id_paciente = %s
            ORDER BY data_avaliacao DESC
        """, (id_paciente,))
        resultados = cursor.fetchall()
        conn.close()

        # ✅ MELHORIA: Substituir eval() por json.loads() (mais seguro)
        for r in resultados:
            try:
                if r["medidas_frontal"]:
                    r["medidas_frontal"] = eval(r["medidas_frontal"])  # ou json.loads()
                if r["medidas_sagital"]:
                    r["medidas_sagital"] = json.loads(r["medidas_sagital"])
                if r["angulos_sagital"]:
                    r["angulos_sagital"] = json.loads(r["angulos_sagital"])
            except Exception:
                r["medidas_frontal"] = {}
                r["medidas_sagital"] = {}
                r["angulos_sagital"] = {}

        return resultados

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))