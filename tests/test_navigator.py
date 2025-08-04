import sys

sys.path.append('.')  # Adjust path to import from parent directory

import unittest

from baby_lights.navigator import Navigator

# ============================================================================
# AUTOMATED TESTS
# ============================================================================


class TestNavigator(unittest.TestCase):  # noqa
    """Comprehensive test suite for the Navigator component."""

    def test_constructor_with_valid_destinations(self):
        """Test basic constructor with valid destinations."""
        nav = Navigator(['home', 'about', 'contact'])
        self.assertEqual(nav.current(), 'home')
        self.assertEqual(nav.get_history(), [])

    def test_constructor_with_custom_initial_destination(self):
        """Test constructor with custom initial destination."""
        nav = Navigator(['home', 'about', 'contact'], initial_destination='about')
        self.assertEqual(nav.current(), 'about')

    def test_constructor_validation(self):
        """Test constructor validation for invalid inputs."""
        with self.assertRaises(ValueError):
            Navigator([])  # Empty destinations

        with self.assertRaises(ValueError):
            Navigator(['home'], initial_destination='invalid')  # Invalid initial

        with self.assertRaises(ValueError):
            Navigator(['home'], {'home': 'invalid'})  # Invalid fallback target

        with self.assertRaises(ValueError):
            Navigator(['home'], {'invalid': 'home'})  # Invalid fallback source

    def test_push_navigation_mode(self):
        """Test push navigation mode."""
        nav = Navigator(['home', 'about', 'contact'])
        nav.navigate('about', 'push')
        self.assertEqual(nav.current(), 'about')
        self.assertEqual(nav.get_history(), ['home'])

    def test_replace_navigation_mode(self):
        """Test replace navigation mode."""
        nav = Navigator(['home', 'about', 'contact'])
        nav.navigate('about', 'push')
        nav.navigate('contact', 'replace')
        self.assertEqual(nav.current(), 'contact')
        self.assertEqual(nav.get_history(), ['home'])  # Unchanged

    def test_invalid_navigation_mode(self):
        """Test invalid navigation mode raises error."""
        nav = Navigator(['home', 'about'])
        with self.assertRaises(ValueError):
            nav.navigate('about', 'invalid_mode')

    def test_jump_back_removes_target_and_newer_entries(self):
        """Test jump-back behavior removes target and newer entries."""
        nav = Navigator(['home', 'about', 'contact', 'blog'])
        nav.navigate('about', 'push')
        nav.navigate('contact', 'push')
        nav.navigate('blog', 'push')
        self.assertEqual(nav.get_history(), ['home', 'about', 'contact'])

        # Jump back to 'about'
        nav.navigate('about')
        self.assertEqual(nav.current(), 'about')
        self.assertEqual(nav.get_history(), ['home'])

    def test_noop_when_navigating_to_current_destination(self):
        """Test no-op when navigating to current destination."""
        nav = Navigator(['home', 'about'])
        nav.navigate('about', 'push')
        history_before = nav.get_history()

        nav.navigate('about')  # Should be no-op
        self.assertEqual(nav.current(), 'about')
        self.assertEqual(nav.get_history(), history_before)

    def test_history_never_contains_active_destination(self):
        """Test history never contains active destination."""
        nav = Navigator(['home', 'about', 'contact'])
        nav.navigate('about', 'push')
        nav.navigate('contact', 'push')

        self.assertNotIn(nav.current(), nav.get_history())

    def test_history_avoids_consecutive_duplicates(self):
        """Test history avoids consecutive duplicates."""
        nav = Navigator(['home', 'about'])
        nav.navigate('about', 'push')
        nav.navigate('home', 'push')
        nav._add_to_history('home')  # Should not create duplicate

        self.assertEqual(nav.get_history(), ['home'])

    def test_history_never_records_none_values(self):
        """Test history never records None values."""
        nav = Navigator(['home', 'about'])
        nav._add_to_history(None)
        nav._add_to_history('about')
        nav._add_to_history(None)

        self.assertEqual(nav.get_history(), ['about'])

    def test_back_via_history(self):
        """Test back navigation via history."""
        nav = Navigator(['home', 'about', 'contact'])
        nav.navigate('about', 'push')
        nav.navigate('contact', 'push')

        self.assertTrue(nav.can_go_back())
        self.assertTrue(nav.back())
        self.assertEqual(nav.current(), 'about')
        self.assertEqual(nav.get_history(), ['home'])

    def test_back_via_fallback_when_history_empty(self):
        """Test back navigation via fallback when history is empty."""
        nav = Navigator(['home', 'about'], {'about': 'home'}, 'about')

        self.assertTrue(nav.can_go_back())
        self.assertTrue(nav.back())
        self.assertEqual(nav.current(), 'home')

    def test_back_with_no_options_available(self):
        """Test back navigation with no options available."""
        nav = Navigator(['home', 'about'], {}, 'home')

        self.assertFalse(nav.can_go_back())
        self.assertFalse(nav.back())
        self.assertEqual(nav.current(), 'home')

    def test_replace_history_with_valid_entries(self):
        """Test replacing history with valid entries."""
        nav = Navigator(['home', 'about', 'contact', 'blog'])
        nav.navigate('blog', 'push')

        nav.replace_history(['about', 'contact'])
        self.assertEqual(nav.get_history(), ['about', 'contact'])

    def test_replace_history_with_depth_capping(self):
        """Test replacing history with depth capping."""
        nav = Navigator(['a', 'b', 'c', 'd', 'e'])
        nav.replace_history(['a', 'b', 'c', 'd'], 2)
        self.assertEqual(nav.get_history(), ['c', 'd'])

    def test_replace_history_removes_active_and_duplicates(self):
        """Test replace history removes active destination and duplicates."""
        nav = Navigator(['home', 'about', 'contact'], {}, 'contact')
        nav.replace_history(['home', 'about', 'contact', 'about'])
        self.assertEqual(nav.get_history(), ['home', 'about'])

    def test_reject_unknown_destinations(self):
        """Test rejection of unknown destinations."""
        nav = Navigator(['home', 'about'])
        with self.assertRaises(ValueError):
            nav.navigate('invalid')

    def test_reject_unknown_destinations_in_history_replacement(self):
        """Test rejection of unknown destinations in history replacement."""
        nav = Navigator(['home', 'about'])
        with self.assertRaises(ValueError):
            nav.replace_history(['invalid'])

    def test_replace_history_validation(self):
        """Test replace_history input validation."""
        nav = Navigator(['home', 'about'])
        with self.assertRaises(ValueError):
            nav.replace_history('not_a_list')

    def test_complex_navigation_scenario(self):
        """Test complex navigation scenario with multiple operations."""
        nav = Navigator(
            ['home', 'about', 'contact', 'blog', 'profile'],
            {'profile': 'home', 'contact': 'about'},
            'home',
        )

        # Build up history
        nav.navigate('about', 'push')
        nav.navigate('contact', 'push')
        nav.navigate('blog', 'push')
        nav.navigate('profile', 'push')

        self.assertEqual(nav.get_history(), ['home', 'about', 'contact', 'blog'])
        self.assertEqual(nav.current(), 'profile')

        # Jump back to 'about'
        nav.navigate('about')
        self.assertEqual(nav.current(), 'about')
        self.assertEqual(nav.get_history(), ['home'])

        # Replace mode navigation
        nav.navigate('contact', 'replace')
        self.assertEqual(nav.current(), 'contact')
        self.assertEqual(nav.get_history(), ['home'])

        # Back via history
        self.assertTrue(nav.back())
        self.assertEqual(nav.current(), 'home')
        self.assertEqual(nav.get_history(), [])

        # Back should now fail (no fallback for home)
        self.assertFalse(nav.back())
        self.assertEqual(nav.current(), 'home')


def run_tests():
    """Run all tests and display results."""
    print('🧪 Running Navigation Component Tests\n')

    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestNavigator)

    # Run tests with custom result handler
    class ColoredTextTestResult(unittest.TextTestResult):
        def addSuccess(self, test):
            super().addSuccess(test)
            print(f'✅ {test._testMethodName}')

        def addError(self, test, err):
            super().addError(test, err)
            print(f'❌ {test._testMethodName}: ERROR')

        def addFailure(self, test, err):
            super().addFailure(test, err)
            print(f'❌ {test._testMethodName}: FAILURE')

    # Run tests
    runner = unittest.TextTestRunner(
        stream=open('/dev/null', 'w'),  # Suppress default output
        resultclass=ColoredTextTestResult,
        verbosity=0,
    )
    result = runner.run(suite)

    # Display summary
    total = result.testsRun
    failed = len(result.failures) + len(result.errors)
    passed = total - failed

    print(f'\n📊 Results: {passed} passed, {failed} failed')

    if failed == 0:
        print('🎉 All tests passed!')
    else:
        print(f'💥 {failed} test(s) failed')
        for test, trace in result.failures + result.errors:
            print(f'   - {test._testMethodName}')


def example_usage():
    """Demonstrate example usage of the Navigator component."""
    print('\n🚀 Example Usage:')

    nav = Navigator(
        ['dashboard', 'profile', 'settings', 'help'],
        {'help': 'dashboard', 'profile': 'dashboard'},
    )

    print(f'Initial: {nav.current()}')  # dashboard
    nav.navigate('profile', 'push')
    print(f'After push to profile: {nav.current()}, history: {nav.get_history()}')
    nav.navigate('settings', 'push')
    print(f'After push to settings: {nav.current()}, history: {nav.get_history()}')
    nav.navigate('profile')  # Jump-back
    print(f'After jump-back to profile: {nav.current()}, history: {nav.get_history()}')
    nav.back()
    print(f'After back: {nav.current()}, history: {nav.get_history()}')


if __name__ == '__main__':
    # Run tests
    run_tests()

    # Show example usage
    example_usage()
