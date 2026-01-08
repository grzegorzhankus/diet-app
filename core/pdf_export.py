"""
PDF Export Engine for DIET_APP
Generates professional PDF reports with charts and analytics.
"""
from datetime import date, timedelta
from typing import Optional
from pathlib import Path
import io
import base64

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.widgets.markers import makeMarker

import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt

from core.storage import Storage
from core.metrics import MetricsEngine
from core.kpi_engine import KPIEngine
from core.red_flags import RedFlagsEngine


class PDFExportEngine:
    """Generates professional PDF reports with charts and analytics."""

    def __init__(self, storage: Storage, bmr_kcal: float = 2000.0, target_weight_kg: float = 75.0):
        """
        Initialize PDF export engine.

        Args:
            storage: Storage instance
            bmr_kcal: Basal Metabolic Rate in kcal/day
            target_weight_kg: Target weight for KPI calculations
        """
        self.storage = storage
        self.bmr_kcal = bmr_kcal
        self.target_weight_kg = target_weight_kg

        self.metrics = MetricsEngine(storage, bmr_kcal=bmr_kcal)
        self.kpis = KPIEngine(storage, target_weight_kg=target_weight_kg, bmr_kcal=bmr_kcal)
        self.red_flags = RedFlagsEngine(storage, bmr_kcal=bmr_kcal)

    def export_to_pdf(
        self,
        days: int = 90,
        include_kpis: bool = True,
        include_red_flags: bool = True,
        include_charts: bool = True
    ) -> bytes:
        """
        Export comprehensive report to PDF format.

        Args:
            days: Number of days to include
            include_kpis: Include KPI section
            include_red_flags: Include red flags section
            include_charts: Include charts

        Returns:
            PDF file as bytes
        """
        # Create PDF in memory
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )

        # Build document content
        story = []
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f77b4'),
            spaceAfter=30,
            alignment=TA_CENTER
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=12,
            spaceBefore=20
        )

        # Title
        story.append(Paragraph("DIET_APP Report", title_style))
        story.append(Paragraph(
            f"Generated: {date.today().strftime('%Y-%m-%d')} | Period: Last {days} days",
            styles['Normal']
        ))
        story.append(Spacer(1, 0.5*inch))

        # Summary section
        self._add_summary_section(story, styles, heading_style, days)

        # Charts (if requested and data available)
        if include_charts:
            self._add_charts_section(story, styles, heading_style, days)

        # KPIs section (if requested)
        if include_kpis:
            self._add_kpi_section(story, styles, heading_style, days)

        # Red Flags section (if requested)
        if include_red_flags:
            self._add_red_flags_section(story, styles, heading_style, days)

        # Footer
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph(
            "Generated offline with DIET_APP | CFO-grade analytics",
            ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
        ))

        # Build PDF
        doc.build(story)

        # Get PDF bytes
        buffer.seek(0)
        return buffer.getvalue()

    def _add_summary_section(self, story, styles, heading_style, days: int):
        """Add summary statistics section."""
        story.append(Paragraph("Summary Statistics", heading_style))

        stats = self.metrics.get_summary_stats(days=days)

        if not stats:
            story.append(Paragraph("No data available", styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
            return

        # Summary table
        data = [
            ['Metric', 'Value'],
            ['Data Coverage', f"{stats.get('data_coverage', 0):.1f}%"],
            ['Current Weight', f"{stats.get('weight_current_kg', 0):.1f} kg"],
            ['Weight Change', f"{stats.get('weight_change_kg', 0):+.1f} kg"],
            ['Average Weight', f"{stats.get('weight_avg_kg', 0):.1f} kg"],
        ]

        # Add body composition if available
        if stats.get('fm_current_kg'):
            data.extend([
                ['Current Fat Mass', f"{stats.get('fm_current_kg', 0):.1f} kg"],
                ['Current Body Fat %', f"{stats.get('bf_current_pct', 0):.1f}%"],
            ])

        # Add calorie metrics if available
        if stats.get('cal_net_avg_kcal') is not None:
            data.extend([
                ['Avg NET Calories', f"{stats.get('cal_net_avg_kcal', 0):.0f} kcal/day"],
                ['Avg Intake', f"{stats.get('cal_in_avg_kcal', 0):.0f} kcal/day"],
                ['Avg Sport', f"{stats.get('cal_out_sport_avg_kcal', 0):.0f} kcal/day"],
            ])

        table = Table(data, colWidths=[8*cm, 6*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#366092')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))

        story.append(table)
        story.append(Spacer(1, 0.3*inch))

    def _add_charts_section(self, story, styles, heading_style, days: int):
        """Add charts using matplotlib."""
        story.append(PageBreak())
        story.append(Paragraph("Charts & Trends", heading_style))

        # Get data
        df = self.metrics.get_metrics_dataframe(days=days)

        if df.empty:
            story.append(Paragraph("No data available for charts", styles['Normal']))
            return

        # Create weight chart
        weight_img = self._create_weight_chart(df)
        if weight_img:
            story.append(Image(weight_img, width=6*inch, height=3*inch))
            story.append(Spacer(1, 0.2*inch))

        # Create calorie chart if data available
        if df['cal_net_kcal'].notna().sum() > 0:
            cal_img = self._create_calorie_chart(df)
            if cal_img:
                story.append(Image(cal_img, width=6*inch, height=3*inch))
                story.append(Spacer(1, 0.2*inch))

    def _create_weight_chart(self, df: pd.DataFrame) -> Optional[io.BytesIO]:
        """Create weight trend chart using matplotlib."""
        try:
            fig, ax = plt.subplots(figsize=(10, 5))

            # Convert date to datetime
            df = df.copy()
            df['date'] = pd.to_datetime(df['date'])

            # Plot weight
            ax.plot(df['date'], df['bs_weight_kg'], 'o-', label='Weight', color='#1f77b4', linewidth=2)

            # Plot 7-day average if available
            if 'bs_weight_7d_avg_kg' in df.columns and df['bs_weight_7d_avg_kg'].notna().sum() > 0:
                ax.plot(df['date'], df['bs_weight_7d_avg_kg'], '--', label='7-day Avg',
                       color='#ff7f0e', linewidth=2)

            ax.set_xlabel('Date')
            ax.set_ylabel('Weight (kg)')
            ax.set_title('Weight Trend')
            ax.legend()
            ax.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()

            # Save to bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close(fig)

            return img_buffer

        except Exception as e:
            print(f"Error creating weight chart: {e}")
            plt.close('all')
            return None

    def _create_calorie_chart(self, df: pd.DataFrame) -> Optional[io.BytesIO]:
        """Create calorie balance chart using matplotlib."""
        try:
            fig, ax = plt.subplots(figsize=(10, 5))

            # Convert date to datetime
            df = df.copy()
            df['date'] = pd.to_datetime(df['date'])

            # Filter to rows with calorie data
            df_cal = df[df['cal_net_kcal'].notna()].copy()

            if len(df_cal) == 0:
                plt.close(fig)
                return None

            # Plot NET calories
            ax.plot(df_cal['date'], df_cal['cal_net_kcal'], 'o-', label='NET Balance',
                   color='#2ca02c', linewidth=2)

            # Add zero line
            ax.axhline(y=0, color='red', linestyle='--', alpha=0.5, label='Balance Point')

            ax.set_xlabel('Date')
            ax.set_ylabel('Calories (kcal)')
            ax.set_title('Calorie Balance (NET)')
            ax.legend()
            ax.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()

            # Save to bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close(fig)

            return img_buffer

        except Exception as e:
            print(f"Error creating calorie chart: {e}")
            plt.close('all')
            return None

    def _add_kpi_section(self, story, styles, heading_style, days: int):
        """Add KPI section."""
        story.append(PageBreak())
        story.append(Paragraph("Key Performance Indicators", heading_style))

        kpis = self.kpis.compute_all_kpis(days=days)

        if not kpis:
            story.append(Paragraph("No KPIs available", styles['Normal']))
            return

        # KPI table
        data = [['KPI', 'Value', 'Status', 'Explanation']]

        for kpi in kpis:
            # Status symbol
            if kpi.is_good is True:
                status = '✓ Good'
            elif kpi.is_good is False:
                status = '✗ Needs Work'
            else:
                status = '-'

            # Format value
            value_str = f"{kpi.value} {kpi.unit}" if kpi.value is not None else "N/A"

            data.append([
                kpi.name,
                value_str,
                status,
                kpi.explanation[:80] + '...' if len(kpi.explanation) > 80 else kpi.explanation
            ])

        table = Table(data, colWidths=[4*cm, 2.5*cm, 2.5*cm, 5.5*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#366092')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))

        story.append(table)
        story.append(Spacer(1, 0.3*inch))

    def _add_red_flags_section(self, story, styles, heading_style, days: int):
        """Add red flags section."""
        story.append(PageBreak())
        story.append(Paragraph("Red Flags & Issues", heading_style))

        flags = self.red_flags.detect_all_flags(days=days)

        if not flags:
            story.append(Paragraph(
                "✓ No red flags detected - Great job!",
                ParagraphStyle('Success', parent=styles['Normal'], textColor=colors.green, fontSize=12)
            ))
            return

        # Group by severity
        critical = [f for f in flags if f.severity == 'critical']
        high = [f for f in flags if f.severity == 'high']
        medium = [f for f in flags if f.severity == 'medium']
        low = [f for f in flags if f.severity == 'low']

        # Summary
        story.append(Paragraph(
            f"Total Issues: {len(flags)} (Critical: {len(critical)}, High: {len(high)}, "
            f"Medium: {len(medium)}, Low: {len(low)})",
            styles['Normal']
        ))
        story.append(Spacer(1, 0.2*inch))

        # Flags table
        data = [['Severity', 'Category', 'Issue', 'Recommendation']]

        for flag in flags:
            data.append([
                flag.severity.upper(),
                flag.category,
                flag.title,
                (flag.recommendation or '')[:100] + '...' if flag.recommendation and len(flag.recommendation) > 100 else (flag.recommendation or '')
            ])

        table = Table(data, colWidths=[2*cm, 3*cm, 4.5*cm, 5*cm])

        # Color coding for severity
        table_style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#366092')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]

        # Add severity colors
        for i, flag in enumerate(flags, 1):
            if flag.severity == 'critical':
                color = colors.HexColor('#FF0000')
            elif flag.severity == 'high':
                color = colors.HexColor('#FF6600')
            elif flag.severity == 'medium':
                color = colors.HexColor('#FFAA00')
            else:
                color = colors.HexColor('#FFFF00')

            table_style.append(('BACKGROUND', (0, i), (0, i), color))

        table.setStyle(TableStyle(table_style))

        story.append(table)
        story.append(Spacer(1, 0.3*inch))
