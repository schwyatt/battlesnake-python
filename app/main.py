import bottle
import os
import random

@bottle.route('/static/<path:path>')
def static(path):
    return bottle.static_file(path, root='static/')


@bottle.post('/start')
def start():
    data = bottle.request.json
    game_id = data['game_id']
    #board_width = data['width']
    #board_height = data['height']

    head_url = '%s://%s/static/head.png' % (
        bottle.request.urlparts.scheme,
        bottle.request.urlparts.netloc
    )

    return {
        'color': '#00FF00',
        'taunt': 'hissss...sss',
        'head_url': head_url,
        'name': 'our-snake',
        'head_type': 'pixel',
        'tail_type': 'pixel',
    }



class Food:
    def __init__(self, prepend):
        self.coord = [prepend['y'], prepend['x']]

class Snake:
    def __init__(self, prepend):
        self.coord = [[prepend['body']['data'][i]['y'], prepend['body']['data'][i]['x']] for i in range(len(prepend['body']['data']))]
        self.length = prepend['length']
        # distance to apple
        # distance to me

@bottle.post('/move')
def move():
    data = bottle.request.json

    directions = ['up', 'down', 'left', 'right']

    food = [Food(data['food']['data'][i]) for i in range(len(data['food']['data']))]
    snakes = [Snake(data['snakes']['data'][i]) for i in range(len(data['snakes']['data']))]

'''
    return {
        'move': random.choice(directions),
        'taunt': 'python!'
    }
'''

# Expose WSGI app (so gunicorn can find it)
application = bottle.default_app()
if __name__ == '__main__':
    bottle.run(application, host=os.getenv('IP', '0.0.0.0'), port=os.getenv('PORT', '8080'))
