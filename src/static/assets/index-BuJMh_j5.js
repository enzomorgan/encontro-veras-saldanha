// Função auxiliar para exibir mensagens de erro
function showError(elementId, message) {
  const el = document.getElementById(elementId);
  if (el) {
    el.textContent = message;
    el.style.display = message ? 'block' : 'none';
  }
}

// API hospedada na Render
const API_BASE_URL = 'https://encontro-veras-saldanha-backend.onrender.com';

// Cadastro
async function handleCadastro(e) {
  e.preventDefault();
  showError('cadastro-error', '');

  const payload = {
    nomeCompleto: document.getElementById('cadastro-nome').value.trim(),
    email: document.getElementById('cadastro-email').value.trim(),
    password: document.getElementById('cadastro-senha').value,
    confirmPassword: document.getElementById('cadastro-confirmar-senha').value,
    descendencia: document.getElementById('cadastro-descendencia').value.trim().toLowerCase(),
    idade: parseInt(document.getElementById('cadastro-idade').value, 10),
    cidadeResidencia: document.getElementById('cadastro-cidade').value.trim()
  };

  try {
    const res = await fetch(`${API_BASE_URL}/api/auth/cadastro`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (!res.ok) {
      showError('cadastro-error', data.error || 'Erro ao cadastrar');
      return;
    }

    showError('cadastro-error', '✅ Cadastro realizado com sucesso!');
    document.getElementById('form-cadastro').reset();
  } catch (err) {
    console.error(err);
    showError('cadastro-error', '❌ Falha de conexão com o servidor');
  }
}

// Login
async function handleLogin(e) {
  e.preventDefault();
  showError('login-error', '');

  const payload = {
    email: document.getElementById('login-email').value.trim(),
    password: document.getElementById('login-senha').value
  };

  try {
    const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (!res.ok) {
      showError('login-error', data.error || 'Erro no login');
      return;
    }

    showError('login-error', '✅ Login realizado com sucesso!');
    localStorage.setItem('token', data.token);
    setTimeout(() => {
      window.location.href = '/';
    }, 1000);
  } catch (err) {
    console.error(err);
    showError('login-error', '❌ Falha de conexão com o servidor');
  }
}

// Eventos
const formCadastro = document.getElementById('form-cadastro');
if (formCadastro) {
  formCadastro.addEventListener('submit', handleCadastro);
}

const formLogin = document.getElementById('form-login');
if (formLogin) {
  formLogin.addEventListener('submit', handleLogin);
}
