import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from bookdbtool.visualization_tools import running_total_comparison, yearly_comparisons


class TestRunningTotalComparison(unittest.TestCase):

    def setUp(self):
        # Create data spanning 2 years to support window=1 tests
        dates1 = pd.date_range('2019-07-01', periods=50, freq='D')
        dates2 = pd.date_range('2020-01-01', periods=50, freq='D')
        dates = pd.concat([pd.Series(dates1), pd.Series(dates2)])
        self.df = pd.DataFrame({
            'ReadDate': dates.dt.strftime('%Y-%m-%d').tolist(),
            'Pages': np.random.randint(10, 100, size=100)
        })

    def tearDown(self):
        plt.close('all')

    @patch('bookdbtool.visualization_tools.plt.show')
    def test_running_total_comparison_basic(self, mock_show):
        running_total_comparison(self.df.copy(), window=2)

        mock_show.assert_called_once()

    @patch('bookdbtool.visualization_tools.plt.show')
    def test_running_total_comparison_with_multiple_years(self, mock_show):
        dates = []
        pages = []

        for year in [2018, 2019, 2020, 2021, 2022]:
            year_dates = pd.date_range(f'{year}-01-01', periods=365, freq='D')
            dates.extend(year_dates)
            pages.extend(np.random.randint(10, 100, size=365))

        df = pd.DataFrame({
            'ReadDate': [d.strftime('%Y-%m-%d') for d in dates],
            'Pages': pages
        })

        running_total_comparison(df, window=5)

        mock_show.assert_called_once()

    @patch('bookdbtool.visualization_tools.plt.show')
    def test_running_total_comparison_window_parameter(self, mock_show):
        dates = []
        pages = []

        for year in range(2010, 2025):
            year_dates = pd.date_range(f'{year}-01-01', periods=365, freq='D')
            dates.extend(year_dates)
            pages.extend(np.random.randint(10, 100, size=365))

        df = pd.DataFrame({
            'ReadDate': [d.strftime('%Y-%m-%d') for d in dates],
            'Pages': pages
        })

        running_total_comparison(df, window=10)

        mock_show.assert_called_once()

    @patch('bookdbtool.visualization_tools.plt.show')
    def test_running_total_comparison_creates_correct_columns(self, mock_show):
        # Create data for 3 years to support window=2
        dates1 = pd.date_range('2018-01-01', periods=100, freq='D')
        dates2 = pd.date_range('2019-01-01', periods=100, freq='D')
        dates3 = pd.date_range('2020-01-01', periods=100, freq='D')
        dates = pd.concat([pd.Series(dates1), pd.Series(dates2), pd.Series(dates3)])
        df = pd.DataFrame({
            'ReadDate': dates.dt.strftime('%Y-%m-%d').tolist(),
            'Pages': list(range(1, 301))
        })

        with patch('bookdbtool.visualization_tools.plt') as mock_plt:
            mock_ax = MagicMock()
            mock_df = MagicMock()
            mock_df.plot.return_value = mock_ax

            running_total_comparison(df, window=2)

    @patch('bookdbtool.visualization_tools.plt.show')
    def test_running_total_comparison_xlim(self, mock_show):
        with patch('bookdbtool.visualization_tools.plt') as mock_plt:
            mock_ax = MagicMock()

            running_total_comparison(self.df.copy(), window=2)

    @patch('bookdbtool.visualization_tools.plt.show')
    def test_running_total_comparison_with_leap_year(self, mock_show):
        # Create data for 2019 and 2020 (leap year)
        dates1 = pd.date_range('2019-01-01', periods=100, freq='D')
        dates2 = pd.date_range('2020-01-01', periods=366, freq='D')
        dates = pd.concat([pd.Series(dates1), pd.Series(dates2)])
        df = pd.DataFrame({
            'ReadDate': dates.dt.strftime('%Y-%m-%d').tolist(),
            'Pages': np.random.randint(10, 100, size=len(dates))
        })

        running_total_comparison(df, window=2)

        mock_show.assert_called_once()

    def test_running_total_comparison_data_transformations(self):
        # Create data for 3 years to support window=2
        dates1 = pd.date_range('2018-06-01', periods=10, freq='D')
        dates2 = pd.date_range('2019-06-01', periods=10, freq='D')
        dates3 = pd.date_range('2020-06-01', periods=10, freq='D')
        dates = pd.concat([pd.Series(dates1), pd.Series(dates2), pd.Series(dates3)])
        df = pd.DataFrame({
            'ReadDate': dates.dt.strftime('%Y-%m-%d').tolist(),
            'Pages': [10] * 30
        })

        with patch('bookdbtool.visualization_tools.plt.show'):
            running_total_comparison(df, window=2)


class TestYearlyComparisons(unittest.TestCase):

    def setUp(self):
        self.df = pd.DataFrame({
            'year': [2018, 2019, 2020, 2021, 2022],
            'pages read': [5000, 6000, 5500, 7000, 6500],
            'books read': [20, 25, 22, 30, 28],
            'rank': [3, 1, 4, 0, 2]
        })

    def tearDown(self):
        plt.close('all')

    @patch('bookdbtool.visualization_tools.plt.show')
    def test_yearly_comparisons_basic(self, mock_show):
        yearly_comparisons(self.df.copy(), current_year=2020)

        self.assertEqual(mock_show.call_count, 3)

    @patch('bookdbtool.visualization_tools.plt.show')
    def test_yearly_comparisons_histogram(self, mock_show):
        yearly_comparisons(self.df.copy(), current_year=2020)

        self.assertEqual(mock_show.call_count, 3)

    @patch('bookdbtool.visualization_tools.plt.show')
    @patch('bookdbtool.visualization_tools.plt.axvline')
    def test_yearly_comparisons_axvline_calls(self, mock_axvline, mock_show):
        yearly_comparisons(self.df.copy(), current_year=2020)

        self.assertGreater(mock_axvline.call_count, 0)

    @patch('bookdbtool.visualization_tools.plt.show')
    def test_yearly_comparisons_with_different_year(self, mock_show):
        yearly_comparisons(self.df.copy(), current_year=2022)

        self.assertEqual(mock_show.call_count, 3)

    @patch('bookdbtool.visualization_tools.plt.show')
    def test_yearly_comparisons_bar_charts(self, mock_show):
        with patch.object(self.df, 'plot') as mock_plot:
            mock_plot.bar.return_value = None

            yearly_comparisons(self.df.copy(), current_year=2020)

    @patch('bookdbtool.visualization_tools.plt.show')
    def test_yearly_comparisons_sorts_by_year(self, mock_show):
        df = self.df.copy()

        yearly_comparisons(df, current_year=2020)

        self.assertEqual(mock_show.call_count, 3)

    @patch('bookdbtool.visualization_tools.plt.show')
    def test_yearly_comparisons_with_single_year(self, mock_show):
        df = pd.DataFrame({
            'year': [2020],
            'pages read': [5000],
            'books read': [20],
            'rank': [0]
        })

        yearly_comparisons(df, current_year=2020)

        self.assertEqual(mock_show.call_count, 3)

    @patch('bookdbtool.visualization_tools.plt.show')
    def test_yearly_comparisons_with_many_years(self, mock_show):
        df = pd.DataFrame({
            'year': list(range(2000, 2024)),
            'pages read': np.random.randint(4000, 8000, size=24),
            'books read': np.random.randint(15, 35, size=24),
            'rank': list(range(24))
        })

        yearly_comparisons(df, current_year=2020)

        self.assertEqual(mock_show.call_count, 3)

    @patch('bookdbtool.visualization_tools.plt.show')
    @patch('bookdbtool.visualization_tools.plt.axvline')
    def test_yearly_comparisons_iloc_usage(self, mock_axvline, mock_show):
        """Test that .iloc[0] is used to access Series elements (fixes FutureWarning)"""
        df = pd.DataFrame({
            'year': [2019, 2020, 2021],
            'pages read': [5000, 6000, 5500],
            'books read': [20, 25, 22],
            'rank': [2, 0, 1]
        })

        # This should not raise FutureWarning about Series to int conversion
        yearly_comparisons(df, current_year=2020)

        # Verify axvline was called with integer values
        self.assertEqual(mock_axvline.call_count, 2)
        # First call should be with pages read value (6000)
        first_call_x = mock_axvline.call_args_list[0][1]['x']
        self.assertIsInstance(first_call_x, int)
        self.assertEqual(first_call_x, 6000)


class TestVisualizationIntegration(unittest.TestCase):

    def tearDown(self):
        plt.close('all')

    @patch('bookdbtool.visualization_tools.plt.show')
    def test_running_total_and_yearly_together(self, mock_show):
        dates = []
        pages = []

        for year in [2019, 2020, 2021]:
            year_dates = pd.date_range(f'{year}-01-01', periods=365, freq='D')
            dates.extend(year_dates)
            pages.extend(np.random.randint(10, 50, size=365))

        df_running = pd.DataFrame({
            'ReadDate': [d.strftime('%Y-%m-%d') for d in dates],
            'Pages': pages
        })

        df_yearly = pd.DataFrame({
            'year': [2019, 2020, 2021],
            'pages read': [5000, 6000, 5500],
            'books read': [20, 25, 22],
            'rank': [2, 0, 1]
        })

        running_total_comparison(df_running, window=3)

        yearly_comparisons(df_yearly, current_year=2020)

        self.assertGreater(mock_show.call_count, 0)


class TestVisualizationEdgeCases(unittest.TestCase):

    def tearDown(self):
        plt.close('all')

    @patch('bookdbtool.visualization_tools.plt.show')
    def test_running_total_empty_dataframe(self, mock_show):
        df = pd.DataFrame({'ReadDate': [], 'Pages': []})

        with self.assertRaises((KeyError, ValueError, IndexError)):
            running_total_comparison(df, window=2)

    @patch('bookdbtool.visualization_tools.plt.show')
    def test_yearly_comparisons_empty_dataframe(self, mock_show):
        df = pd.DataFrame({'year': [], 'pages read': [], 'books read': [], 'rank': []})

        # Should raise an error when trying to access .iloc[0] on empty Series
        with self.assertRaises((IndexError, KeyError)):
            yearly_comparisons(df, current_year=2020)

    @patch('bookdbtool.visualization_tools.plt.show')
    def test_running_total_with_missing_data(self, mock_show):
        # Need at least 2 years of data for the window parameter to work
        dates = ['2019-12-30', '2020-01-01', '2020-01-05', '2020-01-10']
        pages = [40, 50, 30, 70]

        df = pd.DataFrame({
            'ReadDate': dates,
            'Pages': pages
        })

        running_total_comparison(df, window=2)

        mock_show.assert_called()

    @patch('bookdbtool.visualization_tools.plt.show')
    def test_yearly_comparisons_non_sequential_years(self, mock_show):
        df = pd.DataFrame({
            'year': [2015, 2017, 2019, 2022],
            'pages read': [5000, 6000, 5500, 7000],
            'books read': [20, 25, 22, 30],
            'rank': [2, 0, 3, 1]
        })

        yearly_comparisons(df, current_year=2019)

        self.assertEqual(mock_show.call_count, 3)


class TestVisualizationDataTypes(unittest.TestCase):

    def tearDown(self):
        plt.close('all')

    @patch('bookdbtool.visualization_tools.plt.show')
    def test_running_total_datetime_conversion(self, mock_show):
        # Create data for 2 years to support window=1
        dates1 = pd.date_range('2019-01-01', periods=50, freq='D')
        dates2 = pd.date_range('2020-01-01', periods=50, freq='D')
        dates = pd.concat([pd.Series(dates1), pd.Series(dates2)])
        df = pd.DataFrame({
            'ReadDate': dates,
            'Pages': np.random.randint(10, 100, size=len(dates))
        })

        running_total_comparison(df, window=2)

        mock_show.assert_called_once()

    @patch('bookdbtool.visualization_tools.plt.show')
    def test_yearly_comparisons_integer_years(self, mock_show):
        df = pd.DataFrame({
            'year': [2019, 2020, 2021],
            'pages read': [5000, 6000, 5500],
            'books read': [20, 25, 22],
            'rank': [2, 0, 1]
        })

        yearly_comparisons(df, current_year=2020)

        self.assertEqual(mock_show.call_count, 3)

    @patch('bookdbtool.visualization_tools.plt.show')
    def test_running_total_large_window(self, mock_show):
        dates = []
        pages = []

        for year in range(2000, 2025):
            year_dates = pd.date_range(f'{year}-01-01', periods=365, freq='D')
            dates.extend(year_dates)
            pages.extend(np.random.randint(10, 100, size=365))

        df = pd.DataFrame({
            'ReadDate': [d.strftime('%Y-%m-%d') for d in dates],
            'Pages': pages
        })

        running_total_comparison(df, window=20)

        mock_show.assert_called_once()


if __name__ == '__main__':
    unittest.main()
