from flask import Flask, render_template_string, request, render_template, redirect, url_for, session, flash,jsonify
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date

app = Flask(__name__)
app.secret_key = '17081966'
import os
from werkzeug.utils import secure_filename

app.config['UPLOAD_FOLDER'] = os.path.join('static', 'assets')
from datetime import timedelta
app.permanent_session_lifetime = timedelta(minutes=30)

# ---------------------- CONEXÃO COM O BANCO ----------------------
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="17081966",
        database="cailla"
    )

# ---------------------- ROTAS PÚBLICAS ----------------------
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/sobre')
def sobre():
    return render_template('sobre.html')

@app.route('/membros')
def membros():
    return render_template('membros.html')

@app.route('/contato')
def contato():
    return render_template('contato.html')

# ---------------------- CADASTRO ----------------------

@app.route('/cadastro', methods=['GET'])
def cadastro():
    error = request.args.get('error')
    return render_template('cadastro.html', error=error)

@app.route('/cadastro_cliente', methods=['POST'])
def cadastro_cliente():
    cpf = request.form['cpf']
    nome = request.form['nome']
    email = request.form['email']
    senha = request.form['senha']
    confirmar_senha = request.form['confirmar_senha']
    endereco = request.form['endereco']
    telefone = request.form['telefone']

    if senha != confirmar_senha:
        return redirect(url_for('cadastro', error="As senhas não coincidem."))

    senha_hash = generate_password_hash(senha)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM CLIENTE WHERE IdCliente = %s", (cpf,))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return redirect(url_for('cadastro', error="CPF já cadastrado."))

    cursor.execute("SELECT * FROM CLIENTE WHERE email = %s", (email,))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return redirect(url_for('cadastro', error="E-mail já cadastrado."))

    cursor.execute("""
        INSERT INTO CLIENTE (IdCliente, nome, email, senha, endereco, telefone)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (cpf, nome, email, senha_hash, endereco, telefone))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('cadastro_success'))


@app.route('/cadastro_success')
def cadastro_success():
    return render_template('cadastro_success.html')

# ---------------------- LOGIN, CONTA E LOGOUT ----------------------
@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        next_url = request.form.get('next') or url_for('conta')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM CLIENTE WHERE email = %s", (email,))
        cliente = cursor.fetchone()
        cursor.close()
        conn.close()

        if cliente and check_password_hash(cliente['senha'], senha):
            session['usuario_id'] = cliente['IdCliente']
            session['nome_usuario'] = cliente['nome']
            session['is_admin'] = cliente.get('is_admin', False)

            return redirect(next_url)

        return render_template('perfil.html', error="E-mail ou senha inválidos.", next=next_url)

    # Aqui pega o `next` da URL (GET)
    next_url = request.args.get('next') or ''
    return render_template('perfil.html', next=next_url)

@app.route('/conta')
def conta():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM CLIENTE WHERE IdCliente = %s", (session['usuario_id'],))
    cliente = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template('conta.html', cliente=cliente)

@app.route('/atualizar_conta', methods=['POST'])
def atualizar_conta():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    email = request.form['email']
    senha = request.form['senha']
    telefone = request.form['telefone']
    endereco = request.form['endereco']

    conn = get_db_connection()
    cursor = conn.cursor()

    if senha.strip():
        hash_senha = generate_password_hash(senha)
        cursor.execute("""
            UPDATE CLIENTE SET email=%s, senha=%s, telefone=%s, endereco=%s WHERE IdCliente=%s
        """, (email, hash_senha, telefone, endereco, session['usuario_id']))
    else:
        cursor.execute("""
            UPDATE CLIENTE SET email=%s, telefone=%s, endereco=%s WHERE IdCliente=%s
        """, (email, telefone, endereco, session['usuario_id']))

    conn.commit()
    cursor.close()
    conn.close()

    flash("Dados atualizados com sucesso!")
    return redirect(url_for('conta'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))
@app.route('/meus_pedidos')
def meus_pedidos():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT p.IdPedido, p.data, p.status, p.valorTotal,
               i.quantidade, pr.nome AS nome_produto, pr.imagem, i.subtotal
        FROM PEDIDO p
        LEFT JOIN ITEMPEDIDO i ON p.IdPedido = i.IdPedido
        LEFT JOIN PRODUTO pr ON i.IdProduto = pr.IdProduto
        WHERE p.IdCliente = %s
        ORDER BY p.data DESC
    """, (session['usuario_id'],))

    resultados = cursor.fetchall()

    pedidos_dict = {}
    for row in resultados:
        pid = row['IdPedido']
        if pid not in pedidos_dict:
            pedidos_dict[pid] = {
                'IdPedido': pid,
                'data': row['data'],
                'status': row['status'],
                'valorTotal': row['valorTotal'],
                'itens': []
            }
        pedidos_dict[pid]['itens'].append({
            'nome': row['nome_produto'],
            'quantidade': row['quantidade'],
            'imagem': row['imagem'],
            'subtotal': row['subtotal']
        })

    pedidos = list(pedidos_dict.values())
    cursor.close()
    conn.close()

    return render_template('meus_pedidos.html', pedidos=pedidos)





# ---------------------- LOJA & CARRINHO ----------------------

@app.route('/loja')
@app.route('/loja')
def loja():
    categoria = request.args.get('categoria')
    ordem = request.args.get('ordem')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT IdProduto, nome, preco, descricao, imagem 
        FROM PRODUTO 
        WHERE ativo = TRUE
    """
    params = []

    if categoria:
        query += " AND LOWER(nome) LIKE %s"
        params.append(f"%{categoria.lower()}%")

    if ordem == "menor_preco":
        query += " ORDER BY preco ASC"
    elif ordem == "maior_preco":
        query += " ORDER BY preco DESC"
    else:
        query += " ORDER BY IdProduto DESC"

    cursor.execute(query, params)
    produtos = cursor.fetchall()

    # Pegando produtos favoritados, se o usuário estiver logado
    favoritos = set()
    if 'usuario_id' in session:
        cursor.execute("SELECT IdProduto FROM WISHLIST WHERE IdCliente = %s", (session['usuario_id'],))
        favoritos = set(row['IdProduto'] for row in cursor.fetchall())

    cursor.close()
    conn.close()

    return render_template('loja.html', produtos=produtos, favoritos=favoritos)


@app.route('/carrinho')
def show_cart():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    cart = session.get('cart', [])
    total_cart = sum(item['preco'] * item['quantidade'] for item in cart)
    return render_template('carrinho.html', cart=cart, total_cart=total_cart)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    produto_id = int(data['id'])
    nome = data['nome']
    preco = float(data['preco'])
    imagem = data['imagem']
    tamanho = data['tamanho']

    if 'cart' not in session:
        session['cart'] = []

    cart = session['cart']

    for item in cart:
        if item['id'] == produto_id and item.get('tamanho') == tamanho:
            item['quantidade'] += 1
            break
    else:
        cart.append({
            'id': produto_id,
            'nome': nome,
            'preco': preco,
            'quantidade': 1,
            'imagem': imagem,
            'tamanho': tamanho
        })

    session['cart'] = cart
    session.modified = True

    total_itens = sum(item['quantidade'] for item in cart)

    preview_html = render_template_string("""
        {% for item in cart %}
          <div class="cart-item-preview">
            <img src="{{ url_for('static', filename='assets/' + item['imagem']) }}" alt="{{ item['nome'] }}">
            <div>
              <p class="nome">{{ item['nome'] }}</p>
              <p>{{ item['quantidade'] }}x R$ {{ item['preco'] }}</p>
            </div>
          </div>
        {% endfor %}
        <a href="{{ url_for('show_cart') }}" class="ver-carrinho">Ver carrinho</a>
    """, cart=cart)

    return jsonify({
        'sucesso': True,
        'total_itens': total_itens,
        'preview_html': preview_html
    })


@app.route('/remove_from_cart/<int:produto_id>/<tamanho>')
def remove_from_cart(produto_id, tamanho):
    cart = session.get('cart', [])
    cart = [item for item in cart if not (int(item['id']) == produto_id and item['tamanho'] == tamanho)]
    session['cart'] = cart
    session.modified = True
    return redirect(url_for('show_cart'))


@app.route('/update_quantity/<int:produto_id>', methods=['POST'])
def update_quantity(produto_id):
    data = request.get_json()
    new_quantity = int(data['quantity'])
    tamanho = data.get('tamanho')

    cart = session.get('cart', [])
    for item in cart:
        if int(item['id']) == produto_id and item.get('tamanho') == tamanho:
            item['quantidade'] = new_quantity
            break

    session['cart'] = cart
    session.modified = True

    total_itens = sum(item['quantidade'] for item in cart)
    total_carrinho = sum(item['preco'] * item['quantidade'] for item in cart)

    return jsonify({
        'mensagem': 'Quantidade atualizada com sucesso!',
        'total_itens': total_itens,
        'total_carrinho': f"{total_carrinho:.2f}"
    })


@app.route('/pagamento', methods=['GET'])
def pagamento():
    if not session.get('cart'):
        return redirect(url_for('show_cart'))

    if 'usuario_id' not in session:
        return redirect(url_for('login', next=url_for('pagamento')))

    cart = session.get('cart', [])
    subtotal = sum(item['preco'] * item['quantidade'] for item in cart)

    return render_template('pagamento.html', subtotal=subtotal)


@app.route('/processar_pagamento', methods=['POST'])
def processar_pagamento():
    if 'usuario_id' not in session:
        flash("Sua sessão expirou. Faça login novamente.")
        return redirect(url_for('login'))
    if not session.get('cart'):
        flash("Seu carrinho está vazio. Adicione produtos antes de finalizar a compra.")
        return redirect(url_for('show_cart'))

    cart = session['cart']
    total = sum(item['preco'] * item['quantidade'] for item in cart)
    data_hoje = date.today()

    endereco = request.form['endereco']
    cidade = request.form['cidade']
    estado = request.form['estado']
    cep = request.form['cep']
    bairro = request.form.get('bairro')  # Pode ser None se não estiver preenchido
    metodo_pagamento = request.form.get('metodo_pagamento', 'cartao')
    parcelas = int(request.form.get('parcelas', 1))

    conn = get_db_connection()
    cursor = conn.cursor()

    for item in cart:
        cursor.execute("""
            SELECT quantidade FROM ESTOQUE
            WHERE IdProduto = %s AND tamanho = %s
        """, (item['id'], item['tamanho']))
        resultado = cursor.fetchone()
        if not resultado or resultado[0] < item['quantidade']:
            cursor.close()
            conn.close()
            flash(f"Estoque insuficiente para {item['nome']} tamanho {item['tamanho']}.")
            return redirect(url_for('show_cart'))

    frete = float(request.form.get('frete_valor', 0))
    valor_total_completo = total + frete

    cursor.execute("""
                   INSERT INTO PEDIDO (IdCliente, data, status, valorTotal, frete)
                   VALUES (%s, %s, %s, %s, %s)
                   """, (session['usuario_id'], data_hoje, "Confirmado", valor_total_completo, frete))
    conn.commit()
    pedido_id = cursor.lastrowid

    for item in cart:
        subtotal = item['preco'] * item['quantidade']
        cursor.execute("""
            INSERT INTO ITEMPEDIDO (IdPedido, IdProduto, quantidade, subtotal, tamanho)
            VALUES (%s, %s, %s, %s, %s)
        """, (pedido_id, item['id'], item['quantidade'], subtotal, item.get('tamanho')))
        cursor.execute("""
            UPDATE ESTOQUE
            SET quantidade = quantidade - %s
            WHERE IdProduto = %s AND tamanho = %s
        """, (item['quantidade'], item['id'], item['tamanho']))

    cursor.execute("""
        INSERT INTO PAGAMENTO (IdPedido, dataPagamento, valor, metodoDePagamento, parcelas)
        VALUES (%s, %s, %s, %s, %s)
    """, (pedido_id, data_hoje, valor_total_completo, metodo_pagamento, parcelas))

    cursor.execute("""
                   INSERT INTO ENDERECO_ENTREGA (IdPedido, endereco, cidade, estado, cep, bairro)
                   VALUES (%s, %s, %s, %s, %s, %s)
                   """, (pedido_id, endereco, cidade, estado, cep, bairro))

    if metodo_pagamento == "cartao":
        numero_cartao = request.form.get('numero_cartao', '').strip()
        nome_cartao = request.form.get('nome_cartao', '').strip()
        validade = request.form.get('validade', '').strip()
        cvv = request.form.get('cvv', '').strip()

        if not all([numero_cartao, nome_cartao, validade, cvv]):
            flash("Por favor, preencha todos os dados do cartão.")
            return redirect(url_for('pagamento'))

        cursor.execute("""
            INSERT INTO DADOS_CARTAO (IdPedido, nomeTitular, numeroCartao, validade, cvv)
            VALUES (%s, %s, %s, %s, %s)
        """, (pedido_id, nome_cartao, numero_cartao, validade, cvv))

    conn.commit()
    cursor.close()
    conn.close()

    session['cart'] = []
    session.modified = True
    return redirect(url_for('pedido_realizado', pedido_id=pedido_id))

@app.route('/pedido-realizado')
def pedido_realizado():
    pedido_id = request.args.get('pedido_id')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM PEDIDO WHERE IdPedido = %s", (pedido_id,))
    pedido = cursor.fetchone()

    cursor.execute("""
        SELECT i.quantidade, i.subtotal, p.nome
        FROM ITEMPEDIDO i
        JOIN PRODUTO p ON i.IdProduto = p.IdProduto
        WHERE i.IdPedido = %s
    """, (pedido_id,))
    itens = cursor.fetchall()

    cursor.execute("SELECT * FROM PAGAMENTO WHERE IdPedido = %s", (pedido_id,))
    pagamento = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template('pedido_finalizado.html', pedido=pedido, itens=itens, pagamento=pagamento)
@app.route('/cadastrar_membro', methods=['POST'])
def cadastrar_membro():
    nome = request.form['nome']
    email = request.form['email']

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO MEMBRO (nome, email)
        VALUES (%s, %s)
    """, (nome, email))

    conn.commit()
    cursor.close()
    conn.close()

    flash("Cadastro realizado com sucesso! 💌")
    return redirect(url_for('membros'))
@app.route('/faq')
def faq():
    return render_template('faq.html')

@app.route('/envio')
def envio():
    return render_template('envio.html')

@app.route('/politica')
def politica():
    return render_template('politica.html')

@app.route('/metodos')
def metodos():
    return render_template('metodos.html')
@app.route('/inscrever_newsletter', methods=['POST'])
def inscrever_newsletter():
    email = request.form['email']

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO NEWSLETTER (email) VALUES (%s)", (email,))
        conn.commit()
    except mysql.connector.IntegrityError:
        pass  # Email já cadastrado
    cursor.close()
    conn.close()

    return redirect(url_for('home'))
@app.route('/produto/<int:id>', methods=['GET', 'POST'])
def produto(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Buscar o produto
    cursor.execute("SELECT * FROM PRODUTO WHERE IdProduto = %s", (id,))
    produto = cursor.fetchone()

    if not produto:
        cursor.close()
        conn.close()
        return "Produto não encontrado", 404

    # Se o usuário estiver logado e enviando uma avaliação
    if request.method == 'POST' and 'usuario_id' in session:
        nota = int(request.form['nota'])
        comentario = request.form['comentario']
        data_hoje = date.today()

        cursor.execute("""
            INSERT INTO AVALIACAO (IdProduto, IdCliente, nota, comentario, data)
            VALUES (%s, %s, %s, %s, %s)
        """, (id, session['usuario_id'], nota, comentario, data_hoje))
        conn.commit()

    # Buscar avaliações do produto
    cursor.execute("""
        SELECT a.nota, a.comentario, a.data, c.nome
        FROM AVALIACAO a
        JOIN CLIENTE c ON a.IdCliente = c.IdCliente
        WHERE a.IdProduto = %s
        ORDER BY a.data DESC
    """, (id,))
    avaliacoes = cursor.fetchall()

    # Buscar imagens extras
    cursor.execute("""
        SELECT caminho FROM IMAGEM_PRODUTO WHERE produto_id = %s
    """, (id,))
    imagens_extras = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('produto.html', produto=produto, avaliacoes=avaliacoes, imagens_extras=imagens_extras)

@app.route('/calcular_frete', methods=['POST'])
def calcular_frete():
    cep = request.form.get('cep')

    # Exemplo simples de regra de frete
    if cep.startswith('01'):  # SP capital
        frete = 10.00
        prazo = "2 a 3 dias úteis"
    elif cep.startswith('2'):  # Interior
        frete = 15.00
        prazo = "3 a 5 dias úteis"
    else:
        frete = 20.00
        prazo = "5 a 7 dias úteis"

    return {'frete': frete, 'prazo': prazo}
from datetime import date

@app.route('/adicionar_wishlist', methods=['POST'])
def adicionar_wishlist():
    if 'usuario_id' not in session:
        flash('Você precisa estar logado para adicionar aos favoritos.')
        return redirect(url_for('login'))

    id_cliente = session['usuario_id']
    id_produto = request.form['id_produto']

    conn = get_db_connection()
    cursor = conn.cursor()

    # Verifica se já está na wishlist
    cursor.execute("""
        SELECT * FROM WISHLIST WHERE IdCliente = %s AND IdProduto = %s
    """, (id_cliente, id_produto))
    existe = cursor.fetchone()

    if not existe:
        cursor.execute("""
            INSERT INTO WISHLIST (IdCliente, IdProduto)
            VALUES (%s, %s)
        """, (id_cliente, id_produto))
        conn.commit()
        flash('Produto adicionado aos favoritos!')
    else:
        flash('Produto já está nos seus favoritos.')

    cursor.close()
    conn.close()
    return redirect(request.referrer)
@app.route('/wishlist')
def wishlist():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT p.IdProduto, p.nome, p.preco, p.imagem
        FROM WISHLIST w
        JOIN PRODUTO p ON w.IdProduto = p.IdProduto
        WHERE w.IdCliente = %s
    """, (session['usuario_id'],))

    favoritos = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('wishlist.html', favoritos=favoritos)
@app.route('/remover_wishlist/<int:id_produto>', methods=['POST'])
def remover_wishlist(id_produto):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM WISHLIST WHERE IdCliente = %s AND IdProduto = %s
    """, (session['usuario_id'], id_produto))
    conn.commit()
    cursor.close()
    conn.close()

    flash('Produto removido dos favoritos.')
    return redirect(request.referrer)
@app.route('/blog')
def blog():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT C.texto, C.data, CL.nome AS nome_usuario
        FROM COMENTARIO C
        JOIN CLIENTE CL ON C.usuario_id = CL.IdCliente
        ORDER BY C.data DESC
    """)
    comentarios = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('blog.html', comentarios=comentarios)


# Painel Admin - Visualizar Produtos e Estoques
@app.route('/admin/produtos')
def admin_produtos():
    if not session.get('is_admin'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM PRODUTO WHERE ativo = TRUE")
    produtos = cursor.fetchall()

    for produto in produtos:
        cursor.execute("""
            SELECT tamanho, quantidade
            FROM ESTOQUE
            WHERE IdProduto = %s
        """, (produto['IdProduto'],))
        estoques = cursor.fetchall()
        produto['estoques'] = {e['tamanho']: e['quantidade'] for e in estoques}

    cursor.close()
    conn.close()

    return render_template('admin_produtos.html', produtos=produtos)


@app.route('/admin_adicionar', methods=['GET', 'POST'])
def admin_adicionar():
    if request.method == 'POST':
        nome = request.form['nome']
        descricao = request.form['descricao']
        preco = float(request.form['preco'])
        imagem = request.form['imagem']  # nome do arquivo principal
        imagens_extras = request.files.getlist('imagens_extras')

        # Limitar a 4 imagens extras
        if len(imagens_extras) > 4:
            imagens_extras = imagens_extras[:4]

        conn = get_db_connection()
        cursor = conn.cursor()

        # Inserir produto
        cursor.execute("""
            INSERT INTO PRODUTO (nome, descricao, preco, imagem)
            VALUES (%s, %s, %s, %s)
        """, (nome, descricao, preco, imagem))
        produto_id = cursor.lastrowid

        # Salvar imagens extras no servidor e registrar no banco
        for img in imagens_extras:
            if img and img.filename:
                filename = secure_filename(img.filename)
                path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                img.save(path)

                cursor.execute("""
                    INSERT INTO IMAGEM_PRODUTO (produto_id, caminho)
                    VALUES (%s, %s)
                """, (produto_id, filename))

        # Inserir estoque
        for tamanho, campo in zip(['P', 'M', 'G', 'GG'],
                                  ['estoque_p', 'estoque_m', 'estoque_g', 'estoque_gg']):
            quantidade = int(request.form.get(campo, 0))
            if quantidade > 0:
                cursor.execute("""
                    INSERT INTO ESTOQUE (IdProduto, tamanho, quantidade)
                    VALUES (%s, %s, %s)
                """, (produto_id, tamanho, quantidade))

        conn.commit()
        cursor.close()
        conn.close()
        flash('Produto adicionado com sucesso!')
        return redirect(url_for('admin_produtos'))

    return render_template('admin_adicionar.html')


@app.route('/admin/editar/<int:produto_id>', methods=['GET', 'POST'])
def editar_produto(produto_id):
    if not session.get('is_admin'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'GET':
        cursor.execute("SELECT * FROM PRODUTO WHERE IdProduto = %s", (produto_id,))
        produto = cursor.fetchone()

        cursor.execute("SELECT tamanho, quantidade FROM ESTOQUE WHERE IdProduto = %s", (produto_id,))
        estoques = cursor.fetchall()
        produto['estoques'] = {e['tamanho']: e['quantidade'] for e in estoques}

        cursor.close()
        conn.close()

        return render_template('admin_editar.html', produto=produto)

    # POST
    nome = request.form['nome']
    descricao = request.form['descricao']
    preco = request.form['preco']

    nova_imagem = request.files.get('nova_imagem')
    imagem_atual = request.form['imagem_atual']

    # Se enviou nova imagem principal
    if nova_imagem and nova_imagem.filename:
        filename = secure_filename(nova_imagem.filename)
        caminho = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        nova_imagem.save(caminho)
        imagem = filename
    else:
        imagem = imagem_atual

    # Atualiza produto
    cursor.execute("""
        UPDATE PRODUTO SET nome=%s, descricao=%s, preco=%s, imagem=%s
        WHERE IdProduto=%s
    """, (nome, descricao, preco, imagem, produto_id))

    # Atualiza estoque
    for tamanho in ['P', 'M', 'G', 'GG']:
        quantidade = int(request.form.get(f'estoque_{tamanho.lower()}', 0))
        cursor.execute("SELECT * FROM ESTOQUE WHERE IdProduto = %s AND tamanho = %s", (produto_id, tamanho))
        existe = cursor.fetchone()
        if existe:
            cursor.execute("""
                UPDATE ESTOQUE SET quantidade = %s
                WHERE IdProduto = %s AND tamanho = %s
            """, (quantidade, produto_id, tamanho))
        else:
            cursor.execute("""
                INSERT INTO ESTOQUE (IdProduto, tamanho, quantidade)
                VALUES (%s, %s, %s)
            """, (produto_id, tamanho, quantidade))

    # Novas imagens extras
    imagens_extras = request.files.getlist('imagens_extras')
    if len(imagens_extras) > 4:
        imagens_extras = imagens_extras[:4]

    for img in imagens_extras:
        if img and img.filename:
            filename = secure_filename(img.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            img.save(path)

            cursor.execute("""
                INSERT INTO IMAGEM_PRODUTO (produto_id, caminho)
                VALUES (%s, %s)
            """, (produto_id, filename))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('admin_produtos'))


@app.route('/admin/excluir/<int:produto_id>', methods=['POST'])
def excluir_produto(produto_id):
    if not session.get('is_admin'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Excluir imagens extras relacionadas ao produto
    cursor.execute("DELETE FROM IMAGEM_PRODUTO WHERE produto_id = %s", (produto_id,))

    # 2. Excluir estoque relacionado
    cursor.execute("DELETE FROM ESTOQUE WHERE IdProduto = %s", (produto_id,))

    # 3. Excluir o produto
    cursor.execute("UPDATE PRODUTO SET ativo = FALSE WHERE IdProduto = %s", (produto_id,))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('admin_produtos'))


@app.route('/admin/relatorio')
def admin_relatorio():
    if not session.get('is_admin'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Produtos mais vendidos
    cursor.execute("""
        SELECT P.nome, SUM(I.quantidade) as total_vendido
        FROM ITEMPEDIDO I
        JOIN PRODUTO P ON I.IdProduto = P.IdProduto
        GROUP BY P.nome
        ORDER BY total_vendido DESC
        LIMIT 5
    """)

    produtos_vendidos = cursor.fetchall()

    # Tamanhos mais vendidos
    cursor.execute("""SELECT tamanho, SUM(quantidade) AS total
    FROM ITEMPEDIDO
    GROUP BY tamanho
    ORDER BY
    total DESC;
""")
    tamanhos_vendidos = cursor.fetchall()

    # Receita por mês
    cursor.execute("""
        SELECT DATE_FORMAT(P.data, '%m/%Y') AS mes, SUM(P.valorTotal) AS receita
        FROM PEDIDO P
        GROUP BY mes
        ORDER BY STR_TO_DATE(CONCAT('01/', mes), '%d/%m/%Y') ASC
    """)
    receita_mensal = cursor.fetchall()

    # Clientes que mais compram
    cursor.execute("""
        SELECT C.nome, SUM(P.valorTotal) AS total_gasto
        FROM CLIENTE C
        JOIN PEDIDO P ON C.IdCliente = P.IdCliente
        GROUP BY C.nome
        ORDER BY total_gasto DESC
        LIMIT 5
    """)
    clientes_top = cursor.fetchall()

# Estados com mais vendas
    cursor.execute("""
                   SELECT E.estado, COUNT(*) AS total_vendas
                   FROM ENDERECO_ENTREGA E
                            JOIN PEDIDO P ON E.IdPedido = P.IdPedido
                   GROUP BY E.estado
                   ORDER BY total_vendas DESC
                   """)
    estados_vendas = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'admin_relatorio.html',
        produtos_vendidos=produtos_vendidos,
        tamanhos_vendidos=tamanhos_vendidos,
        receita_mensal=receita_mensal,
        clientes_top=clientes_top,
        estados_vendas=estados_vendas
    )
@app.route('/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('login'))
@app.route('/admin/pedidos')
def admin_pedidos():
    if not session.get('is_admin'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM PEDIDO ORDER BY data DESC")
    pedidos_raw = cursor.fetchall()
    pedidos = []

    for pedido in pedidos_raw:
        pedido_id = pedido['IdPedido']

        # Dados do cliente
        cursor.execute("SELECT nome, email FROM CLIENTE WHERE IdCliente = %s", (pedido['IdCliente'],))
        cliente = cursor.fetchone()

        # Endereço de entrega
        cursor.execute("""
                       SELECT endereco, bairro, cidade, estado, cep
                       FROM ENDERECO_ENTREGA
                       WHERE IdPedido = %s
                       """, (pedido_id,))
        entrega = cursor.fetchone() or {
            'endereco': '',
            'bairro': '',
            'cidade': '',
            'estado': '',
            'cep': ''
        }
        # Método de pagamento + parcelas
        cursor.execute("""
            SELECT metodoDePagamento, parcelas
            FROM PAGAMENTO
            WHERE IdPedido = %s
        """, (pedido_id,))
        pagamento = cursor.fetchone() or {}
        metodo = pagamento.get('metodoDePagamento', 'N/A')
        parcelas = pagamento.get('parcelas', 1)

        # Itens do pedido
        cursor.execute("""
            SELECT I.quantidade, I.subtotal, I.tamanho, P.nome, P.imagem
            FROM ITEMPEDIDO I
            JOIN PRODUTO P ON I.IdProduto = P.IdProduto
            WHERE I.IdPedido = %s
        """, (pedido_id,))
        itens = cursor.fetchall()

        pedidos.append({
            'IdPedido': pedido_id,
            'data': pedido['data'],
            'status': pedido['status'],
            'frete': pedido.get('frete', 0),
            'valorTotal': pedido['valorTotal'],
            'cliente': cliente,
            'entrega': entrega,
            'metodo': metodo,
            'parcelas': parcelas,
            'itens': itens
        })

    cursor.close()
    conn.close()

    return render_template('admin_pedidos.html', pedidos=pedidos)
@app.route('/finalizar_compra')
def finalizar_compra():
    if 'usuario_id' not in session:
        return redirect(url_for('login', next=url_for('pagamento')))
    return redirect(url_for('pagamento'))

@app.route('/add_to_cart_form', methods=['POST'])
def add_to_cart_form():
    produto_id = int(request.form['id'])
    nome = request.form['nome']
    preco = float(request.form['preco'])
    imagem = request.form['imagem']
    tamanho = request.form['tamanho']

    if 'cart' not in session:
        session['cart'] = []

    cart = session['cart']

    # Verifica se já existe no carrinho
    for item in cart:
        if item['id'] == produto_id and item['tamanho'] == tamanho:
            item['quantidade'] += 1
            break
    else:
        cart.append({
            'id': produto_id,
            'nome': nome,
            'preco': preco,
            'quantidade': 1,
            'imagem': imagem,
            'tamanho': tamanho
        })

    session['cart'] = cart
    session.modified = True

    return redirect(url_for('wishlist'))
@app.route('/admin/clientes')
def admin_clientes():
    if not session.get('is_admin'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM CLIENTE")
    clientes = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('admin_clientes.html', clientes=clientes)
@app.route('/admin/clientes/<id_cliente>/pedidos')
def admin_pedidos_cliente(id_cliente):
    if not session.get('is_admin'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Buscar cliente
    cursor.execute("SELECT * FROM CLIENTE WHERE IdCliente = %s", (id_cliente,))
    cliente = cursor.fetchone()

    # Buscar pedidos
    cursor.execute("SELECT * FROM PEDIDO WHERE IdCliente = %s ORDER BY data DESC", (id_cliente,))
    pedidos = cursor.fetchall()

    # Buscar itens de cada pedido
    pedidos_com_itens = []
    for pedido in pedidos:
        cursor.execute("""
            SELECT i.quantidade, i.subtotal, i.tamanho, p.nome
            FROM ITEMPEDIDO i
            JOIN PRODUTO p ON i.IdProduto = p.IdProduto
            WHERE i.IdPedido = %s
        """, (pedido['IdPedido'],))
        itens = cursor.fetchall()
        pedido['itens'] = itens
        pedidos_com_itens.append(pedido)

    cursor.close()
    conn.close()

    return render_template('admin_pedidos_cliente.html', cliente=cliente, pedidos=pedidos_com_itens)
@app.route('/admin/contatos')
def admin_contatos():
    if not session.get('is_admin'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM CONTATO ORDER BY idContato DESC")
    contatos = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('admin_contatos.html', contatos=contatos)

@app.route('/salvar_contato', methods=['POST'])
def salvar_contato():
    nome = request.form['nome']
    email = request.form['email']
    mensagem = request.form['mensagem']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO CONTATO (nome, email, mensagem, dataEnvio)
        VALUES (%s, %s, %s, NOW())
    """, (nome, email, mensagem))
    conn.commit()
    cursor.close()
    conn.close()

    flash("Mensagem enviada com sucesso!")
    return redirect(url_for('contato'))


@app.route('/admin/estoque')
def admin_estoque():
    if not session.get('is_admin'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
                   SELECT p.IdProduto, p.nome AS nome_produto, e.tamanho, e.quantidade
                   FROM ESTOQUE e
                            JOIN PRODUTO p ON e.IdProduto = p.IdProduto
                   ORDER BY p.nome, e.tamanho
                   """)
    estoque = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('admin_estoque.html', estoque=estoque)

@app.route('/admin/avaliacoes')
def admin_avaliacoes():
    if not session.get('is_admin'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT A.IdAvaliacao, A.nota, A.comentario, A.data,
               C.nome AS nome_cliente, P.nome AS nome_produto
        FROM AVALIACAO A
        JOIN CLIENTE C ON A.IdCliente = C.IdCliente
        JOIN PRODUTO P ON A.IdProduto = P.IdProduto
        ORDER BY A.data DESC
    """)
    avaliacoes = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('admin_avaliacoes.html', avaliacoes=avaliacoes)
@app.route('/comentar_video', methods=['POST'])
def comentar_video():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    usuario_id = session['usuario_id']
    texto = request.form['comentario']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO COMENTARIO (usuario_id, texto, data)
        VALUES (%s, %s, NOW())
    """, (usuario_id, texto))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('blog'))

@app.route('/admin/atualizar_status/<int:pedido_id>', methods=['POST'])
def atualizar_status(pedido_id):
    if not session.get('is_admin'):
        return redirect(url_for('login'))

    novo_status = request.form['status']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE PEDIDO SET status = %s WHERE IdPedido = %s", (novo_status, pedido_id))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('admin_pedidos'))


if __name__ == '__main__':
    app.run(debug=True)


