document.addEventListener("DOMContentLoaded", function () {
  // Atualização de quantidade no carrinho
  document.querySelectorAll('.quantidade-input').forEach(function(input) {
    input.addEventListener('change', function(event) {
      const produtoId = event.target.getAttribute('data-id');
      const tamanho = event.target.getAttribute('data-tamanho');
      const quantidade = parseInt(event.target.value);

      fetch(`/update_quantity/${produtoId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          quantity: quantidade,
          tamanho: tamanho
        })
      })
      .then(response => response.json())
      .then(data => {
        console.log(data.mensagem);

        const badge = document.getElementById('cart-count');
        if (badge) {
          badge.textContent = data.total_itens;
          badge.style.display = data.total_itens > 0 ? 'inline-block' : 'none';
        }

        const totalSpan = document.getElementById('totalCarrinho');
        if (totalSpan) {
          totalSpan.textContent = data.total_carrinho.replace('.', ',');
        }
      })
      .catch(error => console.error('Erro:', error));
    });
  });

  // Visualização do carrinho ao passar o mouse
  const icon = document.getElementById('cart-icon');
  const preview = document.getElementById('cart-preview');

  if (icon && preview) {
    icon.addEventListener('mouseenter', () => {
      preview.style.display = 'block';
    });
    icon.addEventListener('mouseleave', () => {
      setTimeout(() => preview.style.display = 'none', 200);
    });
    preview.addEventListener('mouseenter', () => {
      preview.style.display = 'block';
    });
    preview.addEventListener('mouseleave', () => {
      preview.style.display = 'none';
    });
  }

  // Adicionar ao carrinho via AJAX
document.querySelectorAll('.btn-add-carrinho-ajax').forEach(btn => {
  btn.addEventListener('click', async function (e) {
    e.preventDefault();

    const id = this.dataset.id;
    const nome = this.dataset.nome;
    const preco = this.dataset.preco;
    const imagem = this.dataset.imagem;
    const selectId = this.dataset.select;
    const tamanho = document.querySelector(selectId).value;

    if (!tamanho) {
      alert('Selecione um tamanho antes de adicionar ao carrinho.');
      return;
    }

    try {
      const res = await fetch('/add_to_cart', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          id: id,
          nome: nome,
          preco: preco,
          imagem: imagem,
          tamanho: tamanho
        })
      });

      if (res.ok) {
        const data = await res.json();

        const badge = document.getElementById('cart-count');
        if (badge && data.total_itens !== undefined) {
          badge.textContent = data.total_itens;
          badge.style.display = data.total_itens > 0 ? 'inline-block' : 'none';
        }

        const preview = document.getElementById('cart-preview');
        if (preview && data.preview_html) {
          preview.innerHTML = data.preview_html;
          preview.style.display = 'block';
          setTimeout(() => preview.style.display = 'none', 3000);
        }
      } else {
        alert('Erro ao adicionar ao carrinho.');
      }
    } catch (error) {
      console.error(error);
      alert('Erro ao adicionar ao carrinho.');
    }
  });
});

  // Lógica dos botões de tamanho (P, M, G, GG)
  document.querySelectorAll('.btn-tamanho').forEach(botao => {
    botao.addEventListener('click', () => {
      const grupo = botao.closest('.tamanhos-container');
      const inputHidden = grupo.querySelector('input[type="hidden"]');
      const todos = grupo.querySelectorAll('.btn-tamanho');

      todos.forEach(b => b.classList.remove('ativo'));
      botao.classList.add('ativo');
      inputHidden.value = botao.dataset.valor;
    });
  });
});
