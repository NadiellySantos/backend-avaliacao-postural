from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
import base64
from app.pacientes import router as pacientes_router
from app.medicos import router as medicos_router


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Importando o router de para cadastro de pacientes
app.include_router(pacientes_router)
app.include_router(medicos_router)


conexoes = [
    (0, 1), (0, 2), (1, 3), (3, 7), 
    (4, 8), (5, 9), (5, 4), (5, 1), 
    (2, 6), (8, 10), (10, 13), (11, 12),
    (9, 11), (0, 4), (13, 14), (14, 15)
]

nomes = [
    "ACD", "ACE", "ELD", "ELE", "EAD", "EAE", "CUD", "CUE",
    "TDF", "TDE", "LJD", "LJE", "MLE", "MLD", "P14", "P15"
]

def detectar_marcadores_brancos(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 220, 255, cv2.THRESH_BINARY)
    kernel = np.ones((5, 5), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    pontos = [(int(x), int(y)) for cnt in contours if (radius := cv2.minEnclosingCircle(cnt)[1]) > 4
              for (x, y) in [cv2.minEnclosingCircle(cnt)[0]]]
    return sorted(pontos, key=lambda p: (p[1], p[0]))

def desenhar_linhas_com_conexoes(img, pontos):
    for idx, ponto in enumerate(pontos):
        x, y = ponto
        cv2.circle(img, (x, y), 8, (0, 255, 0), -1)
        if idx < len(nomes):
            cv2.putText(img, nomes[idx], (x + 5, y - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 0), 1, cv2.LINE_AA)
    for i, j in conexoes:
        if i < len(pontos) and j < len(pontos):
            cv2.line(img, pontos[i], pontos[j], (0, 255, 255), 4)

@app.post("/process-image")
async def process_image(file: UploadFile = File(...), referencia_pixels: float = Form(...)):
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        return JSONResponse(content={"error": "Erro ao processar imagem"}, status_code=400)

    pontos = detectar_marcadores_brancos(img)
    desenhar_linhas_com_conexoes(img, pontos)

    # Calcular distâncias com base na referência
    escala_cm_por_pixel = 100 / referencia_pixels  # 1 metro = 100 cm
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
        "distancias": distancias_cm
    }
