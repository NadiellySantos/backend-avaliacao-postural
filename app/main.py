from fastapi import FastAPI, File, UploadFile
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np

app = FastAPI()

# Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def detectar_marcadores_brancos(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 220, 255, cv2.THRESH_BINARY)

    kernel = np.ones((5, 5), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    pontos = []

    for cnt in contours:
        (x, y), radius = cv2.minEnclosingCircle(cnt)
        if radius > 4:
            pontos.append((int(x), int(y)))

    pontos = sorted(pontos, key=lambda p: (p[1], p[0]))

    return pontos

def desenhar_linhas_com_conexoes(img, pontos):
    conexoes = [
        (0, 1), 
        (0, 2), 
        (1, 3), 
        # (2, 4),
        # (0, 5), 
        (3, 7), 
        (4, 8),
        (5, 9), 
         
        (5, 4),
        (5, 1), 
        (2, 6), 
        (8, 10), 
        (10, 13),
        (11, 12),
        (9, 11), 
        (0, 4),
        
        (13, 14), 
        (14, 15)
    ]

    for ponto in pontos:
        cv2.circle(img, ponto, 8, (0, 255, 0), -1)

    for i, j in conexoes:
        if i < len(pontos) and j < len(pontos):
            cv2.line(img, pontos[i], pontos[j], (0, 255, 255), 4)

@app.post("/process-image")
async def process_image(file: UploadFile = File(...)):
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        return {"error": "Erro ao processar imagem"}

    pontos = detectar_marcadores_brancos(img)
    print("Pontos detectados:", pontos)

    desenhar_linhas_com_conexoes(img, pontos)

    _, img_encoded = cv2.imencode(".jpg", img)
    return Response(content=img_encoded.tobytes(), media_type="image/jpeg")
