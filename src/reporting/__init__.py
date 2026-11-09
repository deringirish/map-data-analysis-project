"""
Reporting & Executive Synthesis Package
Author: Derin Girish D G
Description: Executive briefing generation, legal warning notice synthesis, and publication analytics.
"""

from .generate_executive_briefing import (
    compile_executive_metrics,
    generate_html_briefing,
    generate_markdown_briefing,
    main as run_executive_briefing,
)
from .generate_violation_notices import (
    generate_all_notices_and_update_tables,
)
from .generate_visualizations import (
    generate_all_figures,
)
