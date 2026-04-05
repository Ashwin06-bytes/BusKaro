from django.shortcuts import render

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
