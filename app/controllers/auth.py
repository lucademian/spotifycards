# -*- coding: utf-8 -*-
import functools, json, requests, uuid, urllib3, os, urllib

from flask import flash, redirect, render_template, request, abort, session
from flask import Blueprint, session, url_for, g
from flask_login import login_user

from app.models.user import User

blueprint = Blueprint('auth', __name__, url_prefix='/auth')

@blueprint.route('/login/spotify')
def spotifylogin():
    if 'uid' not in session:
        session['uid'] = str(uuid.uuid4())

    return redirect("https://accounts.spotify.com/authorize?response_type=token&client_id=" 
        + os.getenv('SPOTIFY_CLIENT_ID', default='')
        + "&scope=" 
        + urllib.parse.quote("user-read-private user-read-email")
        + "&redirect_uri=" 
        + urllib.parse.quote(os.getenv('SPOTIFY_REDIRECT_URI', default=''))
        + "&state=" 
        + session['uid'])

@blueprint.route('/callback/spotify/', methods=('GET', 'POST'))
def spotifyCallback():
    if 'access_token' in request.args and 'state' in request.args and request.args.get('state') == session['uid']:

        if 'access_token' in request.args:
            access_token = request.args.get('access_token')

        if 'refresh_token' in request.args:
            refresh_token = request.args.get('refresh_token')

        if access_token is None:
            flash('Could not authorize your request. Please try again.', 'danger')
            return abort(404)

        user = User.find_or_create_from_token(access_token)
        user.access_token = access_token
        if refresh_token is not None:
            user.refresh_token = refresh_token
        user.token_expires_at = request.args.get('expires_in')

        login_user(user)

        return redirect(url_for('home.index'))
    else:
        abort(500)

@blueprint.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home.index'))
