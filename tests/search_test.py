import os
import time

import init
import numpy as np
import random
import threading
import unittest
from lib.doubly_linked_list import DoublyLinkedNode as dln
from lib.point import Point
from PIL import Image
from queue import Queue
from src.searcher import Searcher


class SearchTest(unittest.TestCase):
    def test_empty(self):
        """
        Length of paths in a black image should be the sum of the x and y \
        distances between ``orig`` and ``dest``.
        """
        searcher = Searcher(threading.Lock())
        for i in range(10):
            size, orig, dest = self._make_rand(100)
            searcher.clear()

            img = Image.new('L', (size, size), 0)
            self._push_to_searcher(searcher, orig, dest)
            line = searcher.search(np.zeros((size, size), dtype=np.uint8),
                                   np.array(img))
            self.assertEqual(abs(dest.y - orig.y) + abs(dest.x - orig.x) + 1,
                             len(line))

    def test_diag(self):
        """
        All pixels along the bright diagonal should be in the path. \
        The length of the path should be ``2*(size-1)``.
        """
        searcher = Searcher(threading.Lock())
        for i in range(100):
            size, _, _ = self._make_rand(100)
            intensity = random.randint(1, 255)
            searcher.clear()

            data = np.zeros((size, size), dtype=np.uint8)
            for j in range(size): data[j, j] = intensity
            img = Image.fromarray(data)
            self._push_to_searcher(searcher, Point(0, 0),
                                   Point(size - 1, size - 1))
            line = searcher.search(np.zeros((size, size), dtype=np.uint8),
                                   np.array(img))

            for j in range(size):
                self.assertTrue((j, j) in line)
            self.assertEqual(2 * size - 1, len(line))

    def test_rand_path(self):
        """Generated path should be identical to the bright path in image."""
        exceptions = Queue()
        running = threading.Event()
        running.set()
        pool = []

        def dfs_worker(count):
            try:
                lock = threading.Lock()
                searcher = Searcher(lock)
                size, start, end = self._make_rand(max(7, 30 - count * 2))
                data = np.zeros((size, size), dtype=np.uint8)
                seen = {start}
                stack = [(start, [start])]

                while stack and running.is_set():
                    pos, path = stack.pop()
                    if pos == end:
                        for p in path:
                            data[*p._] = random.randint(128, 255)
                        with (lock):
                            searcher.clear()
                            self._push_to_searcher(searcher, start, end)
                            result = (searcher.search(np.zeros_like(data), data)
                            [::-1])
                            if (not result or len(path) != len(result) or
                                path != result):
                                raise AssertionError(
                                    f"Path mismatch: {path} != {result}")
                        return

                    random.shuffle(
                        nbrs := [pos + p for p in
                                 [Point(1, 0), Point(0, 1), Point(-1, 0),
                                  Point(0, -1)] if not (pos + p).out_of_bounds(
                                Point(size, size))])

                    for nb in nbrs:
                        if nb not in seen and not any(
                                nb + d in seen
                                for d in
                                [Point(1, 0), Point(0, 1), Point(-1, 0),
                                 Point(0, -1)]
                                if not (nb + d).out_of_bounds(
                                    Point(size, size))
                                   and nb + d != pos):
                            seen.add(nb)
                            stack.append((nb, path + [nb]))

                if not running.is_set(): raise KeyboardInterrupt()

            except Exception as e:
                exceptions.put(e)
                running.clear()

        try:
            for i in range(100):
                if not running.is_set() or not exceptions.empty():
                    raise exceptions.get() if not exceptions.empty() else KeyboardInterrupt()

                pool = [t for t in pool if t.is_alive()]
                while len(pool) > 10: pass
                t = threading.Thread(target=dfs_worker, args=(i,),
                                     daemon=True)
                t.start()
                pool.append(t)
                if i % 10 == 0: print(f"\nProgress: {i}/100\n")
                time.sleep(0.01)

        except (KeyboardInterrupt, Exception):
            running.clear()
            raise
        finally:
            print("\nTerminating...")
            for t in pool: t.join(timeout=10)
            running.clear()

    @staticmethod
    def _make_rand(max_size):
        size = random.randint(2, max_size)
        orig = Point(random.randint(0, size - 1), random.randint(0, size - 1))
        while True:
            dest = Point(random.randint(0, size - 1),
                         random.randint(0, size - 1))
            if dest != orig: break
        return size, orig, dest

    @staticmethod
    def _push_to_searcher(searcher, orig, dest):
        searcher.push(searcher.clicks, dln(orig))
        searcher.push(searcher.clicks, dln(dest))


if __name__ == '__main__':
    unittest.main()
