"""
Script to generate high-resolution Streamlit BI Dashboard Preview Image.
Renders the complete Streamlit interface with dark executive theme, sidebar,
KPI metrics cards, and embedded analytic visualizations.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
FIGURES_DIR = ROOT_DIR / "data_processed" / "reports" / "figures"
OUTPUT_PATH = FIGURES_DIR / "00_streamlit_dashboard_preview.png"

def create_dashboard_preview():
    # Canvas dimensions (High resolution 1920x1080)
    width, height = 1920, 1080
    bg_color = (14, 17, 23)  # Streamlit dark background
    sidebar_bg = (21, 27, 38) # Slightly lighter sidebar
    card_bg = (30, 41, 59)    # Modern slate card
    border_color = (51, 65, 85) # Slate border
    text_white = (248, 250, 252)
    text_muted = (148, 163, 184)
    accent_blue = (99, 102, 241) # Indigo accent
    accent_red = (239, 68, 68)   # Red alert
    accent_green = (34, 197, 94) # Green success

    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # Load system fonts
    try:
        font_huge = ImageFont.truetype("arialbd.ttf", 32)
        font_large = ImageFont.truetype("arialbd.ttf", 24)
        font_med_bold = ImageFont.truetype("arialbd.ttf", 18)
        font_med = ImageFont.truetype("arial.ttf", 16)
        font_small = ImageFont.truetype("arial.ttf", 13)
        font_tiny = ImageFont.truetype("arial.ttf", 11)
    except Exception:
        font_huge = font_large = font_med_bold = font_med = font_small = font_tiny = ImageFont.load_default()

    # 1. Top Browser Window Chrome / Header Bar
    draw.rectangle([0, 0, width, 40], fill=(15, 23, 42))
    # Window control dots
    draw.ellipse([15, 14, 27, 26], fill=(239, 68, 68))
    draw.ellipse([35, 14, 47, 26], fill=(245, 158, 11))
    draw.ellipse([55, 14, 67, 26], fill=(34, 197, 94))
    
    # URL bar mockup
    draw.rounded_rectangle([320, 8, 1600, 32], radius=6, fill=(30, 41, 59), outline=border_color)
    draw.text((340, 12), "🔒 http://localhost:8501  —  MAP Compliance & Brand Protection BI Hub | Executive Analytics", fill=text_muted, font=font_small)

    # 2. Left Sidebar (Width: 320px)
    sidebar_w = 320
    draw.rectangle([0, 40, sidebar_w, height], fill=sidebar_bg)
    draw.line([(sidebar_w, 40), (sidebar_w, height)], fill=border_color, width=1)

    # Sidebar Header
    draw.text((25, 65), "⚖️ MAP Intelligence Hub", fill=text_white, font=font_large)
    draw.text((25, 100), "Enterprise Brand Protection Suite", fill=text_muted, font=font_small)
    draw.line([(25, 125), (295, 125)], fill=border_color, width=1)

    # Sidebar Navigation Items
    draw.text((25, 145), "NAVIGATION MENU", fill=text_muted, font=font_tiny)
    
    # Active menu card
    draw.rounded_rectangle([20, 170, 300, 210], radius=6, fill=card_bg, outline=accent_blue, width=2)
    draw.text((35, 180), "📊 Executive KPI Overview", fill=text_white, font=font_med_bold)
    
    draw.rounded_rectangle([20, 220, 300, 260], radius=6, fill=(26, 34, 48))
    draw.text((35, 230), "🕵️ Reseller Surveillance", fill=text_muted, font=font_med)

    draw.rounded_rectangle([20, 270, 300, 310], radius=6, fill=(26, 34, 48))
    draw.text((35, 280), "🔬 Deep Visual Analytics", fill=text_muted, font=font_med)

    draw.line([(25, 335), (295, 335)], fill=border_color, width=1)

    # Sidebar Filters
    draw.text((25, 355), "🎛️ OMNI-CHANNEL FILTERS", fill=text_muted, font=font_tiny)
    
    draw.text((25, 385), "Marketplaces (Active: 4/4)", fill=text_white, font=font_small)
    channels = ["☑ Amazon.in", "☑ Flipkart", "☑ JioMart", "☑ Tata CliQ"]
    for i, ch in enumerate(channels):
        draw.text((35, 410 + i * 24), ch, fill=accent_blue if "Amazon" in ch else text_muted, font=font_small)

    draw.text((25, 520), "Product Divisions (Active: 6/6)", fill=text_white, font=font_small)
    cats = ["☑ Smartphones", "☑ Laptops & Computing", "☑ Audio & Acoustics", "☑ Smart Wearables", "☑ Camera & Imaging"]
    for i, cat in enumerate(cats):
        draw.text((35, 545 + i * 24), cat, fill=text_muted, font=font_small)

    draw.line([(25, 680), (295, 680)], fill=border_color, width=1)
    
    # System status in sidebar
    draw.text((25, 700), "SYSTEM STATUS", fill=text_muted, font=font_tiny)
    draw.text((25, 725), "🟢 Real-time Feed: Synchronized", fill=accent_green, font=font_small)
    draw.text((25, 750), "📁 Total Records: 147,900", fill=text_muted, font=font_small)
    draw.text((25, 775), "⚡ Engine Version: v2.4 Enterprise", fill=text_muted, font=font_small)

    # 3. Main Dashboard Body (X: 350 to 1890)
    main_x = 350
    main_w = width - main_x - 30

    # Main Header & Title
    draw.text((main_x, 65), "🎯 Executive KPI Overview & Holiday Surveillance Scope", fill=text_white, font=font_huge)
    draw.text((main_x, 110), "Surveillance trajectory across 147,900 omni-channel listings (Dec 21, 2025 – Jan 05, 2026) | All 4 Marketplaces", fill=text_muted, font=font_med)

    # 4. Top KPI Metric Cards (4 Columns)
    card_gap = 20
    card_w = int((main_w - (3 * card_gap)) / 4)
    card_h = 110
    card_y = 145

    kpis = [
        ("TOTAL POLICY VIOLATIONS", "15,936", "+12.4% vs Baseline", accent_red, "Confirmed listings below floor price"),
        ("MARGINShortfall (INR)", "₹1.85 Cr", "₹18,524,310 Deficit", accent_red, "Cumulative discount erosion"),
        ("ACTIVE SUSPENSIONS", "279", "Obj. 4 Enforced", accent_blue, "Resellers with 3+ strike recidivism"),
        ("MONITORED ROGUE ENTITIES", "1,280", "Omni-Channel Scope", accent_green, "Distinct corporate parent sellers"),
    ]

    for i, (title, val, delta, d_color, desc) in enumerate(kpis):
        cx = main_x + i * (card_w + card_gap)
        draw.rounded_rectangle([cx, card_y, cx + card_w, card_y + card_h], radius=8, fill=card_bg, outline=border_color, width=1)
        draw.text((cx + 18, card_y + 14), title, fill=text_muted, font=font_tiny)
        draw.text((cx + 18, card_y + 36), val, fill=text_white, font=font_large)
        draw.text((cx + 18, card_y + 72), delta, fill=d_color, font=font_small)
        draw.text((cx + 18, card_y + 90), desc, fill=text_muted, font=font_tiny)

    # 5. Visual Charts Grid (Row 1: Two Large Charts)
    # Chart 1: Daily Trend, Chart 2: Violations by Marketplace
    grid_y = card_y + card_h + 25
    c_w1 = int(main_w * 0.60)
    c_w2 = main_w - c_w1 - 20
    grid_h = 360

    # Box 1: Daily Trend
    draw.rounded_rectangle([main_x, grid_y, main_x + c_w1, grid_y + grid_h], radius=8, fill=card_bg, outline=border_color, width=1)
    draw.text((main_x + 20, grid_y + 16), "📈 Holiday Shopping Surveillance Trajectory (Daily Trend)", fill=text_white, font=font_med_bold)
    
    # Load and paste chart 03
    f03 = FIGURES_DIR / "03_daily_violation_trend.png"
    if f03.exists():
        im03 = Image.open(f03)
        im03_resized = im03.resize((c_w1 - 30, grid_h - 60), Image.Resampling.LANCZOS)
        img.paste(im03_resized, (main_x + 15, grid_y + 48))

    # Box 2: Marketplace breakdown
    bx2 = main_x + c_w1 + 20
    draw.rounded_rectangle([bx2, grid_y, bx2 + c_w2, grid_y + grid_h], radius=8, fill=card_bg, outline=border_color, width=1)
    draw.text((bx2 + 20, grid_y + 16), "🛒 Marketplace Infraction Share", fill=text_white, font=font_med_bold)
    
    f01 = FIGURES_DIR / "01_violations_by_marketplace.png"
    if f01.exists():
        im01 = Image.open(f01)
        im01_resized = im01.resize((c_w2 - 30, grid_h - 60), Image.Resampling.LANCZOS)
        img.paste(im01_resized, (bx2 + 15, grid_y + 48))

    # 6. Visual Charts Grid (Row 2: Two Analytical Panels)
    grid_y2 = grid_y + grid_h + 20
    grid_h2 = 360
    c_half = int((main_w - 20) / 2)

    # Box 3: Top Violating Resellers
    draw.rounded_rectangle([main_x, grid_y2, main_x + c_half, grid_y2 + grid_h2], radius=8, fill=card_bg, outline=border_color, width=1)
    draw.text((main_x + 20, grid_y2 + 16), "🚨 Top 10 Recidivist Resellers by Deficit Volume", fill=text_white, font=font_med_bold)
    
    f02 = FIGURES_DIR / "02_top_10_violating_resellers.png"
    if f02.exists():
        im02 = Image.open(f02)
        im02_resized = im02.resize((c_half - 30, grid_h2 - 60), Image.Resampling.LANCZOS)
        img.paste(im02_resized, (main_x + 15, grid_y2 + 48))

    # Box 4: Suspension Status by Category
    bx4 = main_x + c_half + 20
    draw.rounded_rectangle([bx4, grid_y2, bx4 + c_half, grid_y2 + grid_h2], radius=8, fill=card_bg, outline=border_color, width=1)
    draw.text((bx4 + 20, grid_y2 + 16), "⚖️ Reseller Suspensions & Compliance Enforcement Status", fill=text_white, font=font_med_bold)
    
    f06 = FIGURES_DIR / "06_category_suspension_status.png"
    if f06.exists():
        im06 = Image.open(f06)
        im06_resized = im06.resize((c_half - 30, grid_h2 - 60), Image.Resampling.LANCZOS)
        img.paste(im06_resized, (bx4 + 15, grid_y2 + 48))

    # Save output
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUTPUT_PATH, "PNG", quality=95)
    print(f"[SUCCESS] Dashboard preview successfully generated at: {OUTPUT_PATH}")

if __name__ == "__main__":
    create_dashboard_preview()
