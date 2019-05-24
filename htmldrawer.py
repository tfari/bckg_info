import json


def html_draw(data, filepath):
    """
    Generate the HTML for the report, save it under filepath/output.html.

    :param data: dict, InfoGet.run() return
    :param filepath: str, valid path

    :return: None
    """
    css = '''
    <style>
    body{
        color: #333333;
        background-color: #dddddd;
        font-family: Georgia;
    }
    h1{
        text-align: center;
    }
    
    .elem{
        background-color: white  ;
        width: 850px;
        margin-left: auto;
        margin-right: auto;
        margin-top: 20px;
        margin-bottom: 20px;
        border-radius: 10px;
        padding: 20px ;
        padding-left: 40px ;
        padding-right: 40px ;
    }
    .aligncenter{
        text-align: center;
    }
    
    </style>
    '''

    # START
    start = '''<!DOCTYPE html>\n<html>\n%s\n<head>\n\t\t<title>Report on: %s</title>\n</head>\n<body>\n\t''' \
            % (css, data['url'])
    end = '\n\t</body>\n</html>'
    output = start

    # TITLE
    output += '\n\t\t\t<div class="elem">'
    output += '\n\t\t\t<h1>Report on %s</h1>' % data['url']

    # TOP-BAR
    sections = ['main', 'whois', 'geolocation', 'builtwith', 'robots', 'sitemap', 'wiki']
    output += '\n\t\t\t<p class="aligncenter">'
    for section in sections:
        output += '<a href=#%s>%s</a> | ' % (section, section)
    output += '</p>'
    output += '\n\t\t\t</div>'

    # MAIN
    output += '\n\t\t\t<a name="main"></a>'
    output += '\n\t\t\t<div class="elem">'
    output += '\n\t\t\t<h2><b><u>Main:</u></b></h2>'
    output += '''
    \n\t\t\t<b>URL:</b> %s
    \t\t\t<br><b>IP:</b> %s
    \t\t\t<br><b>TITLE:</b> %s
    \t\t\t<br><b>ESTIMATED SIZE:</b> <a href=%s>%s</a>
    \t\t\t<br><b>POTENTIAL API:</b> <a href=%s>%s</a>
    \t\t\t<br><b>LINK TO LATEST NEWS:</b> <a href=%s>%s</a>
    ''' % (data['url'], data['ip'], data['title'], data['estimated'][0], data['estimated'][1],
           data['potential_api'], data['potential_api'], data['news_url'], data['news_url'])
    output += '\n\t\t\t</div>'

    # WHOIS
    output += '\n\t\t\t<a name="whois"></a>'
    output += '\n\t\t\t<div class="elem">'
    output += '\n\t\t\t<h2><b><u>Whois:</u></b></h2>'
    if data['whois']:
        output += '\n\t\t\t<ul>'
        for key in data['whois'].keys():
            if isinstance(data['whois'][key], list):
                output += '\n\t\t\t\t<li><b>%s</b>' % key
                output += '\n\t\t\t\t<ul>'
                for elem in data['whois'][key]:
                    output += '\n\t\t\t\t\t<li>%s</li>' % elem
                output += '\n\t\t\t\t</ul></li>'
            else:
                output += '\n\t\t\t\t<li><b>%s:</b> %s</li>' % (key, data['whois'][key])
        output += '\n\t\t\t</ul>'
        output += '\n\t\t\t<p class="aligncenter"><a href="%s"><iframe height=300 width=300 ' \
                  'src="%s" frameborder="0" scrolling="no" marginheight="0" marginwidth="0">' \
                  '</iframe></a></p>' % (data['geo_maps'][0], data['geo_maps'][0])
    output += '\n\t\t\t</div>'

    # GEOLOCATION
    output += '\n\t\t\t<a name="geolocation"></a>'
    output += '\n\t\t\t<div class="elem">'
    output += '\n\t\t\t<h2><b><u>Geolocation:</u></b></h2>'
    if data['geo_location']:
        output += '\n\t\t\t\t<ul>'
        for key in data['geo_location'].keys():
            if isinstance(data['geo_location'][key], list):
                output += '\n\t\t\t<li><b>%s</b>' % key
                output += '\n\t\t\t\t<li><ul>'
                for elem in data['geo_location'][key]:
                    output += '\n\t\t\t\t\t<li>%s</li>' % elem
                output += '\n\t\t\t\t</ul></li>'
            else:
                output += '\n\t\t\t\t<li><b>%s:</b> %s</li>' % (key, data['geo_location'][key])
        output += '\n\t\t\t</ul>'
        output += '\n\t\t\t<p class="aligncenter"><a href="%s"><img width=300 height=300 src="location.jpg"></a></p>' \
                  % data['geo_maps'][1]
    output += '\n\t\t\t</div>'

    # BUILTWITH
    output += '\n\t\t\t<a name="builtwith"></a>'
    output += '\n\t\t\t<div class="elem">'
    output += '\n\t\t\t<h2><b><u>Builtwith:</u></b></h2>'
    if data['builtwith']:
        output += '\n\t\t\t<ul>'
        for elem in data['builtwith']:
            output += '\n\t\t\t\t<li><b>%s</b></li>' % elem
        output += '\n\t\t\t</ul>'
    output += '\n\t\t\t</div>'

    # ROBOTS
    output += '\n\t\t\t<a name="robots"></a>'
    output += '\n\t\t\t<div class="elem">'
    output += '\n\t\t\t<h2><b><u>Robots:</u></b></h2>'
    if data['robots']:
        robots = data['robots'].split('\n')
        output += '\n\t\t\t<ul>'
        for elem in robots:
            output += '\n\t\t\t\t<li><b>%s</b></li>' % elem
        output += '\n\t\t\t</ul>'
    output += '\n\t\t\t</div>'

    # SITEMAP
    output += '\n\t\t\t<a name="sitemap"></a>'
    output += '\n\t\t\t<div class="elem">'
    output += '\n\t\t\t<h2><b><u>Sitemap:</u></b></h2>'
    if data['sitemap']:
        output += '\n\t\t\t\t<br><iframe width=850 height=800 src=%s></iframe>' % data['sitemap']
    output += '\n\t\t\t</div>'

    # WIKI
    output += '\n\t\t\t<a name="wiki"></a>'
    output += '\n\t\t\t<div class="elem">'
    output += '\n\t\t\t<h2><b><u>Wiki:</u></b></h2>'
    if data['wiki']:
        output += '\n\t\t\t\t<br><iframe src=%s width=850 height=800></iframe>' % data['wiki']
    output += '\n\t\t\t</div>'

    # END
    output += end

    # SAVE
    with open('%s/output.html' % filepath, 'w', encoding='utf-8') as f:
        f.write(output)

