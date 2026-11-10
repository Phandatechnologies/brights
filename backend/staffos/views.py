"""GET /api/internal/staff-os/metrics/?start=YYYY-MM-DD&end=YYYY-MM-DD

Answers only Phanda Staff OS: the request must carry a valid signature made with STAFF_OS_METRICS_SECRET, less than
5 minutes old. Without that setting the address doesn't exist (404). Read-only, totals only.
"""

import time
from datetime import date

from django.conf import settings
from django.http import Http404, JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET

from . import signing
from .totals import collect

MAX_DAYS = 93


def _bad(msg, code=400):
    resp = JsonResponse({"detail": msg}, status=code)
    resp["Cache-Control"] = "no-store"
    return resp


@require_GET
def metrics(request):
    secret = getattr(settings, "STAFF_OS_METRICS_SECRET", "")
    if not secret:
        raise Http404()
    ok = signing.verify(secret, request.headers.get("X-Staff-OS-Timestamp", ""),
                        request.headers.get("X-Staff-OS-Signature", ""), "GET", request.get_full_path(),
                        int(time.time()))
    if not ok:
        return _bad("Signature missing, wrong or too old.", 403)
    try:
        start = date.fromisoformat(request.GET.get("start", ""))
        end = date.fromisoformat(request.GET.get("end", ""))
    except ValueError:
        return _bad("start and end must be dates like 2026-10-19.")
    if end < start or (end - start).days >= MAX_DAYS or end > timezone.localdate():
        return _bad(f"Ask for up to {MAX_DAYS} days that have started, start before end.")
    resp = JsonResponse({"app": "brights", "schema": 1, "start": start.isoformat(), "end": end.isoformat(),
                         "generated_at": timezone.now().isoformat(), "metrics": collect(start, end)})
    resp["Cache-Control"] = "no-store"
    return resp
