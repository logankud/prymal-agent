from smolagents import tool
import pandas as pd

class Metrics:
    def unique_count(self, df: pd.DataFrame, field: str) -> int:
        return df[field].nunique()

    def total_count(self, df: pd.DataFrame, field: str) -> int:
        return df[field].count()

    def sum_field(self, df: pd.DataFrame, field: str) -> float:
        return df[field].sum()

    def mean_field(self, df: pd.DataFrame, field: str) -> float:
        return df[field].mean()

    def top_values(self, df: pd.DataFrame, field: str, top_n: int = 5) -> pd.Series:
        return df[field].value_counts().head(top_n)

    def group_sum(self, df: pd.DataFrame, group_field: str, sum_field: str) -> pd.Series:
        return df.groupby(group_field)[sum_field].sum()

    def group_mean(self, df: pd.DataFrame, group_field: str, mean_field: str) -> pd.Series:
        return df.groupby(group_field)[mean_field].mean()

    def group_count(self, df: pd.DataFrame, group_field: str) -> pd.Series:
        return df[group_field].value_counts()

    def average_order_value(self, df: pd.DataFrame, total_field: str, order_id_field: str) -> float:
        grouped = df.groupby(order_id_field)[total_field].sum()
        return grouped.mean()

    def percent_missing(self, df: pd.DataFrame, field: str) -> float:
        return df[field].isnull().mean() * 100

# Instantiate
metrics = Metrics()

@tool
def unique_count(df: pd.DataFrame, field: str) -> int:
    """Return the number of unique values in a specified field.

    Args:
        df: The dataframe containing the data.
        field: The name of the column to count unique values for.

    Returns:
        The count of unique values.
    """
    return metrics.unique_count(df, field)

@tool
def total_count(df: pd.DataFrame, field: str) -> int:
    """Return the total number of non-null entries in a field.

    Args:
        df: The dataframe containing the data.
        field: The name of the column to count entries in.

    Returns:
        The total count of entries.
    """
    return metrics.total_count(df, field)

@tool
def sum_field(df: pd.DataFrame, field: str) -> float:
    """Calculate the sum of a specified field.

    Args:
        df: The dataframe containing the data.
        field: The name of the column to sum.

    Returns:
        The sum of the field values.
    """
    return metrics.sum_field(df, field)

@tool
def mean_field(df: pd.DataFrame, field: str) -> float:
    """Calculate the mean of a specified field.

    Args:
        df: The dataframe containing the data.
        field: The name of the column to average.

    Returns:
        The mean value.
    """
    return metrics.mean_field(df, field)

@tool
def top_values(df: pd.DataFrame, field: str, top_n: int = 5) -> pd.Series:
    """Return the top N most frequent values in a field.

    Args:
        df: The dataframe containing the data.
        field: The column to analyze.
        top_n: Number of top values to return.

    Returns:
        A series of the most frequent values.
    """
    return metrics.top_values(df, field, top_n)

@tool
def group_sum(df: pd.DataFrame, group_field: str, sum_field: str) -> pd.Series:
    """Group by one field and calculate the sum of another.

    Args:
        df: The dataframe containing the data.
        group_field: The column to group by.
        sum_field: The column to sum.

    Returns:
        A series with summed values per group.
    """
    return metrics.group_sum(df, group_field, sum_field)

@tool
def group_mean(df: pd.DataFrame, group_field: str, mean_field: str) -> pd.Series:
    """Group by one field and calculate the mean of another.

    Args:
        df: The dataframe containing the data.
        group_field: The column to group by.
        mean_field: The column to average.

    Returns:
        A series with mean values per group.
    """
    return metrics.group_mean(df, group_field, mean_field)

@tool
def group_count(df: pd.DataFrame, group_field: str) -> pd.Series:
    """Count the number of entries per group in a column.

    Args:
        df: The dataframe containing the data.
        group_field: The column to group and count.

    Returns:
        A series with counts per unique value.
    """
    return metrics.group_count(df, group_field)

@tool
def average_order_value(df: pd.DataFrame, total_field: str, order_id_field: str) -> float:
    """Calculate average order value by summing per order and averaging.

    Args:
        df: The dataframe containing order data.
        total_field: The column with item totals or prices.
        order_id_field: The column with order IDs.

    Returns:
        The average order value.
    """
    return metrics.average_order_value(df, total_field, order_id_field)

@tool
def percent_missing(df: pd.DataFrame, field: str) -> float:
    """Calculate the percent of missing (null) values in a field.

    Args:
        df: The dataframe containing the data.
        field: The column to inspect for null values.

    Returns:
        The percentage of missing values.
    """
    return metrics.percent_missing(df, field)
