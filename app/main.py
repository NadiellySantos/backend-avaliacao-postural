from fastapi import FastAPI, File, UploadFile
from fastapi.responses import Response
import cv2
import numpy as np

app = FastAPI()

def detectar_marcadores_brancos(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 220, 255, cv2.THRESH_BINARY)

    # Morfologia para remover ruído e melhorar os contornos
    kernel = np.ones((5, 5), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

    # Detecta contornos
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    pontos = []

    for cnt in contours:
        (x, y), radius = cv2.minEnclosingCircle(cnt)
        if radius > 4:  # evita ruído
            pontos.append((int(x), int(y)))

    # Ordena por eixo Y (de cima pra baixo), e em seguida por X (esquerda pra direita)
    pontos = sorted(pontos, key=lambda p: (p[1], p[0]))

    return pontos

def desenhar_linhas_com_conexoes(img, pontos):
    # Exemplo de conexões baseadas na imagem fornecida
    conexoes = [
        (0, 1), (0, 2), (1, 3), (2, 4),    # Ombros e braços
        (0, 5),                            # Ombro até quadril
        (5, 6),                            # Quadris
        (3, 7), (4, 8),                    # Braço até mão
        (5, 9), (6, 10),                   # Quadril até joelho
        (9, 11), (10, 12),                 # Joelho até pé
        (5, 6), (6, 10), (10, 12),         # Lado direito inferior
        (5, 9), (9, 11),                   # Lado esquerdo inferior
        (0, 13), (13, 14), (14, 15)        # Centro vertical (cabeça → pés)
    ]

    for i, ponto in enumerate(pontos):
        cv2.circle(img, ponto, 8, (0, 255, 0), -1)  # ponto verde

    for i, j in conexoes:
        if i < len(pontos) and j < len(pontos):
            cv2.line(img, pontos[i], pontos[j], (0, 255, 255), 4)  # amarelo

@app.post("/process-image")
async def process_image(file: UploadFile = File(...)):
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        return {"error": "Erro ao processar imagem"}

    pontos = detectar_marcadores_brancos(img)
    desenhar_linhas_com_conexoes(img, pontos)

    _, img_encoded = cv2.imencode(".jpg", img)
    return Response(content=img_encoded.tobytes(), media_type="image/jpeg")
