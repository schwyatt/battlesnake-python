board_height = board_width = 5

grid = [[0 for col in range(board_height)] for row in range(board_width)]

FOOD = "f"
food = [
    [1, 0]
]


for f in food:
    print(f)
    grid[f[0]][f[1]] = FOOD

print(grid)

