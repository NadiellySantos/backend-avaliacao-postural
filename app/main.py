from fastapi import FastAPI, File, UploadFile
from fastapi.responses import Response
import cv2
import numpy as np
import mediapipe as mp

app = FastAPI()

@app.post("/process-image")
async def process_image(file: UploadFile = File(...)):
    contents = await file.read()
    print('processando imagem...')
    # converte para array NumPy
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        return {"error": "Erro ao processar imagem"}

    # MediaPipe (aqui só vamos marcar o centro por enquanto)
    height, width, _ = img.shape
    center_x, center_y = width // 2, height // 2
    cv2.circle(img, (center_x, center_y), 40, (0, 255, 0), -1)  # verde e maior


    # Encode de volta para JPEG
    _, img_encoded = cv2.imencode(".jpg", img)
    return Response(content=img_encoded.tobytes(), media_type="image/jpeg")
