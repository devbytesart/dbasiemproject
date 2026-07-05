"""
Copyright 2026 ttdantett DevBytesArt

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

author: ttdantett
title: siem project
document: report manager

"""

import os
import time
import json
import base64
import traceback
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import csv
from io import BytesIO, StringIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape, portrait
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
import Utils as utils
import UtilsEnum as uenum


class ReportManager:
    def __init__(self, logger, indexer, authenticator):
        # Logger
        self.logger = logger
        self.indexer = indexer
        self.authenticator = authenticator


    def generate_report(self, request, session):
        """ Generate the report based on the data provided """
        print("before sessions print")
        try:
            print("session:" , str(session), " ", str(type(session)))
            print("request:", str(request), " ",  str(type(request)))
            widgets = request.get("widgets")
            print("widgets:", str(widgets))
            format_report = request.get("format_report", "pdf")
            or_portrait = request.get("portrait", True)
            query = {
                "query": request.get("query"),
                "startTime": request.get("startTime"), 
                "endTime": request.get("endTime"),
                "session_token": json.dumps(session),
                "all_pages": True,
                "page_id": request.get("page_id"),
                "format_report": format_report,
                "portrait": or_portrait,
                "current_id": utils.create_current_id(session.get("username"),request.get("page_id"))
            }
            token_data = session.get("token")
            print("query:", str(query))
            results = {}
            for w in widgets:
                print("Widget w: ", str(w))
                if w.get("type") == "query":
                    config = w.get("config",{})
                    index = config.get("index").split(",")
                    tenant = config.get("tenant").split(",")
                    technology = config.get("technology").split(",")
                    # Add in query 
                    query["index"] = index
                    query["tenant"] = tenant
                    query["technology"] = technology
                    # Check permissions
                    permissions_required = []
                    for ind in index:
                        permissions_required.append({"resource": ind, "type": "index", "read": True, "write": False})
                    for ten in tenant:
                        permissions_required.append({"resource": ten, "type": "tenant", "read": True, "write": False})
                    print("type query")
                    query["query"] = config.get("command")
                    print("query widget.", str(query["query"]))
                    if json.loads(self.authenticator.check_permissions(token_data, permissions_required)):
                        results[w.get("id")] = self.indexer.handle_search_data({"query":query}, query["current_id"])
                    else:
                        return None
                else:
                    print("type non query")
                    results[w.get("id")] = {"type": w.get("type"), "data": w.get("config").get("content")}
            print("Results: ", str(results))
            print("generate_report before interpret: format: ", str(format_report))
            return self.interpret_report_type(results, request, format_report, or_portrait)
        except:
            self.logger.log("error", f"Failed to generate report: {traceback.format_exc()}")
            return None

    def interpret_report_type(self, data, request, format_report="pdf", or_portrait=True):
        """ Generate a report with widgets, ensuring tables and graphs display correctly. """
        try:
            print("interpret_report_type:", str(format_report))
            # Get Widgets list
            widgets = sorted(request.get("widgets"), key=lambda w: w["position"]["top"])
            # PDF REPORT
            if format_report == "pdf":
                print("Generating PDF")

                pdf_filename = "temp_report.pdf"
                if or_portrait:
                    doc = SimpleDocTemplate(pdf_filename, pagesize=portrait(letter))
                else:
                    doc = SimpleDocTemplate(pdf_filename, pagesize=landscape(letter))
                elements = []

                PAGE_WIDTH, PAGE_HEIGHT = letter
                MARGIN_LEFT = 50
                MAX_WIDTH = PAGE_WIDTH - 2 * MARGIN_LEFT
                SPACE_BETWEEN_WIDGETS = 20

                styles = getSampleStyleSheet()
                cell_style = styles["BodyText"]
                cell_style.wordWrap = 'CJK'
                title_style = styles["Title"]

                for w in widgets:
                    name = w.get("name", None)
                    if name:
                        elements.append(Paragraph(name, title_style))
                        elements.append(Spacer(1, 10))
                    d_w = data.get(w.get("id"), {})
                    print(f"Widget '{w.get('id')}' with type '{d_w}'")
                    res_type = d_w.get("type","text")
                    f = d_w.get("fields", [])
                    d = d_w.get("data", [])
                    widget_width_percent = w["size"]["width"] / 100
                    widget_left_percent = w["position"]["left"] / 100
                    widget_width = MAX_WIDTH * widget_width_percent
                    widget_x = MARGIN_LEFT + (MAX_WIDTH * widget_left_percent)
                    print(f"Widget '{res_type}': width={widget_width:.2f}, left={widget_x:.2f}")
                    if res_type == "table":
                        if not d:
                            continue
                        elements.append(self.generate_table(d, f, format_report, widget_width, portrait=or_portrait))
                        elements.append(Spacer(1, SPACE_BETWEEN_WIDGETS))
                    elif res_type == "graph":
                        graph_img = self.generate_graph(d, format_report, d_w.get("graph_type", "bar"))
                        if graph_img:
                            elements.append(graph_img)
                            elements.append(Spacer(1, SPACE_BETWEEN_WIDGETS))
                    elif res_type == "text":
                        elements.append(Paragraph(d, cell_style))
                        elements.append(Spacer(1, SPACE_BETWEEN_WIDGETS))
                    elif res_type == "image":
                        elements.append(self.generate_image(d, format_report))
                        elements.append(Spacer(1, SPACE_BETWEEN_WIDGETS))
                    elif res_type == "markdown":
                        # TODO this part
                        pass
                print("before build element")
                doc.build(elements)
                print("before pdf_filename")
                while not os.path.exists(pdf_filename):
                    time.sleep(0.5)
                print("after pdf_filename")
                with open(pdf_filename, "rb") as f:
                    encoded = base64.b64encode(f.read()).decode("utf-8")
                    return f"{uenum.SIEM_Field_Format.file.value}/{uenum.SIEM_File_Type.pdf.value}:{encoded}"
            # CSV REPORT
            elif format_report == "csv":
                print("Generate CSV: data:", str(data), str(type(data)))
                # TODO manage for several widgets, now only first elements is get
                for w in widgets:
                    print("in for widgets loop csv")
                    # get data
                    widget_data = data.get(w.get("id"), {}).get("data",{})
                    print("widget_data", str(widget_data))
                    res_type = data.get(w.get("id"), {}).get("type",{})
                    print("widget_type", str(res_type))
                    # Fields compute
                    fieldnames = set()
                    for d in widget_data:
                        fieldnames.update(d.keys())
                    fieldnames = list(fieldnames)
                    # Only type supported for now
                    if res_type == "table":
                        print("before generate table")
                        csv_data = self.generate_table(widget_data, fieldnames, format_report, None)
                        print("csv_data :", str(csv_data))
                        encoded = base64.b64encode(csv_data.encode("utf-8")).decode("utf-8")
                        print("results encoded:", str(encoded))
                        return f"{uenum.SIEM_Field_Format.file.value}/{uenum.SIEM_File_Type.csv.value}:{encoded}"
        except Exception as e:
            self.logger.log("error", f"Failed to interpret report type: {traceback.format_exc()}")
            return None
        
    def generate_text(self, data, format):
        """ Generate the text based on the data provided """
        try:
            if format == "pdf":
                content = data.get("content", "")
                formatted_data = [Paragraph(str(content), getSampleStyleSheet()["BodyText"])]
                return formatted_data
        except:
            self.logger.log("error", f"Failed to generate text: {traceback.format_exc()}")
            return ""

    def generate_markdown(self, data, format):
        """ Generate the markdown based on the data provided """
        try:
            #TODO 
            return ""
        except:
            self.logger.log("error", f"Failed to generate markdown: {traceback.format_exc()}")  
            return ""

    def generate_graph(self, data, format, graph_type="bar"):
        """ Generate different types of graphs """
        try:
            df = pd.DataFrame(data)
            if df.empty:
                return None

            fig, ax = plt.subplots(figsize=(8, 6), dpi=150)

            if graph_type == "bar":
                sns.barplot(x=df.columns[0], y=df.columns[1], data=df, ax=ax)
            elif graph_type == "line":
                sns.lineplot(x=df.columns[0], y=df.columns[1], data=df, ax=ax)
            elif graph_type == "pie":
                df.set_index(df.columns[0])[df.columns[1]].plot(kind="pie", autopct='%1.1f%%', ax=ax)
                ax.set_ylabel("")
            elif graph_type == "scatter":
                sns.scatterplot(x=df.columns[0], y=df.columns[1], data=df, ax=ax)
            elif graph_type == "bubble":
                sns.scatterplot(x=df.columns[0], y=df.columns[1], size=df.iloc[:, 2], data=df, ax=ax, legend=False)
            elif graph_type == "polar":
                ax = plt.subplot(111, polar=True)
                ax.plot(df[df.columns[0]], df[df.columns[1]])
            elif graph_type == "radar":
                categories = list(df[df.columns[0]])
                values = list(df[df.columns[1]])
                angles = [n / float(len(categories)) * 2 * 3.1416 for n in range(len(categories))]
                angles += angles[:1]
                values += values[:1]
                ax = plt.subplot(111, polar=True)
                ax.fill(angles, values, alpha=0.3)
                ax.set_xticks(angles[:-1])
                ax.set_xticklabels(categories)
            elif graph_type == "donut":
                df.set_index(df.columns[0])[df.columns[1]].plot(kind="pie", autopct='%1.1f%%', ax=ax, wedgeprops=dict(width=0.3))
                ax.set_ylabel("")

            plt.xticks(rotation=45)
            plt.tight_layout()

            img_buffer = BytesIO()
            plt.savefig(img_buffer, format="png", bbox_inches='tight')
            plt.close(fig)
            img_buffer.seek(0)

            return Image(img_buffer, width=400, height=300)
        except:
            self.logger.log("error", f"Failed to generate graph: {traceback.format_exc()}")
            return None
        
        
    def generate_network_graph(self, data, format):
        """ Generate the network graph based on the data provided """
        try:
            # TODO
            pass
        except:
            self.logger.log("error", f"Failed to generate network graph: {traceback.format_exc()}")
            return None
        

    # --------- utils -----------
    def normalize_fields(self, fields):
        """
        Return a list of dicts [{'id':..., 'label':...}, ...]
        Support fields = ["a","b"] or fields = [{'id':'a','label':'A'}, ...]
        """
        normalized = []
        for idx, f in enumerate(fields or []):
            if isinstance(f, dict):
                fid = f.get("id") or f.get("name") or f.get("key") or str(idx)
                label = f.get("label") or f.get("name") or fid
            else:
                fid = str(f)
                label = str(f)
            normalized.append({"id": fid, "label": label})
        return normalized


    def estimate_avg_char_width(self, fontname="Helvetica", fontsize=8):
        """ Estimate mean width of caracter (points) for the font/size given """
        sample = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        w = pdfmetrics.stringWidth(sample, fontname, fontsize)
        return w / len(sample)
    

    def truncate_to_width(self, text, col_width, fontname="Helvetica", fontsize=8, padding=4, max_chars=400):
        """
        Truncates / wraps `text` to fit within `col_width` (points),
        producing multiple lines if necessary. Characters are accumulated
        line by line up to `max_chars`. If the text exceeds this limit, "..."
        is appended to the end (if possible). Returns a string using '<br/>'
        as a line separator (to be subsequently passed to Paragraph()).

        Args:
            text: source text (None -> "")
            col_width: column width in points
            fontname, fontsize: for pdfmetrics.stringWidth
            padding: space (points) to subtract from the usable width
            max_chars: maximum total number of characters to keep before adding "..."
        """
        from xml.sax.saxutils import escape
        if text is None:
            return ""
        if not isinstance(text, str):
            text = str(text)
        usable = max(col_width - padding, 1)
        ellipsis = "..."
        ellipsis_w = pdfmetrics.stringWidth(ellipsis, fontname, fontsize)
        # If text hold in one line and is <= max_chars, return original (escaped)
        if pdfmetrics.stringWidth(text, fontname, fontsize) <= usable and len(text) <= max_chars:
            return escape(text)
        # Search binary for the bigger prefix of s that hold in "usable" width
        def fit_prefix_length(s, max_len=None):
            if not s:
                return 0
            high = min(len(s), max_len) if max_len is not None else len(s)
            low = 0
            while low < high:
                mid = (low + high + 1) // 2
                if pdfmetrics.stringWidth(s[:mid], fontname, fontsize) <= usable:
                    low = mid
                else:
                    high = mid - 1
            return low
        remaining = text
        total_used = 0
        lines = []
        # Iteration with extracting big portion that hold in one line respecting limit max_chars
        while remaining and total_used < max_chars:
            allowed_chars = max_chars - total_used
            # Search biggest portion of "remaining" that hold in width, limit to allowed_chars
            take = fit_prefix_length(remaining, max_len=allowed_chars)
            if take == 0:
                # No way to insert caracter (usable too small)
                break
            line = remaining[:take]
            lines.append(line.rstrip())
            remaining = remaining[take:]
            total_used += take
        truncated = len(remaining) > 0  # remain unconsumed text
        if not lines:
            # None catacter can enter in one line
            if ellipsis_w <= usable:
                return ellipsis
            else:
                return ""
        # If we have truncated, we can add "..." to the last line (if possible)
        if truncated:
            last = lines[-1]
            # if last + ellipsis hold, we add
            if pdfmetrics.stringWidth(last + ellipsis, fontname, fontsize) <= usable:
                lines[-1] = last + ellipsis
            else:
                # Else, reduce last with research binaries to do some place to ellipsis
                low, high = 0, len(last)
                while low < high:
                    mid = (low + high + 1) // 2
                    if pdfmetrics.stringWidth(last[:mid] + ellipsis, fontname, fontsize) <= usable:
                        low = mid
                    else:
                        high = mid - 1
                if low > 0:
                    lines[-1] = last[:low] + ellipsis
                else:
                    # Can't place even one caracter + "...", try just "..." alone
                    if ellipsis_w <= usable:
                        lines[-1] = ellipsis
                    else:
                        # Impossible to display "..." : let empty or as it is
                        pass
        # Escape each lines to split with "<br/>" (paragraph will interpret the <br/>) 
        escaped_lines = [escape(l) for l in lines]
        return "<br/>".join(escaped_lines)



    def compute_col_widths_with_indicator(self, n_cols,
                                        max_table_width,
                                        max_col_width=200,
                                        min_chars=3,
                                        fontname="Helvetica",
                                        fontsize=8,
                                        indicator_label="..."):
        """
        Compute widths of columns in points.
        If all doesn't fit, return a last indicator column.
        Return: (col_widths_list, n_displayed, indicator_used)
        """
        if n_cols <= 0:
            return [], 0, False
        avg = self.estimate_avg_char_width(fontname, fontsize)
        min_col_width = max(avg * min_chars, 8)
        # If we can display all columns with the initial width
        if n_cols * min_col_width <= max_table_width:
            width_each = min(max_col_width, max_table_width / n_cols)
            col_widths = [width_each] * n_cols
            # Adjust for precision
            total = sum(col_widths)
            if total > max_table_width:
                scale = max_table_width / total
                col_widths = [w * scale for w in col_widths]
            return col_widths, n_cols, False
        # Else add indicator column
        indicator_col_width = max(pdfmetrics.stringWidth(indicator_label, fontname, fontsize) + 8, min_col_width)
        # How many columns enter (at least 1)
        n_fit = int((max_table_width - indicator_col_width) // min_col_width)
        if n_fit < 1:
            n_fit = 1
            # Adjuste indicator if required
            if max_table_width - min_col_width > 0:
                indicator_col_width = max_table_width - min_col_width
            else:
                indicator_col_width = min_col_width
        n_display = min(n_fit, n_cols)
        available = max_table_width - indicator_col_width
        width_each = min(max_col_width, available / n_display)
        # Reduce n_display if width_each < min_col_width
        while width_each < min_col_width and n_display > 1:
            n_display -= 1
            width_each = min(max_col_width, available / n_display)
        width_each = max(width_each, min_col_width)
        col_widths = [width_each] * n_display
        col_widths.append(indicator_col_width)
        return col_widths, n_display, True


    # --------- generate_table (method) -----------
    def generate_table(self, data, fields, format_report, widget_width,
                    max_col_width=100, min_chars=2, indicator_label="...", prefer_plusN=True, portrait=True):
        """
        Generate a Table ReportLab robust :
        - normalise fields/data,
        - truncate to x columns max for portrait and Y for landscape,
        - add a last columns '...' if more than x columns authorized
        - truncate the text for the placement in the column.
        prefer_plusN: if True, the column display '+N' instead of '...'
        """
        print("Generate table (robust)")
        try:
            # Fixed column
            MAX_COLUMNS = uenum.SIEM_Report_MAX_COLUMNS.portrait.value if portrait else uenum.SIEM_Report_MAX_COLUMNS.landscape.value
            if format_report != "pdf":
                # fallback CSV
                output = StringIO()
                fieldnames = [f.get("id") for f in self.normalize_fields(fields)]
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
                return output.getvalue()
            
            # PDF part
            styles = getSampleStyleSheet()
            body_style = styles["BodyText"]
            fontname = getattr(body_style, "fontName", "Helvetica")
            fontsize = getattr(body_style, "fontSize", 8)

            # fallback if invalid widget
            if not widget_width or widget_width <= 0:
                PAGE_WIDTH, PAGE_HEIGHT = letter
                MARGIN = 20
                widget_width = PAGE_WIDTH - 2 * MARGIN
                print(f"[generate_table] widget_width invalid, fallback to {widget_width}")

            # standardize fields
            norm_fields = self.normalize_fields(fields)
            headers = [f["label"] for f in norm_fields]
            n_cols = len(norm_fields)

            # ✅ Limitation to x if portrait or Y if landscape
            
            truncated = False
            if n_cols > MAX_COLUMNS:
                headers = headers[:MAX_COLUMNS] + ["..."]
                norm_fields = norm_fields[:MAX_COLUMNS]
                n_cols = MAX_COLUMNS + 1
                truncated = True

            # Compute width of columns
            col_widths, n_displayed, indicator_used = self.compute_col_widths_with_indicator(
                n_cols=n_cols,
                max_table_width=widget_width,
                max_col_width=max_col_width,
                min_chars=min_chars,
                fontname=fontname,
                fontsize=fontsize,
                indicator_label=indicator_label
            )

            print(f"[generate_table] n_cols={n_cols}, n_displayed={n_displayed}, truncated={truncated}")
            print(f"[generate_table] col_widths={col_widths}")

            # build header
            header_cells = []
            for i in range(n_displayed):
                txt = self.truncate_to_width(headers[i], col_widths[i], fontname, fontsize)
                header_cells.append(Paragraph(txt, body_style))
            formated_data = [header_cells]

            # build lines
            for r_idx, row in enumerate(data or []):
                row_cells = []
                for i in range(min(MAX_COLUMNS, n_displayed)):  # Max columns of data
                    fdef = norm_fields[i]
                    fid = fdef["id"]
                    if isinstance(row, dict):
                        val = row.get(fid, "")
                    elif isinstance(row, (list, tuple)):
                        val = row[i] if i < len(row) else ""
                    else:
                        val = row if i == 0 else ""
                    cell_txt = self.truncate_to_width("" if val is None else str(val), col_widths[i], fontname, fontsize)
                    row_cells.append(Paragraph(cell_txt, body_style))
                # ✅ Add column "..." if more than x columns in the page
                if truncated:
                    row_cells.append(Paragraph("...", body_style))
                formated_data.append(row_cells)

            # sanity check
            for idx, r in enumerate(formated_data):
                if len(r) != len(col_widths):
                    print(f"[generate_table] WARNING: mismatch ligne {idx} len={len(r)} vs col_widths={len(col_widths)}")
                    col_widths = [widget_width / len(r)] * len(r)
                    break

            table = Table(formated_data, colWidths=col_widths, repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('GRID', (0, 0), (-1, -1), 0.25, colors.black)
            ]))
            return table
        except Exception:
            self.logger.log("error", f"Failed to generate table: {traceback.format_exc()}")
            return None

