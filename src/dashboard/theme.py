"""
Shared Dark-Theme Palette & Plotly Styling for Streamlit Dashboard
"""

CYAN = "#00D2FF"
CRIMSON = "#FF4B4B"
TEAL = "#00E676"
AMBER = "#FFA726"
SLATE = "#94A3B8"
BLUE = "#3B82F6"


def apply_dark_theme(fig):
    """Applies modern dark-theme styling with transparent background to Plotly figures."""
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#FAFAFA", family="sans-serif"),
    )
    return fig
