from flask import Flask, render_template, request, redirect, url_for
import json
import os

app = Flask(__name__)
ARQUIVO = 'estoque.json'

def load_estoque():
    if os.path.exists(ARQUIVO):
        with open(ARQUIVO, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_estoque(estoque):
    with open(ARQUIVO, 'w', encoding='utf-8') as f:
        json.dump(estoque, f, indent=4, ensure_ascii=False)

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
    
    estoque[nome] =  {'quantidade': qtd, 'preco': preco}
    save_estoque(estoque)

    return redirect(url_for('index'))

@app.route("/remover/<nome>")
def remover(nome):
    estoque = load_estoque()
    nome = nome.lower()
    if nome in estoque:

        del estoque[nome]
        save_estoque(estoque)
    return redirect(url_for('index'))

@app.route("/atualizar/<nome>", methods=["POST"])
def atualizar(nome):

    try:
        nova_qtd = int(request.form['quantidade'])
    except ValueError:
        return "Quantidade inválida!", 400
    
    estoque = load_estoque()

    nome = nome.lower()
    if nome in estoque:

        estoque[nome]['quantidade'] = nova_qtd
        save_estoque(estoque)
    return redirect(url_for("index"))

@app.route("/buscar", methods=["GET"])
def buscar():
    termo = request.args.get('q', '').strip().lower()
    estoque = load_estoque()
    # Filtrar produtos por nome
    resultado = {nome: info for  nome, info in estoque.items() if termo in nome}
    return render_template("index.html", estoque=estoque, busca=termo, resultado=resultado)

if __name__ == "__main__":
    app.run(debug=True)
