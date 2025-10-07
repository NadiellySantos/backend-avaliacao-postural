from fastapi import APIRouter, File, UploadFile, Form
from fastapi.responses import JSONResponse
import cv2
import numpy as np
import base64

sagital_router = APIRouter()

# Nomes dos pontos (sagital)
nomes = [
    "Trago (orelha)",  # 0
    "Acromio (ombro)",  # 1
    "Epicôndilo (cotovelo)",  # 2
    "Punho",  # 3
    "Trocânter (quadril)",  # 4
    "Joelho",  # 5
    "Tornozelo",  # 6
    "Calcâneo (calcanhar)",  # 7
    "5º metatarso",  # 8
]

# Conexões para formar o esqueleto sagital
conexoes = [
    (0, 1),  # cabeça -> ombro
    (1, 2),  # ombro -> cotovelo
    (2, 3),  # cotovelo -> punho
    (1, 4),  # ombro -> quadril
    (4, 5),  # quadril -> joelho
    (5, 6),  # joelho -> tornozelo
    (6, 7),  # tornozelo -> calcanhar
    (6, 8),  # tornozelo -> ponta pé
]

def detectar_marcadores_brancos(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 220, 255, cv2.THRESH_BINARY)
    kernel = np.ones((5, 5), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    contours, _ = cv2.findContours(
        thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    pontos = [
        (int(x), int(y))
        for cnt in contours
        if (radius := cv2.minEnclosingCircle(cnt)[1]) > 4
        for (x, y) in [cv2.minEnclosingCircle(cnt)[0]]
    ]

    return sorted(pontos, key=lambda p: p[1])

def desenhar_linhas_com_conexoes(img, pontos):
    for idx, ponto in enumerate(pontos):
        x, y = ponto
        cv2.circle(img, (x, y), 8, (0, 255, 0), -1)
        if idx < len(nomes):
            cv2.putText(
                img,
                nomes[idx],
                (x + 10, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 0),
                2,
                cv2.LINE_AA,
            )
    for i, j in conexoes:
        if i < len(pontos) and j < len(pontos):
            cv2.line(img, pontos[i], pontos[j], (0, 255, 255), 2)

@sagital_router.post("/process-image-sagital")
async def process_image_sagital(
    file: UploadFile = File(...),
    ref_x1: float = Form(...),
    ref_y1: float = Form(...),
    ref_x2: float = Form(...),
    ref_y2: float = Form(...),
    referencia_metros: float = Form(...),
):
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        return JSONResponse(
            content={"error": "Erro ao processar imagem"}, status_code=400
        )

    pontos = detectar_marcadores_brancos(img)
    desenhar_linhas_com_conexoes(img, pontos)

    dist_px_ref = np.sqrt((ref_x2 - ref_x1) ** 2 + (ref_y2 - ref_y1) ** 2)
    escala_metros_por_pixel = referencia_metros / dist_px_ref
    escala_cm_por_pixel = escala_metros_por_pixel * 100

    distancias_cm = []
    for i, j in conexoes:
        if i < len(pontos) and j < len(pontos):
            x1, y1 = pontos[i]
            x2, y2 = pontos[j]
            dist_px = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            dist_cm = round(dist_px * escala_cm_por_pixel, 2)
            distancias_cm.append(
                {
                    "ponto1": nomes[i] if i < len(nomes) else f"P{i}",
                    "ponto2": nomes[j] if j < len(nomes) else f"P{j}",
                    "distancia_cm": dist_cm,
                }
            )

    _, img_encoded = cv2.imencode(".jpg", img)
    img_base64 = base64.b64encode(img_encoded).decode("utf-8")

    return {
        "image": img_base64,
        "distancias": distancias_cm,
        "escala_cm_por_pixel": escala_cm_por_pixel,
    }