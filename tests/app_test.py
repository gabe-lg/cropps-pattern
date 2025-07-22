import init
import unittest
import numpy as np
import threading
import queue
from unittest.mock import Mock, patch
from PIL import Image
from src.history import History, Action
from src.searcher import Searcher
from lib.point import Point, PointNode
from src.app import ImageType, ImageList, ImageNode, ImageViewer


class TestImageViewer(unittest.TestCase):
    def setUp(self):
        self.viewer = ImageViewer()
        self.test_image = np.zeros((100, 100), dtype=np.uint8)
        self.test_image_pil = Image.fromarray(self.test_image)

    def test_clear(self):
        # Setup test state
        self.viewer.image_list.push(
            ImageNode(ImageType(self.test_image_pil, 0)))
        self.viewer.image_list.peek().value.lines = [[Point(1, 1), Point(2, 2)]]
        self.viewer.image_list.peek().value.circles = [Point(3, 3)]

        # Test clear
        self.viewer.clear()

        # Verify
        current_image = self.viewer.image_list.peek().value
        self.assertEqual(len(current_image.lines), 0)
        self.assertEqual(len(current_image.circles), 0)
        self.assertFalse(self.viewer.searching)
        self.assertTrue(self.viewer.searcher.canceled)

    def test_on_click(self):
        # Setup mock event and image
        event = Mock()
        event.x, event.y = 50, 50
        self.viewer.image_list.push(
            ImageNode(ImageType(self.test_image_pil, 0)))
        self.viewer.orig_image = (self.test_image_pil, None)

        # Test click
        with patch('cv2.circle') as mock_circle:
            self.viewer.on_click(event)

            # Verify
            current_image = self.viewer.image_list.peek().value
            self.assertEqual(len(current_image.circles), 1)
            self.assertEqual(current_image.circles[0], Point(50, 50))
            mock_circle.assert_called_once()

    @patch('tkinter.messagebox.askokcancel')
    @patch('tkinter.filedialog.askopenfilename')
    def test_open_file(self, mock_open, mock_ask):
        # Setup mocks
        mock_ask.return_value = True
        mock_open.return_value = "test.png"

        with patch('PIL.Image.open', return_value=self.test_image_pil):
            self.viewer.open(is_folder=False)

            # Verify
            self.assertEqual(self.viewer.image_list.peek().value.id, 0)
            self.assertIsNotNone(self.viewer.curr_image)
            self.assertFalse(self.viewer.searching)

    def test_compile_search(self):
        # Setup test data
        self.viewer.image_list.push(
            ImageNode(ImageType(self.test_image_pil, 0)))
        self.viewer.searcher.push(self.viewer.searcher.clicks,
                                  PointNode(Point(1, 1)))
        self.viewer.searcher.push(self.viewer.searcher.clicks,
                                  PointNode(Point(2, 2)))

        # Test compilation
        with patch('tkinter.Toplevel'), \
                patch('tkinter.ttk.Progressbar'), \
                patch('src.searcher.Searcher.search',
                      return_value=[(1, 1), (2, 2)]):
            result = self.viewer._compile_search()

            # Verify
            self.assertTrue(result)
            current_image = self.viewer.image_list.peek().value
            self.assertEqual(len(current_image.lines), 1)
            self.assertEqual(len(current_image.lines[0]), 2)

    def test_get_coor(self):
        # Setup mock event and image state
        event = Mock()
        event.x, event.y = 150, 150
        test_image = np.zeros((200, 200), dtype=np.uint8)
        self.viewer.curr_image = (Image.fromarray(test_image), None)

        # Test coordinate translation
        x, y, image = self.viewer._get_coor(event)

        # Verify coordinates are within bounds and properly scaled
        self.assertTrue(0 <= x < 200)
        self.assertTrue(0 <= y < 200)
        self.assertIsInstance(image, Image.Image)

    def test_play_sequence(self):
        # Setup test sequence
        for i in range(3):
            self.viewer.image_list.push(
                ImageNode(ImageType(self.test_image_pil, i)))

        # Test play sequence
        with patch('app.ImageViewer._compile_search', return_value=True):
            self.viewer._play()

            # Verify
            self.assertFalse(self.viewer.playing)
            self.assertTrue(self.viewer.image_list.curr_at_tail())


if __name__ == '__main__':
    unittest.main()