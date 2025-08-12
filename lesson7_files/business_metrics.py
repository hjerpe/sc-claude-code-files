"""
Business metrics calculation module for e-commerce analysis.

This module provides functions to calculate key business metrics such as revenue,
growth rates, customer metrics, and performance indicators for configurable time periods.
"""

import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any, Optional


def calculate_revenue_metrics(sales_data: pd.DataFrame, target_year: int, comparison_year: int) -> Dict[str, float]:
    """
    Calculate revenue metrics comparing target year to comparison year.
    
    Args:
        sales_data: DataFrame with sales data including 'price', 'purchase_year' columns
        target_year: Year to analyze (e.g., 2023)
        comparison_year: Year to compare against (e.g., 2022)
    
    Returns:
        Dictionary containing revenue metrics:
        - total_revenue_target: Total revenue for target year
        - total_revenue_comparison: Total revenue for comparison year
        - revenue_growth_rate: Revenue growth rate (decimal)
        - revenue_growth_percentage: Revenue growth rate (percentage)
    """
    target_data = sales_data[sales_data['purchase_year'] == target_year]
    comparison_data = sales_data[sales_data['purchase_year'] == comparison_year]
    
    total_revenue_target = target_data['price'].sum()
    total_revenue_comparison = comparison_data['price'].sum()
    
    if total_revenue_comparison > 0:
        revenue_growth_rate = (total_revenue_target - total_revenue_comparison) / total_revenue_comparison
    else:
        revenue_growth_rate = 0.0
    
    return {
        'total_revenue_target': total_revenue_target,
        'total_revenue_comparison': total_revenue_comparison,
        'revenue_growth_rate': revenue_growth_rate,
        'revenue_growth_percentage': revenue_growth_rate * 100
    }


def calculate_monthly_growth(sales_data: pd.DataFrame, year: int) -> pd.Series:
    """
    Calculate month-over-month growth rate for a specific year.
    
    Args:
        sales_data: DataFrame with sales data including 'price', 'purchase_month', 'purchase_year' columns
        year: Year to analyze
    
    Returns:
        Series with monthly growth rates
    """
    year_data = sales_data[sales_data['purchase_year'] == year]
    monthly_revenue = year_data.groupby('purchase_month')['price'].sum()
    monthly_growth = monthly_revenue.pct_change()
    
    return monthly_growth


def calculate_average_monthly_growth(sales_data: pd.DataFrame, year: int) -> float:
    """
    Calculate average monthly growth rate for a specific year.
    
    Args:
        sales_data: DataFrame with sales data including 'price', 'purchase_month', 'purchase_year' columns
        year: Year to analyze
    
    Returns:
        Average monthly growth rate as percentage
    """
    monthly_growth = calculate_monthly_growth(sales_data, year)
    avg_growth = monthly_growth.mean()
    
    return avg_growth * 100


def calculate_order_metrics(sales_data: pd.DataFrame, target_year: int, comparison_year: int) -> Dict[str, Any]:
    """
    Calculate order-related metrics comparing target year to comparison year.
    
    Args:
        sales_data: DataFrame with sales data including 'order_id', 'price', 'purchase_year' columns
        target_year: Year to analyze
        comparison_year: Year to compare against
    
    Returns:
        Dictionary containing order metrics:
        - avg_order_value_target: Average order value for target year
        - avg_order_value_comparison: Average order value for comparison year
        - total_orders_target: Total number of orders for target year
        - total_orders_comparison: Total number of orders for comparison year
        - aov_growth_percentage: Average order value growth percentage
        - orders_growth_percentage: Orders count growth percentage
    """
    target_data = sales_data[sales_data['purchase_year'] == target_year]
    comparison_data = sales_data[sales_data['purchase_year'] == comparison_year]
    
    avg_order_value_target = target_data.groupby('order_id')['price'].sum().mean()
    avg_order_value_comparison = comparison_data.groupby('order_id')['price'].sum().mean()
    
    total_orders_target = target_data['order_id'].nunique()
    total_orders_comparison = comparison_data['order_id'].nunique()
    
    aov_growth_percentage = ((avg_order_value_target - avg_order_value_comparison) / avg_order_value_comparison) * 100 if avg_order_value_comparison > 0 else 0
    orders_growth_percentage = ((total_orders_target - total_orders_comparison) / total_orders_comparison) * 100 if total_orders_comparison > 0 else 0
    
    return {
        'avg_order_value_target': avg_order_value_target,
        'avg_order_value_comparison': avg_order_value_comparison,
        'total_orders_target': total_orders_target,
        'total_orders_comparison': total_orders_comparison,
        'aov_growth_percentage': aov_growth_percentage,
        'orders_growth_percentage': orders_growth_percentage
    }


def calculate_product_category_sales(sales_data: pd.DataFrame, products_data: pd.DataFrame, year: int) -> pd.DataFrame:
    """
    Calculate sales by product category for a specific year.
    
    Args:
        sales_data: DataFrame with sales data including 'product_id', 'price', 'purchase_year' columns
        products_data: DataFrame with product data including 'product_id', 'product_category_name' columns
        year: Year to analyze
    
    Returns:
        DataFrame with category sales sorted by revenue (descending)
    """
    year_data = sales_data[sales_data['purchase_year'] == year]
    sales_categories = pd.merge(
        products_data[['product_id', 'product_category_name']],
        year_data[['product_id', 'price']],
        on='product_id'
    )
    
    category_sales = sales_categories.groupby('product_category_name')['price'].sum().sort_values(ascending=False)
    
    return category_sales.reset_index()


def calculate_geographic_sales(sales_data: pd.DataFrame, orders_data: pd.DataFrame, 
                             customers_data: pd.DataFrame, year: int) -> pd.DataFrame:
    """
    Calculate sales by geographic region (state) for a specific year.
    
    Args:
        sales_data: DataFrame with sales data including 'order_id', 'price', 'purchase_year' columns
        orders_data: DataFrame with order data including 'order_id', 'customer_id' columns
        customers_data: DataFrame with customer data including 'customer_id', 'customer_state' columns
        year: Year to analyze
    
    Returns:
        DataFrame with state sales sorted by revenue (descending)
    """
    year_data = sales_data[sales_data['purchase_year'] == year]
    
    sales_customers = pd.merge(
        year_data[['order_id', 'price']],
        orders_data[['order_id', 'customer_id']],
        on='order_id'
    )
    
    sales_states = pd.merge(
        sales_customers,
        customers_data[['customer_id', 'customer_state']],
        on='customer_id'
    )
    
    state_sales = sales_states.groupby('customer_state')['price'].sum().sort_values(ascending=False)
    
    return state_sales.reset_index()


def categorize_delivery_speed(days: int) -> str:
    """
    Categorize delivery speed into business-relevant groups.
    
    Args:
        days: Number of delivery days
    
    Returns:
        Delivery speed category
    """
    if days <= 3:
        return '1-3 days'
    elif days <= 7:
        return '4-7 days'
    else:
        return '8+ days'


def calculate_delivery_performance(sales_data: pd.DataFrame, reviews_data: pd.DataFrame, year: int) -> Dict[str, Any]:
    """
    Calculate delivery performance metrics including average delivery time and review scores.
    
    Args:
        sales_data: DataFrame with sales data including order timestamps and delivery dates
        reviews_data: DataFrame with review data including 'order_id', 'review_score' columns
        year: Year to analyze
    
    Returns:
        Dictionary containing delivery performance metrics:
        - avg_delivery_days: Average delivery time in days
        - avg_review_score: Average review score
        - delivery_categories_performance: Review scores by delivery speed categories
    """
    year_data = sales_data[sales_data['purchase_year'] == year].copy()
    
    # Check if we already have review_score (from data loading), if so use it directly
    if 'review_score' in year_data.columns and 'delivery_days' in year_data.columns:
        # Use the data already processed by data_loader
        review_speed = year_data[['order_id', 'delivery_days', 'review_score']].dropna().drop_duplicates()
        review_speed = review_speed.rename(columns={'delivery_days': 'delivery_speed'})
    else:
        # Calculate delivery speed and merge with reviews
        year_data['order_purchase_timestamp'] = pd.to_datetime(year_data['order_purchase_timestamp'])
        year_data['order_delivered_customer_date'] = pd.to_datetime(year_data['order_delivered_customer_date'])
        
        year_data['delivery_speed'] = (
            year_data['order_delivered_customer_date'] - year_data['order_purchase_timestamp']
        ).dt.days
        
        # Merge with reviews data, handle potential column name conflicts
        sales_with_reviews = pd.merge(
            year_data[['order_id', 'delivery_speed']], 
            reviews_data[['order_id', 'review_score']], 
            on='order_id', 
            how='inner'
        )
        
        review_speed = sales_with_reviews[['order_id', 'delivery_speed', 'review_score']].drop_duplicates()
    
    avg_delivery_days = review_speed['delivery_speed'].mean()
    avg_review_score = review_speed['review_score'].mean()
    
    review_speed['delivery_category'] = review_speed['delivery_speed'].apply(categorize_delivery_speed)
    delivery_categories_performance = review_speed.groupby('delivery_category')['review_score'].mean()
    
    return {
        'avg_delivery_days': avg_delivery_days,
        'avg_review_score': avg_review_score,
        'delivery_categories_performance': delivery_categories_performance.to_dict()
    }


def calculate_order_status_distribution(orders_data: pd.DataFrame, year: int) -> pd.Series:
    """
    Calculate order status distribution for a specific year.
    
    Args:
        orders_data: DataFrame with order data including 'order_status', 'purchase_year' columns
        year: Year to analyze
    
    Returns:
        Series with normalized order status distribution
    """
    year_orders = orders_data[orders_data['purchase_year'] == year]
    status_distribution = year_orders['order_status'].value_counts(normalize=True)
    
    return status_distribution


def get_monthly_revenue_trend(sales_data: pd.DataFrame, year: int) -> pd.DataFrame:
    """
    Get monthly revenue trend data for visualization.
    
    Args:
        sales_data: DataFrame with sales data including 'price', 'purchase_month', 'purchase_year' columns
        year: Year to analyze
    
    Returns:
        DataFrame with monthly revenue data
    """
    year_data = sales_data[sales_data['purchase_year'] == year]
    monthly_revenue = year_data.groupby(['purchase_year', 'purchase_month'])['price'].sum().reset_index()
    monthly_revenue.columns = ['year', 'month', 'price']
    
    return monthly_revenue


def filter_sales_data_by_period(sales_data: pd.DataFrame, year: int, month: Optional[int] = None) -> pd.DataFrame:
    """
    Filter sales data by year and optionally by month.
    
    Args:
        sales_data: DataFrame with sales data
        year: Year to filter by
        month: Optional month to filter by (1-12)
    
    Returns:
        Filtered DataFrame
    """
    filtered_data = sales_data[sales_data['purchase_year'] == year]
    
    if month is not None:
        filtered_data = filtered_data[filtered_data['purchase_month'] == month]
    
    return filtered_data


