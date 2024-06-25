import numpy as np
from collections import deque
from state import *

#def is_valid_position(x, y, grid):
#    return 0 <= x < grid.shape[0] and 0 <= y < grid.shape[1] and grid[x, y] != WALL

def is_valid_position(x, y, state: BFS_State):
    return not state.is_wall(x, y)

def bfs_find_furthest_unexplored(px, py,state: BFS_State):
    queue = deque([(px, py)])
    visited = set()
    visited.add((px, py))
    
    furthest_node = (px, py)
    
    while queue:
        cx, cy = queue.popleft()
        print(f'{cx},{cy}')
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = cx + dx, cy + dy
            if (nx, ny) not in visited and not state.is_visited(nx, ny) and is_valid_position(nx, ny, state):
                visited.add((nx, ny))
                queue.append((nx, ny))
                furthest_node = (nx, ny)
                
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

def choose_action(px, py, vx, vy, grid, state: BFS_State):
    target = bfs_find_furthest_unexplored(state.R, state.R,state)
    print(target)
    if target:
        target_x, target_y = target
        ax, ay = determine_acceleration(target_x, target_y, px, py, vx, vy)
        next_x, next_y, next_vx, next_vy = get_next_position(px, py, vx, vy, ax, ay)

        if is_valid_position(next_x, next_y, state):
            state.add_to_visited(px, py)
            return ax, ay
        else:
            # If the direct path to the furthest unexplored node is blocked, explore around
            for ax in [-1, 0, 1]:
                for ay in [-1, 0, 1]:
                    if ax == 0 and ay == 0:
                        continue
                    next_x, next_y, next_vx, next_vy = get_next_position(px, py, vx, vy, ax, ay)
                    if is_valid_position(next_x, next_y, state) and (next_x, next_y) not in state.visited:
                        state.add_to_visited(px, py)
                        return ax, ay
    
    # Fallback mechanism: Move towards the least visited direction
    min_visits = float('inf')
    best_action = (0, 0)
    for ax in [-1, 0, 1]:
        for ay in [-1, 0, 1]:
            if ax == 0 and ay == 0:
                continue
            next_x, next_y, next_vx, next_vy = get_next_position(px, py, vx, vy, ax, ay)
            if is_valid_position(next_x, next_y, state) and (next_x, next_y) not in state.visited:
                num_visits = sum((next_x + dx, next_y + dy) in state.visited for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)])
                if num_visits < min_visits:
                    min_visits = num_visits
                    best_action = (ax, ay)
    state.add_to_visited(px, py)
    return best_action
