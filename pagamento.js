document.addEventListener("DOMContentLoaded", function () {
  const inputCartao = document.querySelector('input[name="numero_cartao"]');

  if (inputCartao) {
    const bandeiraDiv = document.createElement('div');
    bandeiraDiv.className = 'bandeira-logo';
    inputCartao.parentElement.classList.add('campo-cartao');
    inputCartao.parentElement.appendChild(bandeiraDiv);

    inputCartao.addEventListener("input", function () {
      const numero = inputCartao.value.replace(/\D/g, '');
      let bandeira = "";

      if (/^4/.test(numero)) {
        bandeira = "visa";
      } else if (/^5[1-5]/.test(numero)) {
        bandeira = "mastercard";
      } else if (/^3[47]/.test(numero)) {
        bandeira = "amex";
      } else if (/^6/.test(numero)) {
        bandeira = "elo";
      } else {
        bandeira = "";
      }

      if (bandeira) {
        bandeiraDiv.style.backgroundImage = `url('/static/assets/bandeiras/${bandeira}.png')`;
        bandeiraDiv.style.display = "block";
      } else {
        bandeiraDiv.style.backgroundImage = "";
        bandeiraDiv.style.display = "none";
      }
    });
  }

  // Alternar forma de pagamento
  function alternarPagamento() {
    const metodo = document.getElementById('metodo_pagamento').value;
    const cartaoForm = document.getElementById('cartao-form');
    const pixInfo = document.getElementById('pix-info');
    const cartaoFields = cartaoForm.querySelectorAll('input, select');

    if (metodo === 'cartao') {
      cartaoForm.style.display = 'block';
      pixInfo.style.display = 'none';
      cartaoFields.forEach(input => input.disabled = false);
    } else {
      cartaoForm.style.display = 'none';
      pixInfo.style.display = 'block';
      cartaoFields.forEach(input => input.disabled = true);
    }
  }

  // Inicializa e escuta mudanças
  alternarPagamento();
  document.getElementById('metodo_pagamento').addEventListener('change', alternarPagamento);

  // Loader no botão
  const form = document.querySelector('form.pagamento-form');
  form.addEventListener('submit', function () {
    const btn = document.getElementById('btnFinalizar');
    const texto = document.getElementById('btnTexto');
    const loader = document.getElementById('btnLoader');

    btn.disabled = true;
    texto.textContent = 'Processando...';
    loader.style.display = 'inline-block';
  });
});
