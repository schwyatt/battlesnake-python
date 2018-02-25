import bottle
import os

@bottle.route('/static/<path:path>')
def static(path):
    return bottle.static_file(path, root='static/')


@bottle.post('/start')
def start():
    data = bottle.request.json
    game_id = data['game_id']
    print('game id: %s' % (game_id)) # For log purposes, to indicate which game log is showing.

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


################################################################################


class Cell:
    def __init__(self, row, column):
        self.is_snakehead = False
        self.is_snakenemy = False # head of enemy snake(s)
        self.is_snakebody = False
        self.is_snaketail = False
        self.is_food = False
        self.coord = (row, column)
        self.symbol = {'snakehead': 's', 'snakenemy': 'e', 'snakebody': 'b', 'snaketail': 't', 'food': 'f', 'cell': '_'}
    
    def to_symbol(self):
        if self.is_snakehead == True:
            return(self.symbol['snakehead'])
        elif self.is_snakenemy == True:
            return(self.symbol['snakenemy'])
        elif self.is_food == True:
            return(self.symbol['food'])
        elif self.is_snakebody == True:
            return(self.symbol['snakebody'])
        elif self.is_snaketail == True:
            return(self.symbol['snaketail'])
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

    def place(self, instance, obj): # maybe break into 3 separate functions?
        if obj == 'food':
            for i in range(len(instance)):
                self.coord[instance[i].coord[0]][instance[i].coord[1]].is_food = True
        elif obj == 'enemy':
            for i in range(len(instance)):
                for j in range(len(instance[i].coord)):
                    if j == 0:
                        self.coord[instance[i].coord[j][0]][instance[i].coord[j][1]].is_snakenemy = True
                    elif j == len(instance[i].coord)-1:
                        self.coord[instance[i].coord[j][0]][instance[i].coord[j][1]].is_snaketail = True
                    else:
                        self.coord[instance[i].coord[j][0]][instance[i].coord[j][1]].is_snakebody = True
        elif obj == 'me':
            for j in range(len(instance.coord)):
                if j == 0:
                    self.coord[instance.coord[j][0]][instance.coord[j][1]].is_snakehead = True
                elif j == len(instance.coord)-1:
                    self.coord[instance.coord[j][0]][instance.coord[j][1]].is_snaketail = True
                else:
                    self.coord[instance.coord[j][0]][instance.coord[j][1]].is_snakebody = True
                 

class Food:
    def __init__(self, prepend, moi):
        self.coord = [prepend['y'], prepend['x']]
        self.distance = distance(moi, self)


class Enemy:
    def __init__(self, prepend):
        self.coord = [[prepend['body']['data'][j]['y'], prepend['body']['data'][j]['x']] for j in range(len(prepend['body']['data']))]
        self.length = prepend['length']
        self.tail = prepend['body(length-1)'] #should just be the last coordinates (point) in the list (body) - Im assuming this is the tail. But my syntax is not great, is this correct? 
        self.id = prepend['id']
        # distance to food
        # distance to me


class Me:
    def __init__(self, prepend):
        self.coord = [[prepend['body']['data'][j]['y'], prepend['body']['data'][j]['x']] for j in range(len(prepend['body']['data']))]
        self.health = prepend['health']
        self.length = prepend['length']
        self.id = prepend['id']


################################################################################


def distance(frm, to):
    dy = abs(to.coord[0] - frm.coord[0][0])
    dx = abs(to.coord[1] - frm.coord[0][1])
    return(sum([dy, dx]))
    
    
def safe(agrid, snake, prepend):
    directions = {
            'up': [snake.coord[0][0]-1, snake.coord[0][1]],
            'down': [snake.coord[0][0]+1, snake.coord[0][1]],
            'left': [snake.coord[0][0], snake.coord[0][1]-1],
            'right': [snake.coord[0][0], snake.coord[0][1]+1],
            } 

    space = [key for key in directions
            if 0 <= directions[key][0] < prepend['height']
            and 0 <= directions[key][1] < prepend['width']
            and agrid.coord[directions[key][0]][directions[key][1]].is_snakebody == False 
            and agrid.coord[directions[key][0]][directions[key][1]].is_snakenemy == False # Update this condition - set to two block buffer
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


###############################################################################


@bottle.post('/move')
def move():
    # Initialise board and stuff on board
    data = bottle.request.json

    grid = Grid(data)
    me = Me(data['you']) 

    foods = [Food(data['food']['data'][i], me) for i in range(len(data['food']['data']))]
    foods.sort(key = lambda food: food.distance)
    
    enemy = [Enemy(data['snakes']['data'][i]) for i in range(len(data['snakes']['data'])) if data['snakes']['data'][i]['id'] != me.id]

    
    # Goal is to create a list of tails on board, and sort by distance to our snake, including our own.
    tails = [Enemy(data['snakes']['data'][i], me).tail for i in range(len(data['enemy']['data']))]
    #sort tails
    
    
    # Grid for log purposes
    grid.place(foods, 'food')
    grid.place(enemy, 'enemy')
    grid.place(me, 'me')
    grid.print()
    
    # Route setter
    safety = safe(grid, me, data)
    route = path(me, foods[0], grid)
    routeTail = path(me, tails[0], grid) # Modeled after Dennis' path finding for food, but replaces - hopefully - with tails.

    for item in safety:
        if item in route:
            output = item
            break
        elif item in routeTail: # This way food is primary concern, tails secondary. Might consider changing this so that tails are primary until HP threshold reached, then foods primary.
            output = item
            break # don't know what this means, but syntax seems to suggest it goes here
        else:
            output = safety[-1]
    
    # Info for current turn, for log purposes
    print("Turn: %s" % (data['turn']))
    print('route: %s' % (route))
    print('safety: %s' % (safety))
    print('output: %s' % (output))

    return {
        'move': output,
        'taunt': 'python!'
    }



# Expose WSGI app (so gunicorn can find it)
application = bottle.default_app()
if __name__ == '__main__':
    bottle.run(application, host=os.getenv('IP', '0.0.0.0'), port=os.getenv('PORT', '8080'))
