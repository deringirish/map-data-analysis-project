import os
import re
from pathlib import Path
import pandas as pd
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_PATH = BASE_DIR / "data_processed" / "database_tables"
NOTICES_DIR = BASE_DIR / "data_processed" / "reports" / "notices"
NOTICES_DIR.mkdir(parents=True, exist_ok=True)


def sanitize_filename(name: str) -> str:
    """Sanitize strings for clean filesystem paths."""
    clean = re.sub(r'[^\w\s-]', '', str(name)).strip()
    return re.sub(r'[-\s]+', '_', clean)


def set_cell_background(cell, fill_hex: str):
    """Set background color of a table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)


def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Set inner padding for a table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('w:top', top), ('w:bottom', bottom), ('w:left', left), ('w:right', right)]:
        node = parse_xml(f'<{m} {nsdecls("w")} w:w="{val}" w:type="dxa"/>')
        tcMar.append(node)
    tcPr.append(tcMar)


def create_violation_notice(homologated_name: str, category: str, group_df: pd.DataFrame, output_path: Path):
    """
    Generates an enterprise-grade, professionally formatted MAP Violation Notice (.docx)
    structured strictly by Category as primary, with Sub-categories as itemized tables.
    """
    doc = Document()

    # Set 1-inch margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    # -------------------------------------------------------------
    # 1. CORPORATE HEADER
    # -------------------------------------------------------------
    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_before = Pt(0)
    title_p.paragraph_format.space_after = Pt(2)
    run_brand = title_p.add_run("GLOBAL BRAND PROTECTION & COMPLIANCE DIVISION")
    run_brand.font.name = "Calibri"
    run_brand.font.size = Pt(11)
    run_brand.font.bold = True
    run_brand.font.color.rgb = RGBColor(70, 80, 95)

    notice_title = doc.add_paragraph()
    notice_title.paragraph_format.space_before = Pt(4)
    notice_title.paragraph_format.space_after = Pt(12)
    run_title = notice_title.add_run(f"OFFICIAL NOTICE OF MAP POLICY VIOLATION: {category.upper()}")
    run_title.font.name = "Calibri"
    run_title.font.size = Pt(18)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(180, 40, 40)  # Crimson Alert

    # -------------------------------------------------------------
    # 2. METADATA SUMMARY TABLE
    # -------------------------------------------------------------
    meta_table = doc.add_table(rows=4, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_table.autofit = False

    meta_data = [
        ("Recipient Organization (Homologated):", homologated_name),
        ("Target Product Category:", category),
        ("Marketplaces Audited:", ", ".join(group_df["Marketplace"].dropna().unique())),
        ("Date of Issuance / Surveillance Cycle:", f"{group_df['Violation_date'].min()} to {group_df['Violation_date'].max()}")
    ]

    for idx, (label, val) in enumerate(meta_data):
        row = meta_table.rows[idx]
        c0, c1 = row.cells[0], row.cells[1]
        c0.width = Inches(2.5)
        c1.width = Inches(4.0)

        p0 = c0.paragraphs[0]
        p0.paragraph_format.space_after = Pt(2)
        r0 = p0.add_run(label)
        r0.font.bold = True
        r0.font.size = Pt(9.5)

        p1 = c1.paragraphs[0]
        p1.paragraph_format.space_after = Pt(2)
        r1 = p1.add_run(val)
        r1.font.size = Pt(9.5)

        set_cell_background(c0, "F1F5F9")
        set_cell_background(c1, "FFFFFF")
        set_cell_margins(c0, 60, 60, 100, 100)
        set_cell_margins(c1, 60, 60, 100, 100)

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # -------------------------------------------------------------
    # 3. FORMAL NOTICE STATEMENT
    # -------------------------------------------------------------
    stmt_p = doc.add_paragraph()
    stmt_p.paragraph_format.line_spacing = 1.15
    stmt_p.paragraph_format.space_after = Pt(10)
    stmt_p.add_run(
        f"This document constitutes formal notification that authorized surveillance of e-commerce channels has "
        f"detected multiple non-compliant listings by your affiliated storefronts. Specifically, advertised prices "
        f"for products within the "
    )
    r_cat = stmt_p.add_run(f"'{category}'")
    r_cat.bold = True
    stmt_p.add_run(
        f" category were observed below the mandated Lowest Possible Price (LPP) or in breach of promotional governance rules. "
        f"A total of "
    )
    r_cnt = stmt_p.add_run(f"{len(group_df):,} infractions")
    r_cnt.bold = True
    stmt_p.add_run(" have been documented across your active merchant accounts.")

    # -------------------------------------------------------------
    # 4. SUB-CATEGORY ITEMIZED INFRACTIONS
    # -------------------------------------------------------------
    subcats = group_df["Sub_category"].dropna().unique()

    for subcat in sorted(subcats):
        sub_df = group_df[group_df["Sub_category"] == subcat].copy()

        h_sub = doc.add_paragraph()
        h_sub.paragraph_format.space_before = Pt(12)
        h_sub.paragraph_format.space_after = Pt(4)
        run_sub = h_sub.add_run(f"Sub-Category: {subcat} ({len(sub_df):,} Infractions)")
        run_sub.font.name = "Calibri"
        run_sub.font.size = Pt(13)
        run_sub.font.bold = True
        run_sub.font.color.rgb = RGBColor(30, 60, 110)

        # Table of violations for this subcategory (up to 15 sample rows for readability)
        table = doc.add_table(rows=1, cols=6)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False

        headers = ["SKU", "Marketplace", "Storefront Alias", "Advertised", "LPP Floor", "Violation Type"]
        col_widths = [Inches(1.0), Inches(0.9), Inches(1.8), Inches(0.9), Inches(0.9), Inches(1.5)]

        hdr_row = table.rows[0]
        for c_idx, title in enumerate(headers):
            cell = hdr_row.cells[c_idx]
            cell.width = col_widths[c_idx]
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(title)
            run.font.bold = True
            run.font.size = Pt(9)
            run.font.color.rgb = RGBColor(255, 255, 255)
            set_cell_background(cell, "1E3A8A")  # Navy Blue
            set_cell_margins(cell, 80, 80, 80, 80)

        # Populate rows (limit display to top 15 rows if many, with summary note)
        display_rows = sub_df.head(15)
        for _, vrow in display_rows.iterrows():
            row = table.add_row()
            vals = [
                str(vrow["SKU"]),
                str(vrow["Marketplace"]),
                str(vrow["seller_name"])[:28],
                f"{float(vrow['Advertised_price']):,.2f}",
                f"{float(vrow['LPP']):,.2f}",
                str(vrow["Violation_Type"])
            ]
            for c_idx, val in enumerate(vals):
                cell = row.cells[c_idx]
                cell.width = col_widths[c_idx]
                p = cell.paragraphs[0]
                p.paragraph_format.space_after = Pt(1)
                if c_idx in [3, 4]:
                    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                elif c_idx in [0, 1]:
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r = p.add_run(val)
                r.font.size = Pt(8.5)
                set_cell_background(cell, "FAFAFA")
                set_cell_margins(cell, 50, 50, 60, 60)

        if len(sub_df) > 15:
            extra_p = doc.add_paragraph()
            extra_p.paragraph_format.space_before = Pt(2)
            extra_p.paragraph_format.space_after = Pt(6)
            r_extra = extra_p.add_run(f"... and {len(sub_df) - 15:,} additional documented infractions for {subcat}. (Full dataset archived in compliance portal).")
            r_extra.font.italic = True
            r_extra.font.size = Pt(8.5)
            r_extra.font.color.rgb = RGBColor(120, 120, 120)

    # -------------------------------------------------------------
    # 5. REQUIRED CORRECTIVE ACTION & CATEGORY SUSPENSION ULTIMATUM
    # -------------------------------------------------------------
    action_h = doc.add_paragraph()
    action_h.paragraph_format.space_before = Pt(16)
    action_h.paragraph_format.space_after = Pt(4)
    run_act = action_h.add_run("MANDATORY CORRECTIVE ACTIONS & ESCALATION PROTOCOL")
    run_act.font.name = "Calibri"
    run_act.font.size = Pt(12)
    run_act.font.bold = True
    run_act.font.color.rgb = RGBColor(180, 40, 40)

    action_p = doc.add_paragraph()
    action_p.paragraph_format.line_spacing = 1.15
    action_p.paragraph_format.space_after = Pt(6)
    action_p.add_run(
        f"1. Immediate Price Correction: Within forty-eight (48) hours of this notice, your organization must adjust "
        f"all advertised prices for the items listed above to or above the published LPP/MAP benchmarks.\n"
        f"2. Written Confirmation: Submit written verification and live listing links demonstrating compliance to "
        f"map-compliance@brandprotection.com.\n"
        f"3. Category Suspension Notice: Pursuant to Section 4 of the Authorized Reseller Agreement, failure to "
        f"cure these pricing violations within 48 hours will trigger an immediate thirty (30) day suspension of your "
        f"reseller authorization for the entire "
    )
    r_act_cat = action_p.add_run(f"'{category}'")
    r_act_cat.bold = True
    action_p.add_run(" category, including cancellation of pending wholesale shipments and revocation of marketing development funds (MDF).")

    # -------------------------------------------------------------
    # 6. SIGNATURE BLOCK
    # -------------------------------------------------------------
    sig_p = doc.add_paragraph()
    sig_p.paragraph_format.space_before = Pt(16)
    sig_p.paragraph_format.space_after = Pt(2)
    sig_p.add_run("Authorized by:\n").font.size = Pt(9.5)
    run_sig = sig_p.add_run("Global MAP Enforcement & Channel Integrity Office\nBrand Legal & Reseller Governance Division")
    run_sig.font.bold = True
    run_sig.font.size = Pt(10)

    doc.save(output_path)


def generate_all_notices_and_update_tables():
    """Generates notices for all Reseller x Category pairs and updates the violation table."""
    v_table_path = DATA_PATH / "violation_table.csv"
    v_df = pd.read_csv(v_table_path)

    print(f"Loaded {len(v_df):,} violation records.")
    combos = v_df.groupby(["homologated_name", "Category"])

    total_groups = len(combos)
    doc_paths = {}
    print(f"Generating professional notices for {total_groups} Reseller x Category groups...")
    for idx, ((homologated_name, category), group) in enumerate(combos, 1):
        file_name = f"{sanitize_filename(homologated_name)}_{sanitize_filename(category)}_Warning_Notice.docx"
        full_path = NOTICES_DIR / file_name
        rel_path = f"data_processed/reports/notices/{file_name}"

        create_violation_notice(homologated_name, category, group, full_path)
        doc_paths[(homologated_name, category)] = rel_path

        # Print live progress
        if idx <= 5 or idx % 25 == 0 or idx == total_groups:
            print(f"  [{idx:3d}/{total_groups}] Generated: {file_name} ({len(group)} records)")
        elif idx == 6:
            print(f"  ... processing remaining notices ...")

    # Assign relative doc path to violation table
    v_df["Notice_Doc_Path"] = v_df.apply(
        lambda r: doc_paths.get((r["homologated_name"], r["Category"]), None),
        axis=1
    )

    # Reorder columns to place Notice_Doc_Path neatly at the end
    v_df.to_csv(v_table_path, index=False)
    print(f" Successfully generated {len(combos)} .docx notices in:")
    print(f" -> data_processed/reports/notices/")
    print(f" Updated {v_table_path} with new column: 'Notice_Doc_Path' (100% Complete!)")


if __name__ == "__main__":
    generate_all_notices_and_update_tables()
