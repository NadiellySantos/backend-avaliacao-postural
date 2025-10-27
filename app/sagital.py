from fastapi import APIRouter, File, UploadFile, Form
from fastapi.responses import JSONResponse
import cv2
import numpy as np
import base64

sagital_router = APIRouter()

# 🔹 Nomes dos pontos anatômicos (sagital)
nomes = [
    "PEC7", "ACD", "PET7", "ELD", "CUD", "PEL4", "PERD",
    "EAD", "CCX", "TFD", "LJD", "TTD", "MLD"
]

# 🔹 Descrição completa dos pontos
descricoes_pontos = {
    "PEC7": "PEC7",
    "ACD": "ACD",
    "PET7": "PET7",
    "ELD": "ELD",
    "CUD": "CUD",
    "PEL4": "PEL4",
    "PERD": "PERD",
    "CCX": "CCX",
    "TFD": "TFD",
    "LJD": "LJD",
    "TTD": "TTD",
    "MLD": "MLD"
}

# 🔹 Conexões entre os pontos
conexoes = [
    (0, 1), (0, 2), (1, 3), (6, 4), (2, 5),
    (5, 7), (7, 9), (9, 10), (10, 11),
    (5, 8), (11, 12)
]

# 🔹 Descrições manuais das conexões (como no código frontal)
descricoes_conexoes = {
    (0, 1): "Processo espinhoso C7 - Acrômio direito.",
    (0, 2): "Processo espinhoso C7 - Processo espinhoso T5.",
    (1, 3): "Acrômio direito - Epicôndilo lateral direito.",
    (6, 4): "Cabeça da Ulna direita - Processo estilóide do rádio direito.",
    (2, 5): "Processo espinhoso T7 - Processo espinhoso L4.",
    (5, 7): "Processo espinhoso L4 - Espinha ilíaca ântero-superior direita..",
    (8, 9): "Espinha ilíaca ântero-superior direita - Trocânter maior do fêmur direito.",
    (9, 10): "Trocânter maior do fêmur direito - Linha articular do joelho direito.",
    (10, 11): "Linha articular do joelho direito - Tuberosidade tibial direita.",
    (5, 8): "Processo espinhoso L4 - Coccix",
    (11, 12): "Tuberosidade tibial direita - Maléolo lateral direito.",
}

# 🔹 Função para desenhar malha
def desenhar_malha(img, spacing=50, color=(200, 200, 200), thickness=1):
    h, w = img.shape[:2]
    for x in range(0, w, spacing):
        cv2.line(img, (x, 0), (x, h), color, thickness)
    for y in range(0, h, spacing):
        cv2.line(img, (0, y), (w, y), color, thickness)
    return img


# 🔹 Função para detectar marcadores brancos
def detectar_marcadores_brancos(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (7, 7), 0)
    _, thresh = cv2.threshold(blur, 200, 255, cv2.THRESH_BINARY)
    kernel = np.ones((3, 3), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=1)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    pontos = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 20 or area > 1500:
            continue
        (x, y), radius = cv2.minEnclosingCircle(cnt)
        perimeter = cv2.arcLength(cnt, True)
        circularidade = 0 if perimeter == 0 else (4 * np.pi * area) / (perimeter ** 2)
        if 0.7 < circularidade < 1.3 and 5 < radius < 30:
            mask = np.zeros_like(gray)
            cv2.circle(mask, (int(x), int(y)), int(radius), 255, -1)
            media_brilho = cv2.mean(gray, mask=mask)[0]
            if media_brilho > 180:
                pontos.append((int(x), int(y)))

    pontos = sorted(pontos, key=lambda p: (p[1], p[0]))
    return pontos


# 🔹 Função para calcular ângulo
def calcular_angulo(p1, p2, p3):
    a = np.array(p1)
    b = np.array(p2)
    c = np.array(p3)
    ba = a - b
    bc = c - b
    cos_ang = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    cos_ang = np.clip(cos_ang, -1.0, 1.0)
    angulo = np.degrees(np.arccos(cos_ang))
    return round(angulo, 2)


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


# 🔹 Rota principal
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

    pontos = detectar_marcadores_brancos(img)
    desenhar_linhas_com_conexoes(img, pontos)
    angulos_resultados = []

    if len(pontos) > 8:
        angulo_tronco = calcular_angulo(pontos[6], pontos[5], pontos[8])
        angulos_resultados.append({
            "nome": "PET7 - PEL4 - EAD",
            "pontos": ("2", "5", "7"),
            "angulo_graus": angulo_tronco
        })

        angulo_cotovelo = calcular_angulo(pontos[2], pontos[5], pontos[7])
        angulos_resultados.append({
            "nome": "PET7 - PEL4 - CCX",
            "pontos": ("2", "5", "8"),
            "angulo_graus": angulo_cotovelo
        })

    for angulo in angulos_resultados:
        p_central = pontos[int(angulo["pontos"][1])]
       
    desenhar_malha(img)

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
            distancias_cm.append({
                "ponto1": nomes[i] if i < len(nomes) else f"P{i}",
                "ponto2": nomes[j] if j < len(nomes) else f"P{j}",
                "descricao": descricoes_conexoes.get((i, j), "Ligação anatômica padrão"),
                "distancia_cm": dist_cm,
            })

    _, img_encoded = cv2.imencode(".jpg", img)
    img_base64 = base64.b64encode(img_encoded).decode("utf-8")

    return {
        "image": img_base64,
        "distancias": distancias_cm,
        "angulos": angulos_resultados,
        "escala_cm_por_pixel": escala_cm_por_pixel,
    }
