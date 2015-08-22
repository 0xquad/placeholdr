#!/usr/bin/env python
#
# Copyright (c) 2015, Alexandre Hamelin <alexandre.hamelin gmail.com>
#
# A clone of placehold.it with Flask.


import sys
import re
from flask import Flask, url_for, request, abort, make_response
from flaskext.genshi import Genshi, render_template


app = Flask(__name__)
genshi = Genshi(app)


def render(template, **kwargs):
    """Render a template using the Genshi template engine."""

    kwargs.update({
        'static' : lambda res: url_for('static', filename=res)
    })
    return render_template(template, kwargs)


def run_app(app):
    """Run the application, accepting a few common options."""

    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option('-v', '--verbose', dest='verbose', default=False,
                      action='store_true',
                      help='Turn on debugging')
    parser.add_option('-p', '--port', dest='port', type=int, default=5000,
                      help='Specify the server port')
    parser.add_option('-l', '--listen', dest='listen_addr', default='::1',
                      help='Specify the listening address')
    options, args = parser.parse_args()
    app.run(host=options.listen_addr, port=options.port, debug=options.verbose)



def generate_placeholder(width, height, text, bgcolor, fgcolor, ext):
    """Generate the placeholder image based on the given parameters.

    The image is generated with ImageMagick convert(1) utility.

    If no width or height is defined (`None`), it is autodetermined by the
    underlying generator tool. The background and foreground colors are in the
    HTML notation, without the leading '#' sign (3 or 6 hexdigits). The text
    can be anything, but no escape sequences are recognized. The extension must
    be either png, gif or jpg, which will automatically determine the MIME type
    of the image.

    """
    import subprocess
    cmd = ['convert']
    size = '{}x{}'.format(width if width else '',
                          height if height else '')
    cmd.extend(['-size', size])
    cmd.extend(['-background', '#' + bgcolor])
    cmd.extend(['-fill', '#' + fgcolor])
    cmd.extend(['-gravity', 'center'])
    cmd.append('label:{}'.format(text))
    cmd.append('{}:-'.format(ext))

    try:
        #app.logger.debug('running command: {}'.format(cmd))
        image_data = subprocess.check_output(cmd)
    except subprocess.CalledProcessError:
        image_data = b''

    mime_types = {
        'png' : 'image/png',
        'jpg' : 'image/jpeg',
        'gif' : 'image/gif',
    }

    response = make_response(image_data)
    response.headers['content-type'] = mime_types[ext]

    return response



def get_size(url_part):
    """Parse the first part of the URL for the width and height values.

    They are returned in a tuple (width, height). The special tuple (None,
    None) is returned if the URL does not specify a valid dimension.

    In case of any error, the request is aborted with a 400 code (Bad Request).

    """

    match = re.match(r'(\d+)(x\d+)?', url_part)
    if match is None:
        return None, None
    width, height = match.groups()

    try:
        width = int(width)
    except ValueError:
        app.logger.fatal('invalid width: {}'.format(width))
        abort(400)

    try:
        if height:
            height = int(height[1:])
    except ValueError:
        app.logger.fatal('invalid height: {}'.format(height))
        abort(400)

    return width, height


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def home(path):
    """The home page, which also handles the image generator."""

    from tempfile import mkstemp
    import re

    if path == '':
        return render('home.html')

    path_parts = re.sub('^/', '', re.sub('/+', '/', path)).split('/')

    width, height = get_size(path_parts[0])
    bgcolor = path_parts[1] if len(path_parts) > 1 else '444'
    fgcolor = path_parts[2] if len(path_parts) > 2 else '888'

    if width is None and height is None:
        return render('home.html')

    size, _dot, ext = path_parts[0].partition('.')
    if _dot != '.':
        bgcolor, _dot, ext = bgcolor.partition('.')
    if _dot != '.':
        fgcolor, _dot, ext = fgcolor.partition('.')
    if _dot != '.':
        ext = 'png'

    if ext not in ('png', 'gif', 'jpg'):
        app.logger.fatal('invalid extension: {}'.format(ext))
        abort(400)

    color_re = re.compile(r'[0-9a-fA-F]{3}([0-9a-fA-F]{3})?$')
    if not color_re.match(bgcolor) or not color_re.match(fgcolor):
        app.logger.fatal('invalid colors: {}/{}'.format(bgcolor, fgcolor))
        abort(400)

    text = request.args.get('text') or \
                '{}x{}'.format(width, height if height else width)

    text = text.replace('\\', '\\\\').replace('%', '\\%')

    return generate_placeholder(width, height, text, bgcolor, fgcolor, ext)



# Run the application.
run_app(app)
