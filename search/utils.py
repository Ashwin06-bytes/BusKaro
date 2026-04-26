import unicodedata
from django.db.models import Q
from routes.models import Stop


def normalize_query(query):
    """
    Strip Latin diacritics using NFKD decomposition so that
    transliterated Tamil input like 'Gandhipuram' or 'Gāndhipuram'
    matches the stored English stop name.
    Characters that are combining marks (category 'Mn') are removed.
    """
    decomposed = unicodedata.normalize('NFKD', query)
    stripped = ''.join(
        ch for ch in decomposed
        if unicodedata.category(ch) != 'Mn'
    )
    return stripped


def fuzzy_stop_search(query):
    """
    Search Stop objects by English name OR Tamil name.
    The query is matched as-is against both fields (icontains),
    and also matched after stripping Latin diacritics from the query
    (so transliterated/accented input still finds the right stop).

    Returns a queryset of matching Stop objects ordered by name.
    """
    if not query or not query.strip():
        return Stop.objects.none()

    query = query.strip()
    normalized = normalize_query(query)

    # Build filter: original query OR normalized query, against both name fields
    filters = (
        Q(name__icontains=query) |
        Q(name_tamil__icontains=query)
    )

    # If normalization changed the query, also search with the normalized form
    if normalized != query:
        filters |= (
            Q(name__icontains=normalized) |
            Q(name_tamil__icontains=normalized)
        )

    return Stop.objects.filter(filters).order_by('name').distinct()
