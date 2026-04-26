import concurrent.futures
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.core.cache import cache
from django.contrib.auth.decorators import login_required
from aggregator.adapters.internal import InternalAdapter
from aggregator.adapters.tnstc import TNSTCAdapter
from aggregator.adapters.redbus import RedbusAdapter
from aggregator.adapters.abhibus import AbhibusAdapter
from tatkal.models import TatkalQuota, TatkalConfig
from aggregator.models import SearchLog
from django.utils import timezone

ADAPTER_CLASSES = {
    "internal": InternalAdapter,
    "tnstc": TNSTCAdapter,
    "redbus": RedbusAdapter,
    "abhibus": AbhibusAdapter,
}

def aggregated_search(request):
    origin = request.GET.get("origin", "")
    destination = request.GET.get("destination", "")
    date = request.GET.get("date", "")

    if not all([origin, destination, date]):
        return JsonResponse({"error": "Missing required parameters."}, status=400)

    cache_key = f"search:{origin}:{destination}:{date}"
    cached_results = cache.get(cache_key)

    if cached_results:
        return JsonResponse({
            "results": cached_results["results"],
            "total": len(cached_results["results"]),
            "cached": True,
            "sources_queried": cached_results["sources_queried"]
        })

    adapters_config = getattr(settings, 'AGGREGATOR_ADAPTERS', {})
    futures = []
    results = []
    sources_queried = []

    def fetch_from_adapter(source_name, adapter_cls, is_dummy):
        adapter_instance = adapter_cls(is_dummy=is_dummy)
        try:
            return source_name, adapter_instance.fetch(origin, destination, date)
        except Exception as e:
            # Optionally log exception
            return source_name, []

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        for source_name, config in adapters_config.items():
            if config.get("enabled", False):
                adapter_cls = ADAPTER_CLASSES.get(source_name)
                if adapter_cls:
                    sources_queried.append(source_name)
                    is_dummy = config.get("dummy", True)
                    futures.append(executor.submit(fetch_from_adapter, source_name, adapter_cls, is_dummy))

        for future in concurrent.futures.as_completed(futures):
            source_name, fetched_results = future.result()
            results.extend(fetched_results)

    # Process tatkal pricing
    for result in results:
        source = result.get('source')
        source_trip_id = result.get('source_trip_id')
        
        # Check if tatkal quota is open or scheduled to open
        now = timezone.now()
        quota = TatkalQuota.objects.filter(source=source, source_trip_id=source_trip_id).first()
        
        is_tatkal_available = False
        if quota:
            if quota.is_open:
                is_tatkal_available = True
            elif quota.auto_open_time and now >= quota.auto_open_time:
                # If timer passed, treat as open and update record if needed
                is_tatkal_available = True
                quota.is_open = True
                quota.opened_at = now
                quota.save()

        if is_tatkal_available:
            result['tatkal_open'] = True
            
            # Determine surcharge percent
            # For internal, check if there's related operator TatkalConfig
            surcharge_percent = 25.0 # default
            if source == 'internal':
                try:
                    from routes.models import Schedule
                    sched = Schedule.objects.get(id=int(source_trip_id))
                    if hasattr(sched.bus.route, 'operator_type'):
                        pass
                except Exception:
                    pass
            
            base_fare = float(result.get('fare', 0))
            result['tatkal_fare'] = round(base_fare * (1 + float(surcharge_percent) / 100), 2)
        elif result.get('is_dummy'):
            # Simulate tatkal for 1/3rd of dummy buses so the frontend filter works
            try:
                trip_num = int(str(source_trip_id).split('-')[-1])
                if trip_num % 3 == 0:
                    result['tatkal_open'] = True
                    result['tatkal_fare'] = round(float(result.get('fare', 0)) * 1.25, 2)
                else:
                    result['tatkal_open'] = False
                    result['tatkal_fare'] = None
            except ValueError:
                result['tatkal_open'] = False
                result['tatkal_fare'] = None
        else:
            result['tatkal_open'] = False
            result['tatkal_fare'] = None

    # Sort unified results by fare ascending
    results.sort(key=lambda x: x.get('fare', float('inf')))

    SearchLog.objects.create(
        origin=origin,
        destination=destination,
        travel_date=date,
        results_count=len(results),
        sources_used=sources_queried
    )

    cache_data = {
        "results": results,
        "sources_queried": sources_queried
    }
    timeout = getattr(settings, 'AGGREGATOR_CACHE_TIMEOUT', 300)
    cache.set(cache_key, cache_data, timeout)

    return JsonResponse({
        "results": results,
        "total": len(results),
        "cached": False,
        "sources_queried": sources_queried
    })

@login_required(login_url='/passenger/login/')
def dummy_booking(request, source_name, trip_id):
    fare = request.GET.get('fare', '0')
    origin = request.GET.get('origin', '')
    destination = request.GET.get('destination', '')
    date = request.GET.get('date', '')
    
    if source_name.lower() != 'tnstc':
        return render(request, 'aggregator/external_redirect.html', {
            'provider': source_name,
            'trip_id': trip_id,
            'origin': origin,
            'destination': destination,
            'date': date
        })

    return render(request, 'aggregator/dummy_booking.html', {
        'source': source_name,
        'trip_id': trip_id,
        'fare': fare,
        'origin': origin,
        'destination': destination,
        'date': date
    })
