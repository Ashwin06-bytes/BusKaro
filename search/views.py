from django.shortcuts import render
from django.http import JsonResponse
from .utils import fuzzy_stop_search


def search_view(request):
    origin = request.GET.get('origin', '')
    destination = request.GET.get('destination', '')
    date = request.GET.get('date', '')
    context = {
        'origin': origin,
        'destination': destination,
        'date': date
    }
    return render(request, 'search/search_results.html', context)


def stop_search_api(request):
    """
    JSON API for stop autocomplete.
    GET /search/stops/?q=gandhi
    Returns matching stops with both English and Tamil names.
    """
    query = request.GET.get('q', '')
    stops = fuzzy_stop_search(query)[:15]  # Limit to 15 results

    results = [
        {
            'id': stop.id,
            'name': stop.name,
            'name_tamil': stop.name_tamil,
            'route_id': stop.route_id,
        }
        for stop in stops
    ]

    return JsonResponse({'results': results})

def city_search_api(request):
    """
    JSON API for major city autocomplete (for Advance Booking).
    """
    query = request.GET.get('q', '').lower()
    cities = [
        "Chennai", "Coimbatore", "Madurai", "Trichy", "Salem", 
        "Tirunelveli", "Erode", "Vellore", "Thoothukudi", "Dindigul", 
        "Thanjavur", "Ranipet", "Sivakasi", "Karur", "Ooty", 
        "Kanyakumari", "Bangalore", "Kochi", "Trivandrum", "Hyderabad",
        "Pondicherry", "Mysore", "Mumbai", "Delhi"
    ]
    
    if not query:
        matches = cities[:15]
    else:
        matches = [c for c in cities if query in c.lower()][:15]
        
    results = [{'name': c, 'name_tamil': ''} for c in matches]
    return JsonResponse({'results': results})
