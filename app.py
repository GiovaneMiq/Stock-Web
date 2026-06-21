from flask import Flask, render_template, request, redirect, url_for, flash
import json
import os
from datetime import datetime

ARQUIVO_HISTORICO = 'historico.json'

app = Flask(__name__)
app.secret_key = 'chave-secreta-stock-web'
ARQUIVO = 'estoque.json'

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
        flash('Nome inválido!', 'error')
        return redirect(url_for('index'))
    try:
        qtd = int(request.form["quantidade"])
        preco = float(request.form["preco"])
    except ValueError:
        flash('Quantidade e preço devem ser números!', 'error')
        return redirect(url_for('index'))

    estoque = load_estoque()
    if nome in estoque:
        flash('Produto já existe! Use a busca para editar.', 'error')
        return redirect(url_for('index'))

    estoque[nome] = {'quantidade': qtd, 'preco': preco}
    save_estoque(estoque)
    flash(f'Produto "{nome}" adicionado com sucesso!', 'success')

    registrar_evento('adição', nome, f'Qtd: {qtd}, Preço: R$ {preco:.2f}')

    return redirect(url_for('index'))

@app.route("/remover/<nome>")
def remover(nome):
    estoque = load_estoque()
    nome = nome.lower()
    if nome in estoque:
        del estoque[nome]
        registrar_evento('remoção', nome, 'Produto removido')
        save_estoque(estoque)
        flash(f'Produto "{nome}" removido.', 'success')
    else:
        flash('Produto não encontrado.', 'error')
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

