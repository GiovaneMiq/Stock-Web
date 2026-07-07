from flask import Flask, render_template, request, redirect, url_for, flash
import json
import os
from datetime import datetime
from werkzeug.utils import secure_filename

ARQUIVO_HISTORICO = 'historico.json'

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'chave-secreta-stock-web'
ARQUIVO = 'estoque.json'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def load_estoque():
    if os.path.exists(ARQUIVO):
        with open(ARQUIVO, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_estoque(estoque):
    with open(ARQUIVO, 'w', encoding='utf-8') as f:
        json.dump(estoque, f, indent=4, ensure_ascii=False)

def carregar_historico():
    if os.path.exists(ARQUIVO_HISTORICO):
        try:
            with open(ARQUIVO_HISTORICO, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return []
    return []

def salvar_historico(historico):
    with open (ARQUIVO_HISTORICO, 'w', encoding='utf-8') as f:
        json.dump(historico, f, indent=4, ensure_ascii=False)

def registrar_evento(tipo, nome, detalhes):
    historico = carregar_historico()
    evento = {
        'data': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
        'tipo': tipo,
        'produto': nome,
        'detalhes': detalhes
    }
    historico.append(evento)
    salvar_historico(historico)

@app.route('/')
def index():
    estoque = load_estoque()

    return render_template('index.html', estoque=estoque)

@app.route("/adicionar", methods=["POST"])
def add():
    nome = request.form['nome'].strip().lower()

    if not nome:
        return "Nome inválido!", 400
    try:
        qtd = int(request.form["quantidade"])
        preco = float(request.form["preco"])
    except ValueError:
        return "Quantidade e preço devem ser números!", 400

    estoque = load_estoque()
    if nome in estoque:
        return "Produto já existe! Volte e use a busca para editar.", 400
    
    # upload das imagens dos produtos
    imagem = request.files.get('imagem')
    nome_imagem = None
    if imagem and imagem.filename != '':
        nome_imagem = secure_filename(imagem.filename)
        # timestamp para evitar duplicatas de nome
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        nome_imagem = f"{timestamp}_{nome_imagem}"
        caminho = os.path.join(app.config['UPLOAD_FOLDER'], nome_imagem)
        imagem.save(caminho)

    estoque[nome] = {
        'quantidade': qtd,
        'preco': preco,
        'imagem': nome_imagem
    }
    save_estoque(estoque)

    registrar_evento('adição', nome, f'Qtd: {qtd},  Preço: R$ {preco:.2f}')
    return redirect(url_for('index'))

@app.route("/remover/<nome>")
def remover(nome):
    estoque = load_estoque()
    nome = nome.lower()
    if nome in estoque:
        produto = estoque[nome]
        if produto.get('imagem'):
            caminho_imagem = os.path.join(app.config['UPLOAD_FOLDER'], produto['imagem'])
            if os.path.exists(caminho_imagem):
                os.remove(caminho_imagem)
        del estoque[nome]
        save_estoque(estoque)
        registrar_evento('remoção', nome, 'Produto removido')
    return redirect(url_for('index'))



@app.route("/atualizar/<nome>", methods=["POST"])
def atualizar(nome):

    try:
        nova_qtd = int(request.form['quantidade'])
    except ValueError:
        flash('Quantidade inválida!', 'error')
        return redirect(url_for('index'))

    estoque = load_estoque()

    nome = nome.lower()
    if nome in estoque:
        qtd_antiga = estoque[nome]['quantidade']
        estoque[nome]['quantidade'] = nova_qtd
        save_estoque(estoque)
        registrar_evento('atualização', nome, f'Qtd: {qtd_antiga} → {nova_qtd}')
        flash(f'Quantidade de "{nome}" atualizada!', 'success')
    else:
        flash('Produto não encontrado.', 'error')
    return redirect(url_for("index"))

@app.route("/buscar", methods=["GET"])
def buscar():
    termo = request.args.get('q', '').strip().lower()
    estoque = load_estoque()
    # Filtrar produtos por nome
    resultado = {nome: info for  nome, info in estoque.items() if termo in nome}
    return render_template("index.html", estoque=estoque, busca=termo, resultado=resultado)

@app.route('/historico')
def historico():
    historico = carregar_historico()
    #Inverte para mostrar os mais recentes
    historico_reverso = list(reversed(historico))
    return render_template('historico.html', historico=historico_reverso)

if __name__ == "__main__":
    app.run(debug=False)

