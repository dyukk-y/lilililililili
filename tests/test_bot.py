"""
Unit tests for AutoPost Bot
Run with: python -m pytest tests/
"""

import unittest
import os
import json
import tempfile
from datetime import datetime, timedelta
import pytz
from bot import AutoPostBot


class TestAutoPostBot(unittest.TestCase):
    """Tests for AutoPostBot class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary storage file
        self.temp_dir = tempfile.mkdtemp()
        self.storage_file = os.path.join(self.temp_dir, "test_posts.json")
        self.bot = AutoPostBot(storage_file=self.storage_file)
    
    def tearDown(self):
        """Clean up after tests"""
        # Remove test storage file
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
    
    # ========================================================================
    # PUBLISH TESTS
    # ========================================================================
    
    def test_publish_post(self):
        """Test publishing a post"""
        post_id = self.bot.publish_post(content="Test post")
        
        self.assertIsNotNone(post_id)
        self.assertIn(post_id, self.bot.posts)
        self.assertEqual(self.bot.posts[post_id]['content'], "Test post")
        self.assertEqual(self.bot.posts[post_id]['status'], "published")
    
    def test_publish_post_with_delete(self):
        """Test publishing post with auto-delete"""
        post_id = self.bot.publish_post(
            content="Temporary post",
            delete_after_hours=1
        )
        
        self.assertIsNotNone(post_id)
        self.assertIn('delete_at', self.bot.posts[post_id])
    
    def test_publish_multiple_posts(self):
        """Test publishing multiple posts"""
        ids = []
        for i in range(5):
            post_id = self.bot.publish_post(f"Post {i}")
            ids.append(post_id)
        
        self.assertEqual(len(self.bot.posts), 5)
        for post_id in ids:
            self.assertIn(post_id, self.bot.posts)
    
    # ========================================================================
    # DELETE TESTS
    # ========================================================================
    
    def test_delete_post(self):
        """Test deleting a post"""
        post_id = self.bot.publish_post("Post to delete")
        result = self.bot.delete_post(post_id)
        
        self.assertTrue(result)
        self.assertNotIn(post_id, self.bot.posts)
    
    def test_delete_nonexistent_post(self):
        """Test deleting non-existent post"""
        result = self.bot.delete_post("nonexistent")
        
        self.assertFalse(result)
    
    # ========================================================================
    # GET TESTS
    # ========================================================================
    
    def test_get_post(self):
        """Test getting post information"""
        post_id = self.bot.publish_post("Test post")
        post = self.bot.get_post(post_id)
        
        self.assertIsNotNone(post)
        self.assertEqual(post['content'], "Test post")
        self.assertEqual(post['id'], post_id)
    
    def test_get_nonexistent_post(self):
        """Test getting non-existent post"""
        post = self.bot.get_post("nonexistent")
        
        self.assertIsNone(post)
    
    # ========================================================================
    # LIST TESTS
    # ========================================================================
    
    def test_list_all_posts(self):
        """Test listing all posts"""
        for i in range(3):
            self.bot.publish_post(f"Post {i}")
        
        posts = self.bot.list_posts()
        
        self.assertEqual(len(posts), 3)
    
    def test_list_published_posts(self):
        """Test listing only published posts"""
        for i in range(2):
            self.bot.publish_post(f"Published {i}")
        
        published = self.bot.list_posts(status='published')
        
        self.assertEqual(len(published), 2)
        for post in published:
            self.assertEqual(post['status'], 'published')
    
    # ========================================================================
    # TIMEZONE TESTS
    # ========================================================================
    
    def test_get_current_nsk_time(self):
        """Test getting current NSK time"""
        nsk_time = self.bot.get_current_nsk_time()
        
        self.assertIsNotNone(nsk_time)
        self.assertEqual(nsk_time.tzinfo, self.bot.nsk_tz)
    
    def test_convert_to_nsk_utc(self):
        """Test timezone conversion from UTC"""
        utc_time = datetime(2026, 2, 23, 12, 0, 0, tzinfo=pytz.UTC)
        nsk_time = self.bot.convert_to_nsk_time(utc_time, from_tz="UTC")
        
        self.assertIsNotNone(nsk_time)
        # UTC 12:00 should be NSK 19:00 (UTC+7)
        self.assertEqual(nsk_time.hour, 19)
    
    def test_convert_to_nsk_moscow(self):
        """Test timezone conversion from Moscow"""
        moscow_time = datetime(2026, 2, 23, 15, 30, 0)
        nsk_time = self.bot.convert_to_nsk_time(moscow_time, from_tz="Europe/Moscow")
        
        self.assertIsNotNone(nsk_time)
        # Moscow 15:30 should be NSK 18:30 (NSK is 3 hours ahead)
        self.assertEqual(nsk_time.hour, 18)
        self.assertEqual(nsk_time.minute, 30)
    
    # ========================================================================
    # STORAGE TESTS
    # ========================================================================
    
    def test_save_and_load_posts(self):
        """Test saving and loading posts"""
        # Save posts
        post_id = self.bot.publish_post("Persistent post")
        
        # Create new bot instance with same storage
        bot2 = AutoPostBot(storage_file=self.storage_file)
        
        # Check if post was loaded
        self.assertEqual(len(bot2.posts), 1)
        self.assertIn(post_id, bot2.posts)
        self.assertEqual(bot2.posts[post_id]['content'], "Persistent post")
    
    def test_posts_json_format(self):
        """Test that posts are saved in valid JSON format"""
        self.bot.publish_post("Test post")
        
        # Check if file is valid JSON
        with open(self.storage_file, 'r') as f:
            data = json.load(f)
        
        self.assertIsInstance(data, dict)
        self.assertGreater(len(data), 0)
    
    # ========================================================================
    # SCHEDULER TESTS
    # ========================================================================
    
    def test_scheduler_running(self):
        """Test that scheduler is running"""
        self.assertTrue(self.bot.scheduler.running)
    
    def test_get_jobs_info(self):
        """Test getting jobs information"""
        jobs = self.bot.get_jobs_info()
        
        self.assertIsInstance(jobs, list)


class TestTimezoneConversion(unittest.TestCase):
    """Tests for timezone conversion functionality"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.storage_file = os.path.join(self.temp_dir, "test_tz.json")
        self.bot = AutoPostBot(storage_file=self.storage_file)
    
    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
    
    def test_multiple_timezone_conversions(self):
        """Test conversions from multiple timezones"""
        timezones = [
            ("UTC", 12, 0, 19, 0),  # UTC 12:00 -> NSK 19:00
            ("Europe/London", 12, 0, 20, 0),  # London 12:00 -> NSK 20:00 (winter)
            ("Europe/Moscow", 15, 30, 18, 30),  # Moscow 15:30 -> NSK 18:30
            ("America/New_York", 7, 0, 20, 0),  # NY 7:00 -> NSK 20:00 (winter)
        ]
        
        for tz_name, src_h, src_m, exp_h, exp_m in timezones:
            dt = datetime(2026, 2, 23, src_h, src_m, 0)
            result = self.bot.convert_to_nsk_time(dt, from_tz=tz_name)
            
            # Allow ±1 hour difference due to DST variations
            hour_diff = abs(result.hour - exp_h)
            self.assertLessEqual(hour_diff, 1, 
                f"Conversion from {tz_name} failed")


class TestIntegration(unittest.TestCase):
    """Integration tests"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.storage_file = os.path.join(self.temp_dir, "test_integration.json")
        self.bot = AutoPostBot(storage_file=self.storage_file)
    
    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
    
    def test_full_workflow(self):
        """Test complete bot workflow"""
        # 1. Publish posts
        post1 = self.bot.publish_post("Post 1", delete_after_hours=1)
        post2 = self.bot.publish_post("Post 2")
        
        # 2. List posts
        all_posts = self.bot.list_posts()
        self.assertEqual(len(all_posts), 2)
        
        # 3. Get specific post
        post = self.bot.get_post(post1)
        self.assertIsNotNone(post)
        
        # 4. Delete post
        self.bot.delete_post(post1)
        remaining = self.bot.list_posts()
        self.assertEqual(len(remaining), 1)
        
        # 5. Verify data persistence
        bot2 = AutoPostBot(storage_file=self.storage_file)
        self.assertEqual(len(bot2.posts), 1)
        self.assertIn(post2, [p['id'] for p in bot2.list_posts()])


if __name__ == '__main__':
    unittest.main()
