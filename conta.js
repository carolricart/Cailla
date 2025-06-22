function editar(campo) {
  document.getElementById(campo).style.display = 'none';
  document.getElementById('input-' + campo).style.display = 'inline';
  document.getElementById('salvar').style.display = 'block';
}

function salvarEdicao() {
  // Copia valores dos inputs visíveis para os campos do form oculto
  document.getElementById('form-email').value = document.getElementById('input-email').value;
  document.getElementById('form-senha').value = document.getElementById('input-senha').value;
  document.getElementById('form-telefone').value = document.getElementById('input-telefone').value;
  document.getElementById('form-endereco').value = document.getElementById('input-endereco').value;

  document.getElementById('form-edicao').submit();
}
