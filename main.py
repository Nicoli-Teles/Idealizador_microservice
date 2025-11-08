from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sqlite3
import bcrypt
from database import criar_tabelas
from models import Idealizador, Habilidade

# =============================
# CONFIGURAÇÃO DO APP
# =============================
app = FastAPI(title="Cadastro de Idealizadores")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # libera para todos os domínios (pode restringir depois)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# cria as tabelas se não existirem
criar_tabelas()

# =============================
# ROTAS BÁSICAS
# =============================
@app.get("/")
def home():
    return {"mensagem": "API de Cadastro funcionando 🚀"}

# =============================
# CADASTRO
# =============================
@app.post("/cadastro")
def cadastrar(idealizador: Idealizador):
    conexao = sqlite3.connect("banco.db")
    cursor = conexao.cursor()

    senha_criptografada = bcrypt.hashpw(idealizador.senha.encode('utf-8'), bcrypt.gensalt())

    try:
        cursor.execute("""
            INSERT INTO idealizadores (nome, telefone, email, senha, github, linkedin, funcao, pais, cidade, sobre_mim)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            idealizador.nome,
            idealizador.telefone,
            idealizador.email,
            senha_criptografada,
            idealizador.github,
            idealizador.linkedin,
            idealizador.funcao,
            idealizador.pais,
            idealizador.cidade,
            idealizador.sobre_mim
        ))
        conexao.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="E-mail já cadastrado.")
    finally:
        conexao.close()

    return {"mensagem": "Idealizador cadastrado com sucesso!"}


# =============================
# LOGIN
# =============================
class Login(BaseModel):
    email: str
    senha: str

@app.post("/login")
def login(credenciais: Login):
    conexao = sqlite3.connect("banco.db")
    cursor = conexao.cursor()
    cursor.execute("SELECT id, senha, nome FROM idealizadores WHERE email = ?", (credenciais.email,))
    resultado = cursor.fetchone()
    conexao.close()

    if not resultado:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    id_usuario, senha_armazenada, nome = resultado
    if bcrypt.checkpw(credenciais.senha.encode('utf-8'), senha_armazenada):
        return {"mensagem": f"Bem-vindo {nome}!", "id": id_usuario}
    else:
        raise HTTPException(status_code=401, detail="Senha incorreta")


# =============================
# PERFIL (GET e PUT)
# =============================

@app.get("/perfil/{idealizador_id}")
def obter_perfil(idealizador_id: int):
    conexao = sqlite3.connect("banco.db")
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT id, nome, telefone, email, github, linkedin, funcao, pais, cidade, sobre_mim
        FROM idealizadores WHERE id = ?
    """, (idealizador_id,))
    resultado = cursor.fetchone()

    if not resultado:
        conexao.close()
        raise HTTPException(status_code=404, detail="Perfil não encontrado")

    perfil = {
        "id": resultado[0],
        "nome": resultado[1] or "",
        "telefone": resultado[2] or "",
        "email": resultado[3] or "",
        "github": resultado[4] or "",
        "linkedin": resultado[5] or "",
        "funcao": resultado[6] or "",
        "pais": resultado[7] or "",
        "cidade": resultado[8] or "",
        "sobre_mim": resultado[9] or ""
    }

    # 🔹 Buscar habilidades
    cursor.execute("SELECT nome FROM habilidades WHERE idealizador_id = ?", (idealizador_id,))
    habilidades = [h[0] for h in cursor.fetchall()]

    conexao.close()
    perfil["habilidades"] = habilidades
    return perfil


class AtualizacaoPerfil(BaseModel):
    nome: Optional[str] = None
    telefone: Optional[str] = None
    github: Optional[str] = None
    linkedin: Optional[str] = None
    funcao: Optional[str] = None
    pais: Optional[str] = None
    cidade: Optional[str] = None
    sobre_mim: Optional[str] = None
    email: Optional[str] = None


@app.put("/perfil/{idealizador_id}")
def atualizar_perfil(idealizador_id: int, dados: AtualizacaoPerfil):
    conexao = sqlite3.connect("banco.db")
    cursor = conexao.cursor()

    # Atualiza apenas os campos enviados
    campos = []
    valores = []

    for campo, valor in dados.dict().items():
        if valor is not None:
            campos.append(f"{campo} = ?")
            valores.append(valor)

    if not campos:
        raise HTTPException(status_code=400, detail="Nenhum dado enviado para atualizar.")

    valores.append(idealizador_id)
    query = f"UPDATE idealizadores SET {', '.join(campos)} WHERE id = ?"
    cursor.execute(query, valores)
    conexao.commit()
    conexao.close()

    return {"mensagem": "Perfil atualizado com sucesso!"}


# =============================
# HABILIDADES
# =============================
@app.get("/habilidades/{idealizador_id}")
def listar_habilidades(idealizador_id: int):
    conexao = sqlite3.connect("banco.db")
    cursor = conexao.cursor()
    cursor.execute("SELECT nome FROM habilidades WHERE idealizador_id = ?", (idealizador_id,))
    habilidades = [linha[0] for linha in cursor.fetchall()]
    conexao.close()
    return {"habilidades": habilidades}


@app.post("/habilidades/{idealizador_id}")
def salvar_habilidades(idealizador_id: int, habilidades: list[str]):
    conexao = sqlite3.connect("banco.db")
    cursor = conexao.cursor()

    # Remove as antigas
    cursor.execute("DELETE FROM habilidades WHERE idealizador_id = ?", (idealizador_id,))

    # Insere as novas
    for nome in habilidades:
        cursor.execute("INSERT INTO habilidades (idealizador_id, nome) VALUES (?, ?)", (idealizador_id, nome))

    conexao.commit()
    conexao.close()

    return {"mensagem": "Habilidades atualizadas com sucesso!"}

    # =============================
# EXCLUIR PERFIL (E HABILIDADES RELACIONADAS)
# =============================
@app.delete("/perfil/{idealizador_id}")
def excluir_perfil(idealizador_id: int):
    conexao = sqlite3.connect("banco.db")
    cursor = conexao.cursor()

    # Verifica se o idealizador existe
    cursor.execute("SELECT id FROM idealizadores WHERE id = ?", (idealizador_id,))
    if not cursor.fetchone():
        conexao.close()
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    try:
        # 🔹 Primeiro, exclui as habilidades associadas
        cursor.execute("DELETE FROM habilidades WHERE idealizador_id = ?", (idealizador_id,))

        # 🔹 Depois, exclui o idealizador
        cursor.execute("DELETE FROM idealizadores WHERE id = ?", (idealizador_id,))

        conexao.commit()
    except Exception as e:
        conexao.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao excluir perfil: {e}")
    finally:
        conexao.close()

    return {"mensagem": "Perfil e habilidades excluídos com sucesso!"}

