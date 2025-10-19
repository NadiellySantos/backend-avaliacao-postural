from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import APIRouter
import cv2
import numpy as np
import base64
from app.pacientes import router as pacientes_router
from app.medicos import router as medicos_router
from app.login import router as login_router
from app.avaliacao import router as avaliacao_router
from app.historico import router as historico_router
from app.sagital import sagital_router

router = APIRouter()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Importando os routers
app.include_router(pacientes_router)
app.include_router(medicos_router)
app.include_router(login_router)
app.include_router(avaliacao_router)
app.include_router(historico_router)
app.include_router(sagital_router)


# 🔹 Nomes dos pontos (seguindo protocolo anatômico)
nomes = [
    "ACD",   # 0
    "ACE",   # 1
    "EAE",   # 2
    "EAD",   # 3
    "CRE",   # 4
    "CRD",   # 5
    "TFD",   # 6
    "TFE",   # 7
    "LJD",   # 8
    "LJE",   # 9
    "TTD",   # 10
    "TTE",   # 11
    "MLD",   # 12
    "MLE"    # 13
]

# 🔹 Conexões entre os pontos
conexoes = [
    (0, 3),
    (1, 2),
    (2, 3),
    (0, 1),
    (6, 8),
    (7, 9),
    (8, 10),
    (9, 11),
    (10, 12),
    (11, 13),
    (2, 7),
    (3, 6),
    (0, 5),
    (1, 4),
]

# 🔹 Descrições manuais para cada conexão
descricoes_conexoes = {
    (0, 3): "Acrômio Direito - Espinha ilíaca ântero-superior direita.",
    (1, 2): "Acrômio Esquerdo - Espinha ilíaca ântero-superior esquerda.",
    (2, 3): "Espinha ilíaca ântero-superior esquerda - Espinha ilíaca ântero-superior direita.",
    (0, 1): "Acrômio direito - Acrômio esquerdo",
    (6, 8): "Trocânter maior do fêmur direito - Linha articular do joelho direito",
    (7, 9): "Trocânter maior do fêmur esquerdo - Linha articular do joelho esquerdo",
    (8, 10): "Linha articular do joelho direito - Tuberosidade tibial direita.",
    (9, 11): "Linha articular do joelho esquerdo - Tuberosidade tibial esquerda.",
    (10, 12): "Tuberosidade tibial direita - Maléolo lateral direito.",
    (11, 13): "Tuberosidade tibial esquerda - Maléolo lateral esquerdo.",
    (2, 7): "Espinha ilíaca ântero-superior esquerda - Trocânter maior do fêmur esquerdo.",
    (3, 6): "Espinha ilíaca ântero-superior direita - Trocânter maior do fêmur direito.",
    (0, 5): "Acrômio direito - Cabeça do rádio direito.",
    (1, 4): "Acrômio esquerdo - Cabeça do rádio esquerdo.",
}

# 🔹 Detectar marcadores brancos
def detectar_marcadores_brancos(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 220, 255, cv2.THRESH_BINARY)
    kernel = np.ones((5, 5), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    pontos = [(int(x), int(y)) for cnt in contours
              if (radius := cv2.minEnclosingCircle(cnt)[1]) > 4
              for (x, y) in [cv2.minEnclosingCircle(cnt)[0]]]

    return sorted(pontos, key=lambda p: (p[1], p[0]))


# 🔹 Reordenar pontos em E/D
def reordenar_pontos(pontos):
    grupos = {}
    for p in pontos:
        y_key = round(p[1] / 50)
        if y_key not in grupos:
            grupos[y_key] = []
        grupos[y_key].append(p)

    pontos_ordenados = []
    for _, grupo in sorted(grupos.items()):
        if len(grupo) == 2:
            grupo = sorted(grupo, key=lambda x: x[0])
            pontos_ordenados.extend(grupo)
        else:
            pontos_ordenados.extend(grupo)
    return pontos_ordenados


# 🔹 Desenhar malha quadriculada
def desenhar_malha(img, spacing=50, color=(200, 200, 200), thickness=1):
    h, w = img.shape[:2]
    for x in range(0, w, spacing):
        cv2.line(img, (x, 0), (x, h), color, thickness)
    for y in range(0, h, spacing):
        cv2.line(img, (0, y), (w, y), color, thickness)
    return img


# 🔹 Desenhar pontos e conexões
def desenhar_linhas_com_conexoes(img, pontos):
    for idx, ponto in enumerate(pontos):
        x, y = ponto
        cv2.circle(img, (x, y), 8, (0, 255, 0), -1)
        if idx < len(nomes):
            cv2.putText(img, nomes[idx], (x + 10, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2, cv2.LINE_AA)
    for i, j in conexoes:
        if i < len(pontos) and j < len(pontos):
            cv2.line(img, pontos[i], pontos[j], (0, 255, 255), 2)


# 🔹 Rota principal
@app.post("/process-image")
async def process_image(file: UploadFile = File(...), referencia_pixels: float = Form(...)):
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        return JSONResponse(content={"error": "Erro ao processar imagem"}, status_code=400)

    pontos = detectar_marcadores_brancos(img)
    pontos = reordenar_pontos(pontos)

    desenhar_linhas_com_conexoes(img, pontos)
    img = desenhar_malha(img, spacing=50)

    escala_cm_por_pixel = 100 / referencia_pixels
    distancias_cm = []

    for i, j in conexoes:
        if i < len(pontos) and j < len(pontos):
            x1, y1 = pontos[i]
            x2, y2 = pontos[j]
            dist_px = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            dist_cm = round(dist_px * escala_cm_por_pixel, 2)

            distancias_cm.append({
                "ponto1": nomes[i] if i < len(nomes) else f"P{i}",
                "ponto2": nomes[j] if j < len(nomes) else f"P{j}",
                "distancia_cm": dist_cm,
                "descricao": descricoes_conexoes.get((i, j), "Ligação anatômica padrão")
            })

    _, img_encoded = cv2.imencode(".jpg", img)
    img_base64 = base64.b64encode(img_encoded).decode("utf-8")

    return {
        "image": img_base64,
        "distancias": distancias_cm,
        "referencia_pixels": referencia_pixels
    }
