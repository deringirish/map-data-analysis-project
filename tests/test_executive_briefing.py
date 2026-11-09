"""
Unit tests for Executive C-Suite Briefing Generator
"""

from pathlib import Path
from src.reporting.generate_executive_briefing import compile_executive_metrics, generate_html_briefing, generate_markdown_briefing


def test_compile_executive_metrics():
    metrics = compile_executive_metrics()
    assert "compliance_rate" in metrics
    assert "total_deficit" in metrics
    assert "sellers_80_pct" in metrics
    assert "critical_suspensions" in metrics
    assert metrics["compliance_rate"] > 80.0
    assert metrics["total_deficit"] > 0.0
    assert metrics["sellers_80_pct"] > 0


def test_generate_html_briefing():
    metrics = compile_executive_metrics()
    html = generate_html_briefing(metrics)
    assert "<!DOCTYPE html>" in html
    assert "Executive C-Suite Intelligence Briefing" in html
    assert f"{metrics['compliance_rate']:.1f}%" in html


def test_generate_markdown_briefing():
    metrics = compile_executive_metrics()
    md = generate_markdown_briefing(metrics)
    assert "# ⚖️ Executive C-Suite Intelligence Briefing" in md
    assert "Macro Compliance Scorecard" in md
    assert "Strategic Executive Roadmap" in md
