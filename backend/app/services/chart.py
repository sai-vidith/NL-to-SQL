"""
Matplotlib-based server-side chart generation for Telegram Bot and offline image exports.
"""

from __future__ import annotations

import io
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from typing import Any
from app.schemas.query import ChartConfig, ChartType

def generate_matplotlib_chart(config: ChartConfig) -> bytes:
    """
    Renders a premium visual chart from a ChartConfig using Matplotlib.
    Returns the chart as raw PNG bytes.
    """
    # Use dark background defaults
    plt.style.use('dark_background')
    
    # Create figure and axes
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=150)
    
    # Premium deep navy background colors matching Nexus Dashboard
    bg_color = '#0c102b'
    fig.patch.set_facecolor(bg_color)
    ax.set_facecolor(bg_color)
    
    # Set up styling parameters
    ax.grid(True, color='#1f295c', linestyle='--', alpha=0.5, zorder=0)
    
    chart_type = config.chart_type
    labels = [str(l) for l in config.labels]
    
    dataset = config.datasets[0] if config.datasets else {"label": "Data", "data": []}
    data = dataset.get("data", [])
    label = dataset.get("label", "Value")
    
    # Cast data safely to float
    numeric_data = []
    for val in data:
        try:
            numeric_data.append(float(val))
        except (ValueError, TypeError):
            numeric_data.append(0.0)
            
    # Curated premium color palette
    colors = ['#6366f1', '#a855f7', '#ec4899', '#3b82f6', '#10b981', '#f59e0b']
    
    if chart_type == ChartType.BAR:
        bars = ax.bar(labels, numeric_data, color=colors[0], edgecolor='#a855f7', alpha=0.85, width=0.5, zorder=3)
        # Add labels on top of bars
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height:g}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=8, color='#e2e8f0')
            
    elif chart_type == ChartType.HORIZONTAL_BAR or chart_type == "horizontalBar":
        bars = ax.barh(labels, numeric_data, color=colors[1], edgecolor='#6366f1', alpha=0.85, height=0.5, zorder=3)
        # Add labels next to bars
        for bar in bars:
            width = bar.get_width()
            ax.annotate(f'{width:g}',
                        xy=(width, bar.get_y() + bar.get_height() / 2),
                        xytext=(3, 0),  # 3 points horizontal offset
                        textcoords="offset points",
                        ha='left', va='center', fontsize=8, color='#e2e8f0')
            
    elif chart_type == ChartType.LINE:
        ax.plot(labels, numeric_data, marker='o', color='#ec4899', linewidth=2.5, markersize=6, label=label, zorder=3)
        ax.fill_between(labels, numeric_data, color='#ec4899', alpha=0.15, zorder=2)
        # Add value markers
        for i, txt in enumerate(numeric_data):
            ax.annotate(f'{txt:g}', (labels[i], numeric_data[i]), textcoords="offset points", xytext=(0, 7), ha='center', fontsize=8, color='#e2e8f0')
            
    elif chart_type in [ChartType.PIE, ChartType.DOUGHNUT]:
        # Filter zero/negative data for pie charts to prevent crashes
        pie_labels = []
        pie_data = []
        for i, val in enumerate(numeric_data):
            if val > 0:
                pie_labels.append(labels[i])
                pie_data.append(val)
                
        if not pie_data:
            pie_labels = ["No Data"]
            pie_data = [1]
            
        wedges, texts, autotexts = ax.pie(
            pie_data,
            labels=pie_labels,
            autopct='%1.1f%%',
            colors=colors[:len(pie_data)],
            startangle=140,
            textprops=dict(color="#e2e8f0", fontsize=9),
            zorder=3
        )
        
        if chart_type == ChartType.DOUGHNUT:
            centre_circle = plt.Circle((0, 0), 0.70, fc=bg_color)
            fig.gca().add_artist(centre_circle)
            
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_weight('bold')
            autotext.set_fontsize(8)
            
    # Labels & Title
    ax.set_title(config.title, fontsize=12, pad=15, color='#ffffff', weight='bold')
    
    if chart_type not in [ChartType.PIE, ChartType.DOUGHNUT]:
        if config.x_label:
            ax.set_xlabel(config.x_label, color='#94a3b8', labelpad=8, fontsize=9)
        if config.y_label:
            ax.set_ylabel(config.y_label, color='#94a3b8', labelpad=8, fontsize=9)
            
        plt.xticks(rotation=20, ha='right', color='#cbd5e1', fontsize=8)
        plt.yticks(color='#cbd5e1', fontsize=8)
        
        # Border/spines color
        for spine in ax.spines.values():
            spine.set_color('#1f295c')
            
    plt.tight_layout()
    
    # Save to buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', facecolor=bg_color, edgecolor='none', bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    return buf.getvalue()
