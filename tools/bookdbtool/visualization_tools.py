"""
Visualization Tools - Charts and graphs for reading statistics.

These functions create matplotlib visualizations for analyzing reading patterns.
They work with DataFrames from the BCTool methods.
"""

import pandas as pd
import matplotlib.pyplot as plt


def running_total_comparison(df1, window=15):
    """
    Plot cumulative pages read by day-of-year for multiple years.

    Creates a line chart comparing reading progress across years, showing
    how many total pages were read by each day of the year. The current
    year is highlighted with a thicker line.

    Args:
        df1: DataFrame from bc.bry() containing ReadDate and Pages columns.
        window: Number of recent years to display (default 15).

    Example:
        >>> bc.bry()  # Get all books read
        >>> from bookdbtool.visualization_tools import running_total_comparison
        >>> running_total_comparison(bc.result, window=10)
    """
    df1["read_date"] = pd.to_datetime(df1["ReadDate"])
    df1 = df1.set_index("ReadDate")
    df1.index = pd.to_datetime(df1.index)
    ds_pages = df1.groupby(df1.index.to_period('Y'))["Pages"].cumsum()
    ds_day = df1.read_date.apply(lambda x: x.dayofyear)
    ds_year = df1.read_date.apply(lambda x: x.year)
    df1 = pd.concat([ds_pages, ds_day, ds_year], axis=1)
    df1.columns = ["Pages", "Day", "Year"]
    fig_size = [12, 12]
    xlim = [0, 365]
    ylim = [0, max(df1.Pages)]
    years = df1.Year.unique()[-window:].tolist()
    y = years.pop(0)
    this_year = max(years)
    _df = df1.loc[df1.Year == y]
    ax = _df.plot("Day", "Pages", figsize=fig_size, xlim=xlim, ylim=ylim, label=y)
    for y in years:
        _df = df1.loc[df1.Year == y]
        lw = 3 if y == this_year else 1
        ax = _df.plot("Day", "Pages", figsize=fig_size, xlim=xlim, ylim=ylim, ax=ax, label=y, lw=lw)
    plt.show()


def yearly_comparisons(df, current_year=2020):
    """
    Display multiple charts comparing yearly reading statistics.

    Creates three visualizations:
        1. Histogram of pages read per year (with current year marked)
        2. Bar chart of pages by rank (best year first)
        3. Bar chart of pages by year chronologically

    Args:
        df: DataFrame from bc.sbry() with columns: year, pages read, rank.
            Must include a 'rank' column (add with df["rank"] = df["pages read"].rank()).
        current_year: Year to highlight in red on the charts.

    Example:
        >>> bc.sbry()  # Get summary data
        >>> df = bc.result.copy()
        >>> df["rank"] = df["pages read"].rank(ascending=False)
        >>> from bookdbtool.visualization_tools import yearly_comparisons
        >>> yearly_comparisons(df, current_year=2024)
    """
    now = df.loc[df.year == current_year]
    fig_size = [12, 6]
    ax = df.hist("pages read", bins=14, color="darkblue", figsize=fig_size)
    plt.axvline(x=int(now["pages read"].iloc[0]), color="red")
    plt.show()
    df.plot.bar(x="rank", y="pages read", width=.95, color="darkblue", figsize=fig_size)
    plt.axvline(x=int(now["rank"].iloc[0]) - 1, color="red")
    plt.show()
    df.sort_values("year").plot.bar(x="year", y="pages read", width=.95, color="darkblue", figsize=fig_size)
    plt.show()
