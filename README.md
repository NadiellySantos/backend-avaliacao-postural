# Backend — Sistema computacional para avaliação postural mediante fotogrametria 🧍‍♀️🧍‍♂️📏

Este repositório contém o código responsável pelo processamento de **avaliações posturais** utilizada no sistema web AlignMe.  
O backend é construído com **FastAPI**, utilizando **MediaPipe** para extração de landmarks corporais, armazenando informações em **MySQL (Azure)** e expondo endpoints completos para:

- Cadastro e listagem de médicos  
- Cadastro e listagem de pacientes
- Login de médicos
- Processamento de imagens (vistas frontal e sagital)  
- Cadastro de avaliações (incluindo imagens e medidas)  
- Histórico de avaliações por paciente

---

# 📁 Estrutura do Projeto
```bash
backend-avaliacao-postural/
├── app/
│   ├── __init__.py
│   ├── main.py          # Ponto de entrada FastAPI + endpoint frontal
│   ├── sagital.py       # Endpoint de processamento sagital
│   ├── pacientes.py     # CRUD de pacientes + criação de tabela PESSOA
│   ├── medicos.py       # CRUD de médicos + criação de tabela MEDICO
│   ├── login.py         # Autenticação de médicos (bcrypt)
│   ├── avaliacao.py     # Cadastro de avaliação (avaliação_medica)
│   ├── historico.py     # Histórico de avaliações por paciente
│   ├── pacientes.db     # (arquivo antigo – hoje o backend usa MySQL)
│   └── pacientes.sqbpro # Projeto de banco
├── Dockerfile
├── requirements.txt
├── runtime.txt          # Versão do Python (python-3.10)
├── package.json         
└── README.md
```
---

# 🚀 Tecnologias Utilizadas

## Linguagem e Framework
- **Python 3.10+**
- **FastAPI** — framework para criação de APIs
- **Uvicorn** — servidor ASGI para rodar a API

## Visão computacional
- **MediaPipe Pose** — extração de 33 landmarks corporais
- **OpenCV (cv2)** — leitura e conversão de imagens
- **NumPy** — cálculos vetoriais e geométricos
- **Math** — trigonometria para cálculo de ângulos posturais

## Banco de Dados

- **MySQL** (hospedado no Azure)
- Conexão realizada via:
  - pymysql (pymysql.install_as_MySQLdb())
- Tabelas criadas dinamicamente se não existirem:
  - pessoa (pacientes)
  - medico (médicos)
  - avaliacao_medica (avaliações)
  - consultas sobre essa estrutura em **pacientes.py**, **medicos.py**, **avaliacao.py**, **historico.py**

## Visão Computacional / Processamento de Imagem
- **opencv-python-headless** — leitura/decodificação e desenho de imagens
- **numpy** — operações de distância, raiz quadrada, vetores
- **base64** — codificação de imagens processadas para retornar ao frontend

## Segurança e Autenticação
- bcrypt — hashing de senha de médicos
- Validação de:
  - **CPF**
  - **senha forte** (mínimo de caracteres, maiúscula, minúscula, número e caractere especial)

## Outros
- python-multipart — suportar upload de arquivos via multipart/form-data
- CORS configurado para:
  - http://localhost:3000
  - https://polite-beach-00fc32300.3.azurestaticapps.net

---

# 🧩 Módulos do Projeto e Suas Responsabilidades

## 🔹 `app/main.py` — API Principal + Avaliação Frontal
- Endpoint: POST /process-image
  Recebe:
  - file: imagem frontal (JPEG/PNG)
  - referencia_pixels: valor em pixels correspondente a 100 cm na imagem
  - debug: booleano opcional

  Processamento:
  1. Imagem é decodificada via OpenCV
  2. Marcadores brancos são detectados
  3. Pontos são ordenados verticalmente e horizontalmente
  4. Linhas anatômicas são conectadas
  5. Distâncias são calculadas:
  ```bash
    distancia_cm = distancia_pixels × (100 / referencia_pixels)
  ```
  6. Imagem final é codificada em base64
  7. Caso debug seja true: máscaras intermediárias são retornadas
    Resposta:
  ```bash
  {
  "image": "<base64>",
  "distancias": [
    {
      "ponto1": "ACD",
      "ponto2": "ACE",
      "descricao": "Acrômio direito - Acrômio esquerdo",
      "distancia_cm": 37.2
    }
  ],
  "pontos_detectados": [[x1, y1], [x2, y2], ...],
  "referencia_pixels": 250
  }

---

## 🔹 `app/sagital.py` — Avaliação Lateral (Sagital)
- Endpoint: POST /process-image-sagital
  Recebe:
  - imagem com marcadores laterais
  - pontos de referência (ref_x1, ref_y1, ref_x2, ref_y2)
  - referência real em metros

  Processamento:
  1. Marcadores brancos são detectados
  2. Pontos são ordenados verticalmente e horizontalmente
  3. Distâncias são calculadas e convertidas para centímetros
  4. Calcula ângulos usando produto escalar:
  ```bash
    θ = arccos( (AB · CB) / (|AB| |CB|) )
  ```
    Resposta:
   ```bash
    {
      "image": "<base64>",
      "distancias": [...],
      "angulos": [...],
      "escala_cm_por_pixel": 0.42
    }
  ```
---

## 🔹 `app/pacientes.py` — Cadastro de Pacientes
Tabela: pessoa
  Campos incluem:
  - id
  - cpf
  - nome
  - idade
  - sexo
  - data_nascimento

**Endpoints**
**Método**	→ **Rota**	→ **Descrição**
POST	→ /cadastrar-paciente →	Cadastra paciente
GET	→ /listar-pacientes	→ Lista pacientes

**Validação:**
- CPF
- Campos obrigatórios

---

## 🔹 `app/medicos.py` — Cadastro de Pacientes
Tabela: pessoa
  Campos incluem:
  - id_medico
  - cpf
  - nome
  - especialidade
  - crm
  - email
  - senha hash (bcrypt)

**Endpoints**
**Método**	→ **Rota**	→ **Descrição**
POST	→ /cadastrar-medico →	Cadastra com senha forte
GET	→ /listar-medicos	→ Lista médicos

**Validação:**
- CPF
- Senha forte
- Email único

---

## 🔹 `app/login.py` — Login de Médicos
- Endpoint: POST /login
  Recebe:
   ```bash
  { "email": "...", "senha": "..." }
  ```
  Valida senha via:
   ```bash
  bcrypt.checkpw(senha_digitada, hash_db)
  ```
  Retorna:
  ```bash
  {
  "mensagem": "Login realizado com sucesso",
  "nome": "Fulano",
  "token": "fake-token-123"
  }
  ```

---

## 🔹 `app/avaliacao.py` — Registro de Avaliação
Tabela: avaliacao_medica
  Campos incluem:
  - id_avaliacao
  - id_paciente
  - fots (base64)
  - medidas frontais e sagitais
  - ângulos sagitais
  - altura
  - resultado_avaliacao
  - data_avaliacao

**Endpoints**
  POST	→ /cadastrar-avaliacao
Valida campos obrigatórios, converte altura para float e insere no MySQL.

---

## 🔹 `app/historico.py` — Histórico de Avaliações
- Endpoint: GET /historico/{id_paciente}
  Retorna todas as avaliações ordenadas por data (mais recente primeiro).
  Exemplo:
   ```bash
  [
  {
    "id_avaliacao": 1,
    "foto_frontal": "<base64>",
    "resultado_avaliacao": "Desvio postural discreto",
    "data_avaliacao": "2025-02-01"
  }
  ]
  ```

---

  ## 🐳 Docker

  O Dockerfile deve ser ajustado para:

   ```bash
  CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
  ```

  Build:

  ```bash
  docker build -t avaliacao-backend .
  ```

  Run:

  ```bash
  docker run -p 8000:8000 avaliacao-backend
  ```

---
  
  ## 🧪 Como Rodar o Projeto
  
  1. Criar ambiente virtual
  ```bash
  python -m venv venv
  source venv/bin/activate      # Linux/macOS
  venv\Scripts\activate         # Windows
  ```
  
  2. Instalar dependências
  ```bash
  pip install -r requirements.txt
  ```
  
  3. Rodar servidor FastAPI
  ```bash
  uvicorn app.main:app --reload
  ```
  
  4. Acessar documentação interativa Swagger
  ```bash
  [pip install -r requirements.txt](http://localhost:8000/docs)
  ```

---

  ## 🐳 Rodando com Docker
  Build da imagem:
  ```bash
  docker build -t avaliacao-postural-backend .
  ```
  
  Executar:
  ```bash
  docker run -p 8000:8000 avaliacao-postural-backend
  ```

---
  
  ## 📌 Fluxo geral da aplicação
  Frontend Web → Backend FastAPI → MediaPipe Pose → Cálculo de Ângulos → Histórico → Retorno JSON

---
  
  ## 👥 Autores
  
  - **Claudia Galindo Santos**
  - **Mayara Silva Azevedo**
  - **Nadiélly Oliveira Santos**
  
---

## Projeto desenvolvido para o Trabalho de Conclusão de Curso em Engenharia da Computação, na Faculdade Engenheiro Salvador Arena - 2025.
