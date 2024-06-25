import numpy as np
from collections import deque
from state import State

EMPTY = 0
WALL = -1
START = 1
NOT_VISIBLE = 3
GOAL = 100

def is_valid_position(x, y, grid):
    return 0 <= x < grid.shape[0] and 0 <= y < grid.shape[1] and grid[x, y] != WALL

def bfs_find_nearest_target(grid, start, state: State):
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
            gx, gy = state.to_global(nx - start[0], ny - start[1])
            if is_valid_position(nx, ny, grid) and (nx, ny) not in visited and not state.is_visited(gx, gy):
                visited.add((nx, ny))
                queue.append((nx, ny))
                
    return None  # No target found

def determine_acceleration(target_x, target_y, x, y, vx, vy, grid):
    ax, ay = 0, 0
    if target_x > x + vx:
        ax = 1
    elif target_x < x + vx:
        ax = -1
    
    if target_y > y + vy:
        ay = 1
    elif target_y < y + vy:
        ay = -1
    
    next_x = x + vx + ax
    next_y = y + vy + ay
    if grid[next_x, next_y] == WALL:
        # Avoid accelerating towards a wall
        if ax != 0:
            ax = -1 * ax
        if ay != 0:
            ay = -1 * ay
        
    return ax, ay

def choose_action(x, y, vx, vy, grid, state: State):
    target = bfs_find_nearest_target(grid, (x, y), state)
    if target:
        target_x, target_y = target
        ax, ay = determine_acceleration(target_x, target_y, x, y, vx, vy, grid)
        
        return ax,ay
    else:
        return 0, 0


