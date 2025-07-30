"""
Utilitário para cálculo de preços das camisas baseado na idade
"""

def calcular_preco_camisa(idade):
    """
    Calcula o preço da camisa baseado na idade do usuário
    
    Args:
        idade (int): Idade do usuário
        
    Returns:
        float: Preço da camisa
    """
    if idade >= 13:
        return 290.00  # R$ 290,00 para 13 anos ou mais
    elif idade >= 6:
        return 145.00  # R$ 145,00 para 6 a 12 anos
    else:
        # Crianças menores de 6 anos não precisam de camisa
        return 0.00

def get_faixa_etaria(idade):
    """
    Retorna a faixa etária baseada na idade
    
    Args:
        idade (int): Idade do usuário
        
    Returns:
        str: Descrição da faixa etária
    """
    if idade >= 13:
        return "13 anos ou mais"
    elif idade >= 6:
        return "6 a 12 anos"
    else:
        return "Menor de 6 anos"

def get_info_preco(idade):
    """
    Retorna informações completas sobre o preço para uma idade
    
    Args:
        idade (int): Idade do usuário
        
    Returns:
        dict: Informações sobre preço e faixa etária
    """
    preco = calcular_preco_camisa(idade)
    faixa = get_faixa_etaria(idade)
    
    return {
        'idade': idade,
        'faixa_etaria': faixa,
        'preco': preco,
        'preco_formatado': f'R$ {preco:.2f}'.replace('.', ','),
        'gratuito': preco == 0.00
    }

