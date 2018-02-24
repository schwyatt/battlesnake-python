import bottle
import os

@bottle.route('/static/<path:path>')
def static(path):
    return bottle.static_file(path, root='static/')


@bottle.post('/start')
def start():
    data = bottle.request.json
    game_id = data['game_id']

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


##############

class Cell:
    def __init__(self, row, column):
        self.is_it = {'snakehead': False, 'snakenemy': False, 'snakebody': False, 'food': False}
        self.coord = (row, column)
        self.symbol = {'snakehead': 's', 'snakenemy': 'e', 'snakebody': 'b', 'food': 'f', 'cell': '_'}
    
    def to_symbol(self):
        if self.is_it['snakehead'] == True:
            return(self.symbol['snakehead'])
        if self.is_it['snakenemy'] == True:
            return(self.symbol['snakenemy'])
        elif self.is_it['food'] == True:
            return(self.symbol['food'])
        elif self.is_it['snakebody'] == True:
            return(self.symbol['snakebody'])
        else:
            return(self.symbol['cell'])


class Grid:
    def __init__(self, prepend):
        self.coord = [[Cell(row, col) for col in range(prepend['width'])] for row in range(prepend['height'])]

    def print(self):
        for row in self.coord:
            for cell in row:
                print(cell.to_symbol(), end=" ")
            print("")

    def placer(self, instance, obj, status=False):
        if obj == 'food':
            for i in range(len(instance)):
                self.coord[instance[i].coord[0]][instance[i].coord[1]].is_it['food'] = status
        elif obj == 'enemy':
            for i in range(len(instance)):
                for j in range(len(instance[i].coord)):
                    if j == 0:
                        self.coord[instance[i].coord[j][0]][instance[i].coord[j][1]].is_it['snakenemy'] = status
                    else:
                        self.coord[instance[i].coord[j][0]][instance[i].coord[j][1]].is_it['snakebody'] = status
        elif obj == 'me':
            for j in range(len(instance.coord)):
                if j == 0:
                    self.coord[instance.coord[j][0]][instance.coord[j][1]].is_it['snakehead'] = status
                else:
                    self.coord[instance.coord[j][0]][instance.coord[j][1]].is_it['snakebody'] = status
                 

class Food:
    def __init__(self, prepend, moi):
        self.coord = [prepend['y'], prepend['x']]
        self.distance = distance(moi, self)


class Enemy:
    def __init__(self, prepend):
        self.coord = [[prepend['body']['data'][j]['y'], prepend['body']['data'][j]['x']] for j in range(len(prepend['body']['data']))]
        self.length = prepend['length']
        self.id = prepend['id']
        # distance to food
        # distance to me


class Me:
    def __init__(self, prepend):
        self.coord = [[prepend['body']['data'][j]['y'], prepend['body']['data'][j]['x']] for j in range(len(prepend['body']['data']))]
        self.health = prepend['health']
        self.length = prepend['length']
        self.id = prepend['id']

##########

def distance(frm, to):
    dy = abs(to.coord[0] - frm.coord[0][0])
    dx = abs(to.coord[1] - frm.coord[0][1])
    return(sum([dy, dx]))
    

def safe(agrid, snake, prepend):
    old_direction = {
            'up': [snake.coord[0][0]-1, snake.coord[0][1]],
            'down': [snake.coord[0][0]+1, snake.coord[0][1]],
            'left': [snake.coord[0][0], snake.coord[0][1]-1],
            'right': [snake.coord[0][0], snake.coord[0][1]+1],
            } 

    direction = {
            key: [old_direction[key][0], old_direction[key][1]]
            for key in old_direction
            if 0 <= old_direction[key][0] < prepend['height']
            and 0 <= old_direction[key][1] < prepend['width']
            }

    space = [key for key in direction 
            if agrid.coord[direction[key][0]][direction[key][1]].is_it['snakebody'] == False 
            and agrid.coord[direction[key][0]][direction[key][1]].is_it['snakenemy'] == False
            ]
    return(space)
    

def path(frm, to, agrid):
    dy = to.coord[0] - frm.coord[0][0]
    dx = to.coord[1] - frm.coord[1][1]
    possible = []

    if dy > 0:
        possible.append('down')
    elif dy < 0:
        possible.append('up')

    if dx > 0:
        possible.append('right')
    elif dx < 0:
        possible.append('left')

    return(possible)

#########

@bottle.post('/move')
def move():
    data = bottle.request.json

    grid = Grid(data)
    me = Me(data['you']) 

    foods = [Food(data['food']['data'][i], me) for i in range(len(data['food']['data']))]
    foods.sort(key = lambda food: food.distance)

    enemy = [Enemy(data['snakes']['data'][i]) for i in range(len(data['snakes']['data'])) if data['snakes']['data'][i]['id'] != me.id]

    grid.placer(foods, 'food', True)
    grid.placer(enemy, 'enemy', True)
    grid.placer(me, 'me', True)
    grid.print()
    print("Turn: %s" % (data['turn']))
    

    route = path(me, foods[0], grid)
    empty = safe(grid, me, data)
    
    print('route: %s' % (route))
    print('empty: %s' % (empty))

    for item in route:
        if item in empty:
            output = item
            break
        else:
            output = empty[0]
    
    print('output: %s' % (output))

    return {
        'move': output,
        'taunt': 'python!'
    }

# Expose WSGI app (so gunicorn can find it)
application = bottle.default_app()
if __name__ == '__main__':
    bottle.run(application, host=os.getenv('IP', '0.0.0.0'), port=os.getenv('PORT', '8080'))
