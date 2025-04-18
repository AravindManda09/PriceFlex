from datetime import datetime, timedelta

def get_date_range_data(items, date_attribute, days=30):
    """
    Generate daily aggregated data for date range charts
    
    Args:
        items: List of objects with date attributes
        date_attribute: The attribute name for the date field
        days: Number of days to include
    
    Returns:
        List of date and count/value dictionaries
    """
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = today - timedelta(days=days-1)
    
    # Initialize results with all dates in range
    date_range = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days)]
    results = {date: {'date': date, 'count': 0, 'revenue': 0} for date in date_range}
    
    # Aggregate data by date
    for item in items:
        # Get the date attribute
        item_date = getattr(item, date_attribute)
        date_str = item_date.strftime('%Y-%m-%d')
        
        # Skip items outside our date range
        if date_str not in results:
            continue
            
        # Increment count
        results[date_str]['count'] += 1
        
        # Calculate revenue if available
        if hasattr(item, 'revenue'):
            results[date_str]['revenue'] += item.revenue
        elif hasattr(item, 'price') and hasattr(item, 'quantity'):
            results[date_str]['revenue'] += item.price * item.quantity
    
    # Convert to list
    return [data for date, data in results.items()]
