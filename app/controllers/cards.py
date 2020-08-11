# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, request, Response, abort
import json, requests, base64, os
from xml.dom import minidom
from flask_login import current_user
from app.models.user import User
from colorthief import ColorThief
import sys

if sys.version_info < (3, 0):
    from urllib2 import urlopen
else:
    from urllib.request import urlopen

import io
blueprint = Blueprint('cards', __name__, url_prefix="/cards")

def uri_process(e):
    t = e.find("track")
    n = e.find("artist")
    r = e.find("album")
    o = e.find("playlist")
    i = e.find("user")
    a = e.find("genre")
    s = e.find("show")
    u = e.find("episode")
    l = "https://api.spotify.com/v1"
    c = {}
    if t >= 0:
        f = e[t + 6:len(e)]
        c["apiLink"] = l + "/tracks/" + f
        c["uriLink"] = "spotify:track:" + f
        c["type"] = "track"
    elif n >= 0:
        p = e[n + 7:len(e)]
        c["apiLink"] = l + "/artists/" + p
        c["uriLink"] = "spotify:artist:" + p
        c["type"] = "artist"
    elif r >= 0:
        d = e[r + 6:len(e)]
        c["apiLink"] = l + "/albums/" + d
        c["uriLink"] = "spotify:album:" + d
        c["type"] = "album"
    elif o >= 0 and i >= 0:
        h = e[i + 5:o - 1]
        v = e[o + 9:len(e)]
        c["apiLink"] = l + "/users/" + h + "/playlists/" + v
        c["uriLink"] = "spotify:user:" + h + ":playlist:" + v
        c["type"] = "playlist"
    elif o >= 0:
        v = e[o + 9:len(e)]
        c["apiLink"] = l + "/playlists/" + v
        c["uriLink"] = "spotify:playlist:" + v
        c["type"] = "playlist"
    elif -1 == o and i >= 0:
        m = e.split(":")
        h = m.pop()
        c["apiLink"] = l + "/users/" + h
        c["uriLink"] = "spotify:user:" + h
        c["type"] = "user"
    elif a >= 0:
        g = e[a + 6:len(e)]
        c["apiLink"] = l + "/genre/" + g
        c["uriLink"] = "spotify:genre:" + g
        c["type"] = "genre"
    elif s >= 0:
        y = e[s + 5:len(e)]
        c["apiLink"] = l + "/show/" + y
        c["uriLink"] = "spotify:show:" + y
        c["type"] = "show"
    elif u >= 0:
        b = e[u + 8:len(e)]
        c["apiLink"] = l + "/episode/" + b
        c["uriLink"] = "spotify:episode:" + b
        c["type"] = "episode"
    else:
        c["apiLink"] = e
        c["uriLink"] = e
        c["type"] = "none"
    return c

@blueprint.route('/<spotify_uri>/<layout_name>/')
def template1(layout_name, spotify_uri=None):
    default_settings = {
        "title": "Card Title",
        "subtitle": "Card Subtitle",
        "subtitle2": "",
        "border_color": "#main",
        "container_color": "#secondary",
        "text_color": "#main",
        "album_image": "",
        "code_background_color": "#main",
        "code_color": "#secondary",
        "inner_border_color": "#main",
        "round_corners": True,
        "inner_rectangles": "",
        "title_font_size": "10.5833",
        "title_chunk_size": 17
    }

    if layout_name == "template2.svg":
        default_settings["container_color"] = "#main"
        default_settings["text_color"] = "#secondary"
        default_settings["code_background_color"] = "#main"
        default_settings["code_color"] = "#secondary"
        default_settings["title_chunk_size"] = 24

    if request.args.get("settings") is not None:
        settings = json.loads(request.args.get("settings"))
        for key, value in settings.iteritems():
            if key in default_settings:
                default_settings[key] = value

    if spotify_uri is not None:
        raw_code_url = f"https://scannables.scdn.co/uri/plain/svg/000000/white/640/{spotify_uri}/"
        r = requests.get(raw_code_url)

        doc = minidom.parseString(r.text)
        rects = doc.getElementsByTagName("rect")
        rects.pop(0)
        for rect in rects:
            default_settings["inner_rectangles"] += (rect.toxml() + "\n")

        info = uri_process(spotify_uri)

        if current_user.is_authenticated:
            access_token = current_user.auth_token
        else:
            access_token = User.get_anonymous_access_token()

        api_info = requests.get(info["apiLink"], headers={"Authorization": f"Bearer {access_token}"}).json()
        
        if "name" in api_info:
            default_settings["title"] = api_info["name"]
        
        if "images" in api_info:
            color_image = api_info["images"][len(api_info["images"]) - 1]["url"]
            default_settings["album_image"] = api_info["images"][0]["url"]
        elif "album" in api_info:
            color_image = api_info["album"]["images"][len(api_info["album"]["images"]) - 1]["url"]
            default_settings["album_image"] = api_info["album"]["images"][0]["url"]

        fd = urlopen(color_image)
        f = io.BytesIO(fd.read())
        color_thief = ColorThief(f)
        main_color = color_thief.get_color(quality=1)

        color_palette = color_thief.get_palette(color_count=5)
        color_totals = [sum(color) for color in color_palette]

        if sum(main_color) > 600:
            main_color = color_palette[color_totals.index(min(color_totals))]

        for key, val in default_settings.items():
            if val == "#main":
                default_settings[key] = '%02x%02x%02x' % main_color
            if val == "#secondary":
                default_settings[key] = '%02x%02x%02x' % (255,255,255)

        if info["type"] == "track":
            default_settings["subtitle"] = api_info["album"]["name"] + " - " + ", ".join([a["name"] for a in api_info["album"]["artists"]])
            if api_info["album"]["name"] == api_info["name"]:
                default_settings["subtitle"] = ", ".join([a["name"] for a in api_info["album"]["artists"]])
            if len(default_settings["subtitle"]) > 17:
                default_settings["subtitle"] = api_info["album"]["name"]
                default_settings["subtitle2"] = ", ".join([a["name"] for a in api_info["album"]["artists"]])
                if api_info["album"]["name"] == api_info["name"]:
                    default_settings["subtitle"] = ", ".join([a["name"] for a in api_info["album"]["artists"]])[0:17]
                    default_settings["subtitle2"] = ", ".join([a["name"] for a in api_info["album"]["artists"]])[17:len(api_info["album"]["artists"])]


    if layout_name == "template1.svg":
        if len(default_settings["title"]) > 15:
            default_settings["title_font_size"] = "8"
    elif layout_name == "template2.svg":
        if len(default_settings["title"]) > 15:
            default_settings["title_font_size"] = "8"
    
    line = default_settings["title"]
    n = default_settings["title_chunk_size"]
    chunks = [line[i:i+n] for i in range(0, len(line), n)]

    for i in range(len(chunks)):
        chunk = chunks[i]
        last_space = chunk.rfind(" ")
        if last_space > 10:
            if i < len(chunks) - 1:
                chunks[i] = chunk[0:last_space]
                chunks[i + 1] = chunk[last_space + 1:len(chunk)] + chunks[i + 1]

    default_settings["title_chunks"] = chunks

    if layout_name in ["template1.svg", "template2.svg"]:
        return Response(
            render_template(f'card_templates/{layout_name}', **default_settings), mimetype="image/svg+xml")
    abort(404) 
