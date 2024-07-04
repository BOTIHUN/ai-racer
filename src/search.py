import numpy as np
from collections import deque
from state import *
import heapq


def is_valid_position(x, y, grid):
    return 0 <= x < grid.shape[0] and 0 <= y < grid.shape[1] and grid[x, y] != WALL

def bfs_find_nearest_target(grid, start, state: State):
    priority_queue = []
    heapq.heappush(priority_queue, (0, start))
    visited = set()
    visited.add(start)
    
    while priority_queue:
        _, (cx, cy) = heapq.heappop(priority_queue)
            
        if grid[cx, cy] == GOAL:
            return (cx, cy)
        
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = cx + dx, cy + dy
            gx, gy = state.to_global(nx - start[0], ny - start[1])
            
            if is_valid_position(nx, ny, grid) and (nx, ny) not in visited and not state.is_visited(gx, gy):
                visited.add((nx, ny))
                priority = grid[nx, ny]
                heapq.heappush(priority_queue, (priority, (nx, ny)))
                
    return max(visited, key=lambda pos: abs(pos[0] - start[0]) + abs(pos[1] - start[1]))

def determine_acceleration(target_x, target_y, x, y, vx, vy, state: State):
    ax, ay = 0, 0
    if target_x > x + vx:
        ax = 1
    elif target_x < x + vx:
        ax = -1
    
    if target_y > y + vy:
        ay = 1
    elif target_y < y + vy:
        ay = -1
    
    lax, lay = state.player_last_acc
    if lax == -1 * ax and lay == -1 * ay:
        print(f'{lax}, {lay}, {ax}, {ay}')
        ax *= -1
        ay *= -1
    
    state.player_last_acc = ax, ay
        
    return ax, ay

def get_possible_actions():
    return [-1, 0, 1]

def reconstruct_path(came_from, current):
    total_path = [current]
    while current in came_from:
        current = came_from[current]
        total_path.append(current)
    total_path.reverse()
    return total_path

def heuristic(x, y, grid, state: State, start):
    priority = 0
    Gx, Gy = state.to_global(x - start[0], y - start[1])
    if state.is_visited(Gx, Gy):
        priority -= 20
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nx, ny = x + dx, y + dy
        if 0 <= nx < grid.shape[0] and 0 <= ny < grid.shape[1]:
            gx, gy = state.to_global(nx - start[0], ny - start[1])
            if state.is_visited(gx, gy):
                priority -= 20
            if grid[nx, ny] == NOT_VISIBLE:
                priority += 1
            elif grid[nx, ny] == EMPTY:
                priority += 0.5
    return priority


def a_star_search(grid, start, state: State):
    # Initialize structures
    pq = []
    heapq.heappush(pq, (0, start))
    came_from = {}
    g_score = {start: 0}
    max_f_score_node = (0, start)  # To track the node with maximum f_score
    heur_map = {}
    f_map = {}
    
    while pq:
        current_f, (cx, cy) = heapq.heappop(pq)
        
        # Check if we have reached the goal
        if grid[cx, cy] == GOAL:
            path = []
            while (cx, cy) in came_from:
                path.append((cx, cy))
                cx, cy = came_from[(cx, cy)]
            path.reverse()
            return path

        if max_f_score_node[0] == 0:
            max_f_score_node = (current_f, (cx, cy))
        if current_f > max_f_score_node[0]:
            max_f_score_node = (current_f, (cx, cy))
        
        # Explore neighbors
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = cx + dx, cy + dy
            if is_valid_position(nx, ny, grid):
                tentative_g_score = g_score[(cx, cy)] + 1
                if (nx, ny) not in g_score or tentative_g_score < g_score[(nx, ny)]:
                    came_from[(nx, ny)] = (cx, cy)
                    g_score[(nx, ny)] = tentative_g_score
                    heur = heuristic(nx, ny, grid, state, start)
                    heur_map[(nx, ny)] = heur
                    f_score = tentative_g_score + heur
                    f_map[(nx, ny)] = f_score;
                    gx, gy = state.to_global(nx - start[0], ny - start[1])
                    if state.is_visited(gx, gy):
                        f_score -= 20 * tentative_g_score
                    heapq.heappush(pq, (f_score, (nx, ny)))

    print(f'heuristics neighbour map: {heur_map}')
    print(f'f_score neighbour map: {f_map}')
    if max_f_score_node[0] != 0:
        path = []
        cx, cy = max_f_score_node[1]
        while (cx, cy) in came_from:
            path.append((cx, cy))
            cx, cy = came_from[(cx, cy)]
        path.reverse()
        #path.append(start)
        #path.append((cx, cy))
        print(f'the maximum f_score node: {cx}, {cy} : {max_f_score_node[0]}')
        return path, f_map
    else:
        return None  # No path found with a good f_score

def determine_acceleration_a_star(path, vx, vy):
    if len(path) < 2:
        return 0, 0
    
    next_x, next_y = path[1]
    current_x, current_y = path[0]

    print(f'next_x {next_x}, next_y {next_y}')
    print(f'current_x {current_x}, current_y {current_y}')
    print(f'path {path}')
    
    ax = next_x - current_x - vx
    ay = next_y - current_y - vy
    
    ax = max(-1, min(1, ax))
    ay = max(-1, min(1, ay))
    
    return ax, ay

def choose_action(x, y, vx, vy, grid, state: State):
    path, f_map = a_star_search(grid, (x, y), state)
    if path:
        #target_x, target_y = target
        #ax, ay = determine_acceleration(target_x, target_y, x, y, vx, vy, state)
        ax, ay = determine_acceleration_a_star(path, vx, vy)
        state.f_maps.append(f_map)
        return ax,ay
    else:
        return 0, 0


