import base64
import os
import plotly.io as pio
import requests


convert_api_key = os.getenv("CONVERT_API_KEY")

class ReportGenerator:

    def __init__(self, co1, co2, strat, var, chart, chart_analysis, due):
        self.co1 = co1
        self.co2 = co2
        self.strat = strat
        self.var = var
        self.chart = chart
        self.chart_analysis = chart_analysis
        self.due = due

    
    def _fig_to_base64_img(self, fig, scale=2):
      img_bytes = pio.to_image(fig, format="png", scale=scale, engine="kaleido")
      b64 = base64.b64encode(img_bytes).decode()
      return f'<img src="data:image/png;base64,{b64}" style="width:100%;height:auto;border-radius:8px;">'



    def getHeader(self):
        return """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>M&A Report</title>
  <style>
    @page {
      size: A4;
      margin: 30mm 25mm 30mm 25mm;
    }

    body {
      font-family: 'Arial', sans-serif;
      color: #1e1e1e;
      background-color: white;
      margin: 0;
      padding: 0;
      line-height: 1.6;
      font-size: 12pt;
    }

    main {
      padding: 40px;
    }

    h1 {
      font-size: 24pt;
      color: #2f3542;
      border-bottom: 3px solid #2f3542;
      padding-bottom: 10px;
      margin-bottom: 30px;
    }

    h2 {
      font-size: 18pt;
      color: #2d3436;
      border-left: 6px solid #8b0906;
      padding-left: 12px;
      margin-top: 40px;
      margin-bottom: 15px;
    }

    h3 {
      font-size: 14pt;
      color: #636e72;
      margin-top: 25px;
      margin-bottom: 10px;
    }

    p {
      font-size: 11pt;
      margin: 8px 0;
    }

    ul {
      padding-left: 20px;
      margin-bottom: 20px;
    }

    li {
      font-size: 11pt;
      margin-bottom: 6px;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 20px;
      font-size: 10.5pt;
    }

    th, td {
      border: 1px solid #ced6e0;
      padding: 10px;
      text-align: left;
    }

    th {
      background-color: #f1f2f6;
      font-weight: bold;
    }

    .important {
      color: #c0392b;
      font-weight: bold;
    }

    .section-break {
      page-break-before: always;
    }
  </style>
</head>

<body>
  <main>

        """

    def getFooter(self):
        return """
        </main>
    </body>
</html>
        """
        
    def buildReportHTML(self):
        html = self.getHeader()
        html += self.co1
        html += self.co2
        html += self.strat
        html += self.var
        
        
        if self.chart_plan != "[]":
          #wrapping charts
          img_tags = "".join(self._fig_to_base64_img(fig) for fig in self.chart)
          html += f'''
          <div style="display:grid;grid-template-columns:repeat(2, 1fr);gap:10px;max-width:100%;">
          {img_tags}
          </div>
          '''
          html += self.chart_analysis

        html += self.due
        html += self.getFooter()
        return html
    
    def to_pdf(self):
        report_html = self.buildReportHTML()
        
        url = 'https://v2.convertapi.com/convert/html/to/pdf'
        headers = {
          'Authorization': f'Bearer {convert_api_key}',
        }
        files = {
          "File": ("report.html", report_html, "text/html")
        }
        data = {
          "FileName": "report.pdf"
        }
        response = requests.post(url, headers=headers, files=files, data=data)
        result = response.json()
        
        if "Files" not in result or not result["Files"]:
            raise Exception("Failed to convert HTML to PDF: " + str(result))
        
        b64_data = result["Files"][0]["FileData"]
        return base64.b64decode(b64_data)

    def to_html(self):
        return self.buildReportHTML()
