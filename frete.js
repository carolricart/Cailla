function calcularFrete(subtotal) {
  const cep = document.getElementById('cep').value;
  const freteInfo = document.getElementById('freteInfo');
  const freteInput = document.getElementById('frete_valor');
  const valorFreteSpan = document.getElementById('valorFrete');
  const valorTotalFinalSpan = document.getElementById('valorTotalFinal');

  if (!cep) {
    freteInfo.textContent = "Digite um CEP válido.";
    return;
  }

  fetch("/calcular_frete", {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded"
    },
    body: new URLSearchParams({ cep })
  })
    .then(response => response.json())
    .then(data => {
      const frete = data.frete;
      const subtotal = parseFloat(document.getElementById("subtotal").value);
      const totalFinal = subtotal + frete;

      freteInfo.textContent = `Frete: R$ ${frete.toFixed(2).replace('.', ',')} - Prazo: ${data.prazo}`;
      freteInput.value = frete;
      valorFreteSpan.textContent = `R$ ${frete.toFixed(2).replace('.', ',')}`;
      valorTotalFinalSpan.textContent = `R$ ${totalFinal.toFixed(2).replace('.', ',')}`;
    })
    .catch(error => {
      console.error("Erro ao calcular frete:", error);
      freteInfo.textContent = "Erro ao calcular o frete.";
    });
}

// CEP -> Preenche endereço + chama calcularFrete automaticamente
document.addEventListener("DOMContentLoaded", function () {
  const cepInput = document.getElementById("cep");

  if (cepInput) {
    cepInput.addEventListener("blur", function () {
      const cep = cepInput.value.replace(/\D/g, "");

      if (cep.length === 8) {
        fetch(`https://viacep.com.br/ws/${cep}/json/`)
          .then((response) => response.json())
          .then((data) => {
            if (!data.erro) {
              document.getElementById("endereco").value = data.logradouro || "";
              document.getElementById("bairro").value = data.bairro || "";
              document.getElementById("cidade").value = data.localidade || "";
              document.getElementById("estado").value = data.uf || "";

              const subtotal = parseFloat(document.getElementById("subtotal").value);
              calcularFrete(subtotal); // Chama automaticamente
            } else {
              alert("CEP não encontrado.");
            }
          })
          .catch((error) => {
            console.error("Erro ao buscar CEP:", error);
          });
      }
    });
  }
});
