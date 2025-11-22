from django import template

register = template.Library()

@register.filter
def currency(value, currency_code='INR'):
    """Format a number with the appropriate currency symbol"""
    if value is None:
        return ''
    
    # Currency symbols mapping
    currency_symbols = {
        'INR': '₹',
        'USD': '$',
        'EUR': '€',
        'GBP': '£',
    }
    
    symbol = currency_symbols.get(currency_code, '₹')
    
    try:
        # Convert to float and format
        num_value = float(value)
        return f"{symbol}{num_value:,.2f}"
    except (ValueError, TypeError):
        return f"{symbol}{value}"

@register.simple_tag
def get_currency_symbol(currency_code='INR'):
    """Get the currency symbol for a given currency code"""
    currency_symbols = {
        'INR': '₹',
        'USD': '$',
        'EUR': '€',
        'GBP': '£',
    }
    return currency_symbols.get(currency_code, '₹')

