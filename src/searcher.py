import numpy as np
import heapq


class Searcher:
    def __init__(self):
        self.canceled = False
        self.clicks = []

    def add(self, click):
        self.clicks.append(click)

    def search(self, data: np.ndarray):
        self.canceled = False
        if not self.clicks or len(self.clicks) % 2: return None

        print("Searcher: starting search...")
        orig = self.clicks[-2]
        dest = self.clicks[-1]

        # Convert to grayscale if the image is in color
        if len(data.shape) == 3: data = np.mean(data, axis=2)

        height, width = data.shape
        inf = float('inf')

        # Initialize distances and visited arrays
        distances = np.full((height, width), inf)
        distances[orig[1], orig[0]] = 0
        visited = np.zeros((height, width), dtype=bool)
        # Store predecessors for path reconstruction
        predecessors = np.full((height, width, 2), -1, dtype=int)

        # Priority queue [(distance, (y, x))]
        pq = [(0, (orig[1], orig[0]))]

        def get_neighbors(y, x):
            # 8-directional movement
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    if dy == 0 and dx == 0:
                        continue
                    new_y, new_x = y + dy, x + dx
                    if 0 <= new_y < height and 0 <= new_x < width:
                        yield (new_y, new_x)

        # Dijkstra's algorithm with priority queue
        while pq:
            if self.canceled:
                print("Searcher: canceled")
                return None

            current_dist, (current_y, current_x) = heapq.heappop(pq)

            if visited[current_y, current_x]:
                continue

            if current_y == dest[1] and current_x == dest[0]:
                break

            visited[current_y, current_x] = True

            # Check all neighbors
            for neighbor_y, neighbor_x in get_neighbors(current_y, current_x):
                if visited[neighbor_y, neighbor_x]:
                    continue

                # Use inverse brightness as weight (brighter pixels = shorter path)
                weight = 1.0 / (data[
                                    neighbor_y, neighbor_x] + 1)  # Add 1 to avoid division by zero
                new_dist = current_dist + weight

                if new_dist < distances[neighbor_y, neighbor_x]:
                    distances[neighbor_y, neighbor_x] = new_dist
                    predecessors[neighbor_y, neighbor_x] = [current_y,
                                                            current_x]
                    heapq.heappush(pq, (new_dist, (neighbor_y, neighbor_x)))

        # Reconstruct path
        path = []
        current = (dest[1], dest[0])
        while current[0] != -1 and current[1] != -1:
            path.append(
                (current[1], current[0]))  # Convert back to (x,y) format
            current = tuple(predecessors[current[0], current[1]])

        path.reverse()

        if len(path) <= 1: return None

        print("Searcher: path found!")
        return path
