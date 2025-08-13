// Configuração inicial
const APP_CONFIG = {
  debug: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1',
  apiBaseUrl: 'https://encontro-veras-saldanha-backend.onrender.com'
};

// Sistema de loading
function showLoading(show = true) {
  const loader = document.getElementById('loading-screen');
  if (loader) loader.style.display = show ? 'flex' : 'none';
}

// Função auxiliar melhorada
function showError(elementId, message, isSuccess = false) {
  const el = document.getElementById(elementId);
  if (el) {
    el.innerHTML = message ? `<span class="${isSuccess ? 'success' : 'error'}">${message}</span>` : '';
    el.style.display = message ? 'block' : 'none';
  }
}

// Validação de formulário aprimorada
function validateForm(payload, isLogin = false) {
  const errors = [];
  
  if (!isLogin) {
    if (!payload.nomeCompleto?.trim()) errors.push('Nome completo é obrigatório');
    if (!payload.email?.trim()) errors.push('Email é obrigatório');
    if (!payload.password) errors.push('Senha é obrigatória');
    if (!payload.confirmPassword) errors.push('Confirmação de senha é obrigatória');
    if (payload.password !== payload.confirmPassword) errors.push('As senhas não coincidem');
    if (payload.password?.length < 6) errors.push('A senha deve ter pelo menos 6 caracteres');
  } else {
    if (!payload.email?.trim()) errors.push('Email é obrigatório');
    if (!payload.password) errors.push('Senha é obrigatória');
  }
  
  return errors.length ? errors.join('<br>') : null;
}

// Função de requisição genérica
async function makeRequest(endpoint, method, body, authToken = null) {
  const headers = {
    'Content-Type': 'application/json',
    ...(authToken && { 'Authorization': `Bearer ${authToken}` })
  };

  try {
    const response = await fetch(`${APP_CONFIG.apiBaseUrl}${endpoint}`, {
      method,
      headers,
      body: JSON.stringify(body)
    });

    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.error || 'Erro no servidor');
    }

    return data;
  } catch (error) {
    console.error(`Erro na requisição ${endpoint}:`, error);
    throw error;
  }
}

// Cadastro otimizado
async function handleCadastro(e) {
  e.preventDefault();
  showLoading(true);
  showError('cadastro-error', '');

  const payload = {
    nomeCompleto: document.getElementById('cadastro-nome')?.value.trim(),
    email: document.getElementById('cadastro-email')?.value.trim(),
    password: document.getElementById('cadastro-senha')?.value,
    confirmPassword: document.getElementById('cadastro-confirmar-senha')?.value,
    descendencia: document.getElementById('cadastro-descendencia')?.value.trim().toLowerCase(),
    idade: parseInt(document.getElementById('cadastro-idade')?.value, 10),
    cidadeResidencia: document.getElementById('cadastro-cidade')?.value.trim()
  };

  try {
    const validationError = validateForm(payload);
    if (validationError) {
      showError('cadastro-error', `❌ ${validationError}`);
      return;
    }

    const data = await makeRequest('/api/auth/cadastro', 'POST', payload);
    
    showError('cadastro-error', '✅ Cadastro realizado com sucesso!', true);
    document.getElementById('form-cadastro')?.reset();
    
    setTimeout(() => {
      window.location.hash = '#login';
    }, 2000);
    
  } catch (error) {
    showError('cadastro-error', `❌ ${error.message || 'Falha no cadastro'}`);
  } finally {
    showLoading(false);
  }
}

// Login otimizado
async function handleLogin(e) {
  e.preventDefault();
  showLoading(true);
  showError('login-error', '');

  const payload = {
    email: document.getElementById('login-email')?.value.trim(),
    password: document.getElementById('login-senha')?.value
  };

  try {
    const validationError = validateForm(payload, true);
    if (validationError) {
      showError('login-error', `❌ ${validationError}`);
      return;
    }

    const data = await makeRequest('/api/auth/login', 'POST', payload);
    
    showError('login-error', '✅ Login realizado com sucesso!', true);
    localStorage.setItem('token', data.token);
    
    setTimeout(() => {
      window.location.href = '/';
    }, 1000);
    
  } catch (error) {
    showError('login-error', `❌ ${error.message || 'Falha no login'}`);
  } finally {
    showLoading(false);
  }
}

// Verificação de autenticação
function checkAuth() {
  const token = localStorage.getItem('token');
  const isAuthPage = window.location.pathname.includes('auth');
  
  if (token && isAuthPage) {
    window.location.href = '/';
  }
}

// Inicialização robusta
function initApp() {
  try {
    // Verifica autenticação
    checkAuth();
    
    // Configura formulários
    const formCadastro = document.getElementById('form-cadastro');
    const formLogin = document.getElementById('form-login');
    
    if (formCadastro) formCadastro.addEventListener('submit', handleCadastro);
    if (formLogin) formLogin.addEventListener('submit', handleLogin);
    
    // Esconde o loading
    showLoading(false);
    
    if (APP_CONFIG.debug) {
      console.log('Aplicação inicializada com sucesso');
    }
  } catch (error) {
    console.error('Falha na inicialização:', error);
    showError('global-error', '❌ Falha ao carregar a aplicação');
  }
}

// Inicia quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', initApp);
