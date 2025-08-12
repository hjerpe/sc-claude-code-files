"""
E-commerce Business Analytics Dashboard
A professional Streamlit dashboard based on the EDA analysis
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import warnings

# Import custom modules
from data_loader import EcommerceDataLoader, load_and_process_data
from business_metrics import (
    calculate_revenue_metrics, calculate_monthly_growth, calculate_order_metrics,
    calculate_product_category_sales, calculate_geographic_sales,
    calculate_delivery_performance, get_monthly_revenue_trend
)

warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="E-commerce Analytics Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f1f1f;
        margin-bottom: 0rem;
    }
    
    .kpi-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #e1e5e9;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        height: 160px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .kpi-value {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f1f1f;
        margin-bottom: 0.5rem;
    }
    
    .kpi-label {
        font-size: 0.9rem;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .trend-indicator {
        font-size: 0.9rem;
        font-weight: bold;
        margin-top: 0.5rem;
    }
    
    .trend-positive { color: #28a745; }
    .trend-negative { color: #dc3545; }
    
    .bottom-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #e1e5e9;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        height: 180px;
        text-align: center;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .bottom-card-value {
        font-size: 3rem;
        font-weight: bold;
        color: #1f1f1f;
        margin-bottom: 0.5rem;
    }
    
    .bottom-card-subtitle {
        font-size: 1rem;
        color: #666;
        margin-bottom: 1rem;
    }
    
    .stars {
        color: #ffd700;
        font-size: 2rem;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """Load and cache the data"""
    try:
        loader, processed_data = load_and_process_data('ecommerce_data/')
        return loader, processed_data
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None, None

@st.cache_data
def get_filtered_data(_loader, start_date, end_date):
    """Get filtered data based on date range"""
    if _loader is None:
        return None
    
    # Create sales dataset for the entire date range
    sales_data = _loader.create_sales_dataset(status_filter='delivered')
    
    # Convert timestamp to datetime if it's not already
    if 'order_purchase_timestamp' in sales_data.columns:
        sales_data['order_purchase_timestamp'] = pd.to_datetime(sales_data['order_purchase_timestamp'])
        
        # Filter by date range
        mask = (sales_data['order_purchase_timestamp'].dt.date >= start_date) & \
               (sales_data['order_purchase_timestamp'].dt.date <= end_date)
        sales_data = sales_data[mask]
    
    return sales_data

def format_currency(value, suffix=''):
    """Format currency values for display"""
    if value >= 1_000_000:
        return f"${value/1_000_000:.1f}M{suffix}"
    elif value >= 1_000:
        return f"${value/1_000:.0f}K{suffix}"
    else:
        return f"${value:.0f}{suffix}"

def get_trend_arrow(trend_value):
    """Get trend arrow and color class"""
    if trend_value > 0:
        return "↗", "trend-positive"
    elif trend_value < 0:
        return "↘", "trend-negative"
    else:
        return "→", ""

def main():
    # Load data
    loader, processed_data = load_data()
    
    if loader is None:
        st.error("Failed to load data. Please check your data files.")
        return
    
    # Header section
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown('<div class="main-header">E-commerce Analytics Dashboard</div>', unsafe_allow_html=True)
    
    with col2:
        # Date range filter
        end_date = date(2023, 12, 31)  # Based on the data
        start_date = date(2023, 1, 1)
        
        selected_dates = st.date_input(
            "Select Date Range",
            value=(start_date, end_date),
            min_value=date(2021, 1, 1),
            max_value=date(2024, 12, 31),
            key="date_range"
        )
        
        if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
            start_date, end_date = selected_dates
        else:
            start_date = end_date = selected_dates if isinstance(selected_dates, date) else end_date
    
    # Get filtered data
    sales_data = get_filtered_data(loader, start_date, end_date)
    
    if sales_data is None or len(sales_data) == 0:
        st.warning("No data available for the selected date range.")
        return
    
    # Calculate metrics for current period
    current_year = end_date.year
    previous_year = current_year - 1
    
    # Create comparison data if available
    comparison_data = None
    if 'order_purchase_timestamp' in sales_data.columns:
        all_data = loader.create_sales_dataset(status_filter='delivered')
        all_data['order_purchase_timestamp'] = pd.to_datetime(all_data['order_purchase_timestamp'])
        comparison_data = all_data[all_data['purchase_year'].isin([current_year, previous_year])]
    
    # Calculate metrics
    if comparison_data is not None and len(comparison_data) > 0:
        revenue_metrics = calculate_revenue_metrics(comparison_data, current_year, previous_year)
        order_metrics = calculate_order_metrics(comparison_data, current_year, previous_year)
        delivery_metrics = calculate_delivery_performance(sales_data, loader.raw_data.get('reviews', pd.DataFrame()), current_year)
    else:
        # Fallback calculations for current period only
        revenue_metrics = {'total_revenue_target': sales_data['price'].sum(), 'revenue_growth_percentage': 0}
        order_metrics = {
            'total_orders_target': sales_data['order_id'].nunique(),
            'avg_order_value_target': sales_data.groupby('order_id')['price'].sum().mean(),
            'orders_growth_percentage': 0,
            'aov_growth_percentage': 0
        }
        delivery_metrics = {'avg_delivery_days': sales_data.get('delivery_days', pd.Series([0])).mean(), 'avg_review_score': sales_data.get('review_score', pd.Series([0])).mean()}
    
    # KPI Row - 4 cards with trend indicators
    st.markdown("### Key Performance Indicators")
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    
    with kpi_col1:
        revenue_trend = revenue_metrics.get('revenue_growth_percentage', 0)
        arrow, trend_class = get_trend_arrow(revenue_trend)
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{format_currency(revenue_metrics.get('total_revenue_target', 0))}</div>
            <div class="kpi-label">Total Revenue</div>
            <div class="trend-indicator {trend_class}">{arrow} {revenue_trend:.2f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi_col2:
        # Calculate monthly growth from current data
        monthly_growth = 0
        if len(sales_data) > 0 and 'purchase_month' in sales_data.columns:
            monthly_revenue = sales_data.groupby('purchase_month')['price'].sum()
            if len(monthly_revenue) > 1:
                monthly_growth = monthly_revenue.pct_change().mean() * 100
        
        arrow, trend_class = get_trend_arrow(monthly_growth)
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{monthly_growth:.2f}%</div>
            <div class="kpi-label">Monthly Growth</div>
            <div class="trend-indicator {trend_class}">{arrow} {monthly_growth:.2f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi_col3:
        aov_trend = order_metrics.get('aov_growth_percentage', 0)
        arrow, trend_class = get_trend_arrow(aov_trend)
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{format_currency(order_metrics.get('avg_order_value_target', 0))}</div>
            <div class="kpi-label">Average Order Value</div>
            <div class="trend-indicator {trend_class}">{arrow} {aov_trend:.2f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi_col4:
        orders_trend = order_metrics.get('orders_growth_percentage', 0)
        arrow, trend_class = get_trend_arrow(orders_trend)
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{order_metrics.get('total_orders_target', 0):,}</div>
            <div class="kpi-label">Total Orders</div>
            <div class="trend-indicator {trend_class}">{arrow} {orders_trend:.2f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Charts Grid - 2x2 layout
    st.markdown("### Performance Analytics")
    
    chart_row1_col1, chart_row1_col2 = st.columns(2)
    
    # Chart 1: Revenue trend line chart
    with chart_row1_col1:
        if comparison_data is not None and len(comparison_data) > 0:
            # Current period trend
            current_trend = get_monthly_revenue_trend(comparison_data, current_year)
            # Previous period trend
            previous_trend = get_monthly_revenue_trend(comparison_data, previous_year)
            
            fig = go.Figure()
            
            # Current period line (solid)
            fig.add_trace(go.Scatter(
                x=current_trend['month'],
                y=current_trend['price'],
                mode='lines+markers',
                name=f'{current_year}',
                line=dict(color='#1f77b4', width=3),
                marker=dict(size=8)
            ))
            
            # Previous period line (dashed)
            if len(previous_trend) > 0:
                fig.add_trace(go.Scatter(
                    x=previous_trend['month'],
                    y=previous_trend['price'],
                    mode='lines+markers',
                    name=f'{previous_year}',
                    line=dict(color='#ff7f0e', width=3, dash='dash'),
                    marker=dict(size=8)
                ))
            
            fig.update_layout(
                title='Revenue Trend',
                xaxis_title='Month',
                yaxis_title='Revenue',
                showlegend=True,
                xaxis=dict(showgrid=True),
                yaxis=dict(showgrid=True, tickformat='$,.0f'),
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Revenue trend chart requires historical data for comparison")
    
    # Chart 2: Top 10 categories bar chart
    with chart_row1_col2:
        if 'product_category_name' in sales_data.columns:
            category_sales = sales_data.groupby('product_category_name')['price'].sum().sort_values(ascending=False).head(10)
            
            fig = px.bar(
                x=category_sales.values,
                y=category_sales.index,
                orientation='h',
                title='Top 10 Categories',
                labels={'x': 'Revenue', 'y': 'Category'}
            )
            
            # Blue gradient
            fig.update_traces(
                marker_color=px.colors.sequential.Blues_r,
                text=[format_currency(val) for val in category_sales.values],
                textposition='outside'
            )
            
            fig.update_layout(
                yaxis={'categoryorder': 'total ascending'},
                xaxis_tickformat='$,.0f',
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Category data not available")
    
    chart_row2_col1, chart_row2_col2 = st.columns(2)
    
    # Chart 3: Revenue by state choropleth map
    with chart_row2_col1:
        if 'customer_state' in sales_data.columns:
            state_sales = sales_data.groupby('customer_state')['price'].sum().reset_index()
            
            fig = px.choropleth(
                state_sales,
                locations='customer_state',
                color='price',
                locationmode='USA-states',
                scope='usa',
                title='Revenue by State',
                color_continuous_scale='Blues',
                labels={'price': 'Revenue ($)', 'customer_state': 'State'}
            )
            
            fig.update_layout(
                geo=dict(showframe=False, showcoastlines=True),
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Geographic data not available")
    
    # Chart 4: Satisfaction vs delivery time
    with chart_row2_col2:
        if 'delivery_days' in sales_data.columns and 'review_score' in sales_data.columns:
            # Create delivery time buckets
            sales_data_copy = sales_data.copy()
            sales_data_copy['delivery_bucket'] = pd.cut(
                sales_data_copy['delivery_days'],
                bins=[0, 3, 7, float('inf')],
                labels=['1-3 days', '4-7 days', '8+ days']
            )
            
            satisfaction_delivery = sales_data_copy.groupby('delivery_bucket')['review_score'].mean().reset_index()
            
            fig = px.bar(
                satisfaction_delivery,
                x='delivery_bucket',
                y='review_score',
                title='Satisfaction vs Delivery Time',
                labels={'delivery_bucket': 'Delivery Time', 'review_score': 'Average Review Score'}
            )
            
            fig.update_traces(marker_color='#1f77b4')
            fig.update_layout(
                yaxis_range=[0, 5],
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Delivery and review data not available")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Bottom Row - 2 cards
    st.markdown("### Additional Metrics")
    bottom_col1, bottom_col2 = st.columns(2)
    
    with bottom_col1:
        # Average delivery time with trend indicator
        avg_delivery = delivery_metrics.get('avg_delivery_days', 0)
        delivery_trend = 0  # Would need historical data to calculate actual trend
        arrow, trend_class = get_trend_arrow(delivery_trend)
        
        st.markdown(f"""
        <div class="bottom-card">
            <div class="bottom-card-value">{avg_delivery:.1f}</div>
            <div class="bottom-card-subtitle">Average Delivery Time (Days)</div>
            <div class="trend-indicator {trend_class}">{arrow} {delivery_trend:.2f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with bottom_col2:
        # Review Score with stars
        avg_review = delivery_metrics.get('avg_review_score', 0)
        stars = "★" * int(avg_review) + "☆" * (5 - int(avg_review))
        
        st.markdown(f"""
        <div class="bottom-card">
            <div class="bottom-card-value">{avg_review:.1f}</div>
            <div class="stars">{stars}</div>
            <div class="bottom-card-subtitle">Average Review Score</div>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()