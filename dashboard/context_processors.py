def currency_context(request):
    """Context processor to add currency information to all templates"""
    if not hasattr(request, 'session'):
        currency = 'INR'
    else:
        currency = request.session.get('currency', 'INR')
    
    # Currency symbols mapping
    currency_symbols = {
        'INR': '₹',
        'USD': '$',
        'EUR': '€',
        'GBP': '£',
    }
    
    symbol = currency_symbols.get(currency, '₹')
    
    return {
        'user_currency': currency,
        'currency_symbol': symbol,
    }

