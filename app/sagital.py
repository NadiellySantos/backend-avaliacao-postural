from fastapi import APIRouter, File, UploadFile, Form
from fastapi.responses import JSONResponse
import cv2
import numpy as np
import base64

sagital_router = APIRouter()

# 🔹 Nomes dos pontos anatômicos (sagital)
nomes = [
    "0",         # 0
    "1",        # 1
    "2",  # 2
    "3",                  # 3
    "4",    # 4
    "5",                 # 5
    "6",              # 6
    "7",   # 7
    "8",
    "9",           # 8
    "10",          # 9
    "11",          # 10
    "12",           # 11
    "13"
]

# 🔹 Conexões entre os pontos
conexoes = [
    (0, 1),  # cabeça -> ombro
    (0, 2),
    (1, 3),  # ombro -> cotovelo
    (3, 4),  # ombro -> cotovelo
    (2, 5),  # cotovelo -> punho
    (5, 6),  # joelho -> tornozelo
    (5, 7),  # calcanhar -> ponta pé
    (8, 9),  # quadril -> joelho
    (9, 10),
    (10, 11),  # joelho -> tornozelo
    (5, 8),  # tornozelo -> calcanhar
    (11, 12)
]

# 🔹 Desenhar malha quadriculada
def desenhar_malha(img, spacing=50, color=(200, 200, 200), thickness=1):
    h, w = img.shape[:2]
    # Linhas verticais
    for x in range(0, w, spacing):
        cv2.line(img, (x, 0), (x, h), color, thickness)
    # Linhas horizontais
    for y in range(0, h, spacing):
        cv2.line(img, (0, y), (w, y), color, thickness)
    return img


# 🔹 Função aprimorada de detecção dos marcadores brancos
def detectar_marcadores_brancos(img):
    # Converte para escala de cinza
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Reduz ruídos visuais do fundo
    blur = cv2.GaussianBlur(gray, (7, 7), 0)

    # Detecta regiões realmente brancas
    _, thresh = cv2.threshold(blur, 200, 255, cv2.THRESH_BINARY)

    # Limpeza morfológica
    kernel = np.ones((3, 3), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=1)

    # Encontra contornos externos
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    pontos = []

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 20 or area > 1500:
            continue  # ignora muito pequenos ou muito grandes

        (x, y), radius = cv2.minEnclosingCircle(cnt)
        perimeter = cv2.arcLength(cnt, True)
        circularidade = 0 if perimeter == 0 else (4 * np.pi * area) / (perimeter ** 2)

        # Mantém apenas círculos pequenos e brancos
        if 0.7 < circularidade < 1.3 and 5 < radius < 30:
            mask = np.zeros_like(gray)
            cv2.circle(mask, (int(x), int(y)), int(radius), 255, -1)
            media_brilho = cv2.mean(gray, mask=mask)[0]
            if media_brilho > 180:
                pontos.append((int(x), int(y)))

    # Ordena de cima para baixo e esquerda para direita
    pontos = sorted(pontos, key=lambda p: (p[1], p[0]))
    return pontos


# 🔹 Função para desenhar pontos e conexões
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


# 🔹 Endpoint principal
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
        return JSONResponse(content={"error": "Erro ao processar imagem"}, status_code=400)

    # Detecta marcadores brancos reais
    pontos = detectar_marcadores_brancos(img)

    # Desenha pontos e conexões
    desenhar_linhas_com_conexoes(img, pontos)
    desenhar_malha(img)
    # Calcula a escala baseada na referência marcada manualmente
    dist_px_ref = np.sqrt((ref_x2 - ref_x1) ** 2 + (ref_y2 - ref_y1) ** 2)
    escala_metros_por_pixel = referencia_metros / dist_px_ref
    escala_cm_por_pixel = escala_metros_por_pixel * 100

    # Calcula as distâncias entre os pontos conectados
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
            })

    # Codifica a imagem com marcações em base64
    _, img_encoded = cv2.imencode(".jpg", img)
    img_base64 = base64.b64encode(img_encoded).decode("utf-8")

    return {
        "image": img_base64,
        "distancias": distancias_cm,
        "escala_cm_por_pixel": escala_cm_por_pixel,
    }
