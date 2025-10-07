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


# Nomes dos pontos (seguindo protocolo anatômico)
# Lista de pontos identificados (na mesma ordem do algoritmo de detecção)
nomes = [
    "ACD",   # 0
    "ACE",  # 1
    "EAE",# 2
    "EAD",# 3
    "CUE",   # 4
    "CUD",  # 5
    "TFD", # 6
    "TFE",# 7
    "LJD",  # 8
    "LJE", # 9
    "TTD",# 10
    "TTE",# 11
    "MLD",# 12
    "MLE" # 13
]

# Conexões entre os pontos (pares de índices)
conexoes = [
    (0, 3),   # Ombro esquerdo -> iliaca Direito
    (1, 2),   # Ombro Direito -> iliaca Esquerdo
    (2, 3),   # iliaca Direito -> Punho Direito    
    (0, 1),   # Ombro Direito -> Ombro Esquerdo
    (6, 8),   # Quadril Direito -> Joelho Direito
    (7, 9),   # Quadril esquerdo -> Joelho Esquerdo
    (8, 10),  # Joelho Direito -> Tornozelo Direito
    (9, 11),  # Joelho Esquerdo -> Tornozelo Esquerdo
    (10, 12), # Tornozelo Direito -> Calcanhar Direito
    (11, 13), # Tornozelo Esquerdo -> Calcanhar Esquerdo
    (2, 7),  # iliaca esquerda -> Quadril esquerdo
    (3, 6),  # iliaca direita -> Quadril direito
    (0, 5),  # ombro direita -> punho direito
    (1, 4),  # ombro esquerdo -> punho esquerdo
]


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
        y_key = round(p[1] / 50)  # agrupa por "faixa de altura"
        if y_key not in grupos:
            grupos[y_key] = []
        grupos[y_key].append(p)

    pontos_ordenados = []
    for _, grupo in sorted(grupos.items()):
        if len(grupo) == 2:
            grupo = sorted(grupo, key=lambda x: x[0])  # esquerda = menor X
            pontos_ordenados.extend(grupo)
        else:
            pontos_ordenados.extend(grupo)
    return pontos_ordenados


# 🔹 Desenhar os pontos e conexões
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

    # Detectar e organizar pontos
    pontos = detectar_marcadores_brancos(img)
    pontos = reordenar_pontos(pontos)

    desenhar_linhas_com_conexoes(img, pontos)

    # Escala: 1 metro = 100 cm
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
                "distancia_cm": dist_cm
            })

    _, img_encoded = cv2.imencode(".jpg", img)
    img_base64 = base64.b64encode(img_encoded).decode("utf-8")

    return {
        "image": img_base64,
        "distancias": distancias_cm,
        "referencia_pixels": referencia_pixels
    }
