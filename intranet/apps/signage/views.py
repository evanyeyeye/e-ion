# -*- coding: utf-8 -*-

import datetime
import logging

from django import http
from django.conf import settings
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.clickjacking import xframe_options_exempt

from .models import Sign
from ..announcements.models import Announcement
from ..eighth.models import EighthBlock
from ..eighth.serializers import EighthBlockDetailSerializer
from ..schedule.views import schedule_context
from ..users.models import User
from ...utils.serialization import safe_json

logger = logging.getLogger(__name__)


def check_show_eighth(now):
    next_block = EighthBlock.objects.get_first_upcoming_block()
    if next_block:
        if next_block.date != now.date():
            return False

    return (8 < now.time().hour < 16)


def check_internal_ip(request):
    remote_addr = (request.META["HTTP_X_FORWARDED_FOR"] if "HTTP_X_FORWARDED_FOR" in request.META else request.META.get("REMOTE_ADDR", ""))
    if not request.user.is_authenticated and remote_addr not in settings.INTERNAL_IPS:
        return render(request, "error/403.html", {"reason": "You are not authorized to view this page."}, status=403)


@xframe_options_exempt
def signage_display(request, display_id=None):
    internal_ip = check_internal_ip(request)
    if internal_ip:
        return internal_ip

    try:
        sign = Sign.objects.get(display=display_id)
        sign_status = sign.status
    except Sign.DoesNotExist:
        sign = None
        sign_status = "auto"

    if "status" in request.GET:
        sign_status = request.GET.get("status")

    suffix = "id={}".format(display_id)
    if "mac" in request.GET:
        suffix += "&mac={}".format(request.GET["mac"])

    now = datetime.datetime.now()
    if sign_status == "eighth":
        # return eighth_signage(request, None, sign.block_increment)
        if sign and sign.eighth_block_increment:
            iframe = "/signage/eighth?no_reload&block_increment={}&".format(sign.eighth_block_increment)
        else:
            iframe = "/signage/eighth?no_reload&"
        if sign and sign.use_frameset:
            return frameset_signage(request, iframe)
        else:
            return iframe_signage(request, iframe)
    elif sign_status == "schedule":
        return schedule_signage(request)
    elif sign_status == "status":
        return status_signage(request)
    elif sign_status == "touch":
        return touch_signage(request, sign)
    elif sign_status == "url" or "url" in request.GET:
        url = request.GET.get('url') or (sign.url if sign else "about:blank")
        use_header = ('use_header' in request.GET) or sign.use_header or True
        if sign and sign.use_frameset:
            return frameset_signage(request, url)
        else:
            return iframe_signage(request, url, use_header=use_header)
    else:
        if check_show_eighth(now):
            if sign and sign.eighth_block_increment:
                iframe = "/signage/eighth?block_increment={}&".format(sign.eighth_block_increment)
            else:
                iframe = "/signage/eighth?no_reload&"
            if sign and sign.use_frameset:
                return frameset_signage(request, iframe)
            else:
                return iframe_signage(request, iframe)
        elif sign_status == "autourl":
            url = request.GET.get('url') or (sign.url if sign else "about:blank")
            if sign and sign.use_frameset:
                return frameset_signage(request, url)
            else:
                return iframe_signage(request, url)
        else:
            return status_signage(request)


@xframe_options_exempt
def touch_signage(request, sign=None, landscape=False):
    internal_ip = check_internal_ip(request)
    if internal_ip:
        return internal_ip

    block_increment = 0
    if sign and sign.eighth_block_increment:
        block_increment = sign.eighth_block_increment

    zoom = request.GET.get("zoom", 3)
    if sign and sign.zoom:
        zoom = sign.zoom

    landscape = request.GET.get("landscape", landscape)
    if sign and sign.landscape:
        landscape = True

    default_page = "clock"
    now = datetime.datetime.now()
    if check_show_eighth(now):
        default_page = "eighth"

    map_location = ""
    if sign and sign.map_location:
        map_location = sign.map_location

    context = schedule_context(request)
    context["senior_graduation"] = settings.SENIOR_GRADUATION
    context["senior_graduation_year"] = settings.SENIOR_GRADUATION_YEAR
    context["signage"] = True
    context["zoom"] = zoom
    context["eighth_url"] = "/signage/eighth?no_reload&touch=1&detail=1&block_increment={}".format(block_increment)
    context["calendar_url"] = "https://postman.tjhsst.edu/"
    try:
        context["map_url"] = "{}{}".format(settings.SIGNAGE_MAP_URL, map_location)
    except AttributeError:
        context["map_url"] = None

    context["default_page"] = default_page
    context["public_announcements"] = Announcement.objects.filter(groups__isnull=True, expiration_date__gt=timezone.now())
    context["landscape"] = landscape
    return render(request, "signage/touch.html", context)


@xframe_options_exempt
def schedule_signage(request):
    internal_ip = check_internal_ip(request)
    if internal_ip:
        return internal_ip

    context = schedule_context(request)
    context["signage"] = True
    context["hide_arrows"] = True
    return render(request, "schedule/embed.html", context)


@xframe_options_exempt
def status_signage(request):
    internal_ip = check_internal_ip(request)
    if internal_ip:
        return internal_ip

    context = schedule_context(request)
    context["signage"] = True
    return render(request, "signage/status.html", context)


@xframe_options_exempt
def iframe_signage(request, url, use_header=True):
    internal_ip = check_internal_ip(request)
    if internal_ip:
        return internal_ip

    context = schedule_context(request)
    context["signage"] = True
    context["url"] = url
    context["use_header"] = use_header
    return render(request, "signage/iframe.html", context)


@xframe_options_exempt
def frameset_signage(request, url):
    internal_ip = check_internal_ip(request)
    if internal_ip:
        return internal_ip

    context = schedule_context(request)
    context["signage"] = True
    url = url + ("&" if "?" in url else "?") + "zoom={}".format(request.GET.get("framezoom", 1))
    context["url"] = url
    return render(request, "signage/frameset.html", context)


@xframe_options_exempt
def frameset_signage_header(request):
    internal_ip = check_internal_ip(request)
    if internal_ip:
        return internal_ip
    return render(request, "signage/frameset-header.html", {})


@xframe_options_exempt
def eighth_signage(request, block_id=None, block_increment=0):
    internal_ip = check_internal_ip(request)
    if internal_ip:
        return internal_ip

    if block_id is None:
        next_block = EighthBlock.objects.get_first_upcoming_block()
        if next_block is not None:
            block_id = next_block.id
        else:
            last_block = EighthBlock.objects.order_by("date").last()
            if last_block is not None:
                block_id = last_block.id

    if "block_increment" in request.GET:
        block_increment = request.GET.get("block_increment", 0)

    try:
        block_increment = int(block_increment)
    except ValueError:
        block_increment = 0

    block = None
    if block_increment > 0:
        next_blocks = next_block.next_blocks()
        if next_blocks.count() >= block_increment:
            block = next_blocks[block_increment - 1]

    if not block:
        try:
            block = (EighthBlock.objects.prefetch_related("eighthscheduledactivity_set").get(id=block_id))
        except EighthBlock.DoesNotExist:
            if EighthBlock.objects.count() == 0:
                # No blocks have been added yet
                return render(request, "eighth/display.html", {"no_blocks": True})
            else:
                # The provided block_id is invalid
                raise http.Http404

    user = User.get_signage_user()

    serializer_context = {"request": request, "user": user}
    block_info = EighthBlockDetailSerializer(block, context=serializer_context).data
    try:
        reload_mins = float(request.GET.get("reload_mins") or 5)
    except Exception:
        reload_mins = 5

    touch_signage = ("touch" in request.GET)

    next_block = list(block.next_blocks(1))
    if next_block:
        next_block = next_block[0]
        if next_block.date != block.date:
            next_block = None

    prev_block = list(block.previous_blocks(1))
    if prev_block:
        prev_block = prev_block[0]
        if prev_block.date != block.date:
            prev_block = None

    context = {
        "user": user,
        "real_user": request.user,
        "block_info": block_info,
        "activities_list": safe_json(block_info["activities"]),
        "active_block": block,
        "active_block_current_signup": None,
        "no_title": ("no_title" in request.GET),
        "no_detail": not ("detail" in request.GET),
        "no_rooms": ("no_rooms" in request.GET),
        "use_scroll": False if touch_signage else ("no_scroll" not in request.GET),
        "do_reload": ("no_reload" not in request.GET),
        "preload_background": True,
        "reload_mins": reload_mins,
        "no_user_display": True,
        "no_fav": True,
        "touch_signage": touch_signage,
        "next_block": next_block,
        "prev_block": prev_block
    }

    return render(request, "eighth/display.html", context)
