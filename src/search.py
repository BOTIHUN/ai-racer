import numpy as np
from collections import deque

EMPTY = 0
WALL = -1
START = 1
NOT_VISIBLE = 3
GOAL = 100

def is_valid_position(x, y, grid):
    return 0 <= x < grid.shape[0] and 0 <= y < grid.shape[1] and grid[x, y] != WALL

def bfs_find_nearest_target(grid, start):
    #rows, cols = grid.shape
    queue = deque([start])
    visited = set()
    visited.add(start)
    
    while queue:
        cx, cy = queue.popleft()
        
        if grid[cx, cy] == NOT_VISIBLE or grid[cx, cy] == GOAL:
            return (cx, cy)
        
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = cx + dx, cy + dy
            if is_valid_position(nx, ny, grid) and (nx, ny) not in visited:
                visited.add((nx, ny))
                queue.append((nx, ny))
                
    return None  # No target found

def bfs_find_furthest_valid_node(grid, start):
    queue = deque([start])
    visited = set()
    visited.add(start)
    furthest_node = start
    
    while queue:
        cx, cy = queue.popleft()
        
        # Check if current node is further than previously found furthest_node
        if (cx - start[0])**2 + (cy - start[1])**2 > (furthest_node[0] - start[0])**2 + (furthest_node[1] - start[1])**2:
            furthest_node = (cx, cy)
        
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = cx + dx, cy + dy
            if is_valid_position(nx, ny, grid) and (nx, ny) not in visited:
                visited.add((nx, ny))
                queue.append((nx, ny))
                
    return furthest_node

def get_possible_actions():
    return [-1, 0, 1]

def get_next_position(x, y, vx, vy, ax, ay):
    next_vx = vx + ax
    next_vy = vy + ay
    next_x = x + next_vx
    next_y = y + next_vy
    return next_x, next_y, next_vx, next_vy

def determine_acceleration(target_x, target_y, x, y, vx, vy):
    ax, ay = 0, 0
    if target_x > x + vx:
        ax = 1
    elif target_x < x + vx:
        ax = -1
    
    if target_y > y + vy:
        ay = 1
    elif target_y < y + vy:
        ay = -1
        
    return ax, ay

def choose_action(x, y, vx, vy, grid):
    target = bfs_find_furthest_valid_node(grid, (x, y))
    if target:
        target_x, target_y = target
        ax, ay = determine_acceleration(target_x, target_y, x, y, vx, vy)

        return ax, ay
    else:
        return 0, 0


