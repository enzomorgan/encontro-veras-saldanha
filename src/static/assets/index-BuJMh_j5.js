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

// Validação de formulário
function validateForm(payload, isLogin = false) {
  if (!isLogin) {
    if (!payload.nomeCompleto || !payload.email || !payload.password || !payload.confirmPassword) {
      return 'Preencha todos os campos obrigatórios';
    }
    if (payload.password !== payload.confirmPassword) {
      return 'As senhas não coincidem';
    }
    if (payload.password.length < 6) {
      return 'A senha deve ter pelo menos 6 caracteres';
    }
  } else {
    if (!payload.email || !payload.password) {
      return 'Preencha todos os campos obrigatórios';
    }
  }
  return null;
}

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

  // Validação antes de enviar
  const validationError = validateForm(payload);
  if (validationError) {
    showError('cadastro-error', `❌ ${validationError}`);
    return;
  }

  try {
    const res = await fetch(`${API_BASE_URL}/api/auth/cadastro`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    
    if (!res.ok) {
      const errorMsg = data.error || 
                      (res.status === 400 ? 'Dados inválidos' : 
                       res.status === 401 ? 'Não autorizado' : 
                       'Erro no servidor');
      showError('cadastro-error', `❌ ${errorMsg}`);
      return;
    }

    showError('cadastro-error', '✅ Cadastro realizado com sucesso!');
    document.getElementById('form-cadastro').reset();
    
    // Redireciona para login após 2 segundos
    setTimeout(() => {
      window.location.href = '#login';
    }, 2000);
    
  } catch (err) {
    console.error('Erro no cadastro:', err);
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

  // Validação antes de enviar
  const validationError = validateForm(payload, true);
  if (validationError) {
    showError('login-error', `❌ ${validationError}`);
    return;
  }

  try {
    const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    
    if (!res.ok) {
      const errorMsg = data.error || 
                      (res.status === 400 ? 'Credenciais inválidas' : 
                       res.status === 401 ? 'Não autorizado' : 
                       'Erro no servidor');
      showError('login-error', `❌ ${errorMsg}`);
      return;
    }

    showError('login-error', '✅ Login realizado com sucesso!');
    localStorage.setItem('token', data.token);
    
    // Redireciona após 1 segundo
    setTimeout(() => {
      window.location.href = '/';
    }, 1000);
    
  } catch (err) {
    console.error('Erro no login:', err);
    showError('login-error', '❌ Falha de conexão com o servidor');
  }
}

// Inicialização quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', function() {
  // Verifica se está na página de autenticação
  if (document.getElementById('form-cadastro') || document.getElementById('form-login')) {
    const formCadastro = document.getElementById('form-cadastro');
    const formLogin = document.getElementById('form-login');
    
    if (formCadastro) {
      formCadastro.addEventListener('submit', handleCadastro);
    }
    
    if (formLogin) {
      formLogin.addEventListener('submit', handleLogin);
    }
  }
  
  // Verifica se há token salvo para redirecionar
  if (localStorage.getItem('token') && window.location.pathname.includes('auth')) {
    window.location.href = '/';
  }
});
