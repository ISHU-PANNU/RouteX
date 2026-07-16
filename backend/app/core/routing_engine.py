from typing import List, Tuple

def calculate_tour_cost(tour: List[int], cost_matrix: List[List[int]]) -> int:
    """
    Calculate the total distance or time of a tour sequence.
    """
    cost = 0
    for i in range(len(tour) - 1):
        cost += cost_matrix[tour[i]][tour[i + 1]]
    return cost

def solve_nearest_neighbor(cost_matrix: List[List[int]]) -> List[int]:
    """
    Generate an initial tour using the Nearest Neighbor heuristic starting at Depot (index 0).
    The resulting tour will start and end at the depot (index 0).
    """
    n = len(cost_matrix)
    if n == 0:
        return []
    if n == 1:
        return [0, 0]

    visited = [False] * n
    visited[0] = True
    tour = [0]
    
    current = 0
    for _ in range(n - 1):
        next_node = -1
        min_dist = float('inf')
        for neighbor in range(n):
            if not visited[neighbor] and cost_matrix[current][neighbor] < min_dist:
                min_dist = cost_matrix[current][neighbor]
                next_node = neighbor
        if next_node != -1:
            visited[next_node] = True
            tour.append(next_node)
            current = next_node
    
    # Return to depot
    tour.append(0)
    return tour

def solve_tsp_2opt(cost_matrix: List[List[int]]) -> Tuple[List[int], int]:
    """
    Optimize the TSP tour using the deterministic 2-opt local search algorithm.
    Starts and ends at depot (index 0).
    """
    n = len(cost_matrix)
    if n <= 1:
        return [0, 0], 0
    if n == 2:
        tour = [0, 1, 0]
        cost = calculate_tour_cost(tour, cost_matrix)
        return tour, cost

    # 1. Create an initial tour
    best_tour = solve_nearest_neighbor(cost_matrix)
    best_cost = calculate_tour_cost(best_tour, cost_matrix)

    improved = True
    while improved:
        improved = False
        # Do not alter the starting depot (index 0) or the ending depot (last index)
        for i in range(1, len(best_tour) - 2):
            for j in range(i + 1, len(best_tour) - 1):
                # We attempt to reverse the sequence between i and j
                new_tour = best_tour[:]
                new_tour[i:j + 1] = reversed(best_tour[i:j + 1])
                new_cost = calculate_tour_cost(new_tour, cost_matrix)

                if new_cost < best_cost:
                    best_tour = new_tour
                    best_cost = new_cost
                    improved = True
                    break # Break out to outer loop to start scanning with the improved tour
            if improved:
                break

    return best_tour, best_cost
