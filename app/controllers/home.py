# -*- coding: utf-8 -*-
from flask import Blueprint, render_template
from urllib.parse import quote
import os
from dotenv import load_dotenv

load_dotenv()

blueprint = Blueprint('home', __name__)

@blueprint.route('/')
def index():
    return render_template('home/index.html')
