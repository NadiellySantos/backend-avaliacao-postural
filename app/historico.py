from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import JSONResponse
import pymysql
pymysql.install_as_MySQLdb()

router = APIRouter()

@router.get("/historico/{id_paciente}")
async def listar_avaliacoes(id_paciente: int):
    try:
        conn = pymysql.connect(
            host='tccalignme.mysql.database.azure.com', # Host do Azure MySQL
            user='adminuser',                            # Usuário do Azure MySQL
            password='Gnbg6twvJp9cqFR',                  # Senha do Azure MySQL
            database='tccalignme',                       # Nome do banco
            port=3306                                   # Porta padrão
        )
        cursor = conn.cursor(pymysql.cursors.DictCursor)
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

        # Converter medidas JSON para objeto
        for r in resultados:
            try:
                if r["medidas_frontal"]:
                    r["medidas_frontal"] = eval(r["medidas_frontal"])  # ou json.loads()
                if r["medidas_sagital"]:
                    r["medidas_sagital"] = eval(r["medidas_sagital"])
                if r["angulos_sagital"]:
                    r["angulos_sagital"] = eval(r["angulos_sagital"])
            except Exception:
                r["medidas_frontal"] = []
                r["medidas_sagital"] = []

        return resultados

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))