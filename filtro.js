function filtrarPor(categoria) {
  const produtos = document.querySelectorAll('.product-card');
  const botoes = document.querySelectorAll('.filtro-btn');

  // Atualiza classe ativa
  botoes.forEach(btn => btn.classList.remove('ativo'));
  const btnAtivo = Array.from(botoes).find(btn => btn.textContent.toLowerCase().includes(categoria));
  if (btnAtivo) btnAtivo.classList.add('ativo');
  else botoes[0].classList.add('ativo'); // Se não encontrar, ativa "Todos"

  // Mostra ou oculta os produtos
  produtos.forEach(produto => {
    const nome = produto.querySelector('.product-name').textContent.toLowerCase();

    if (categoria === 'todos' || nome.includes(categoria)) {
      produto.style.display = 'block';
    } else {
      produto.style.display = 'none';
    }
  });
}
