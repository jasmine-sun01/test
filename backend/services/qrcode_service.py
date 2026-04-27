"""二维码生成 & PDF 导出"""
import os
import qrcode
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from config import SERVER_HOST, QRCODE_DIR, EXPORT_DIR


def generate_qrcode(item_id: int, item_code: str) -> str:
    """生成二维码图片，返回保存路径"""
    os.makedirs(QRCODE_DIR, exist_ok=True)

    url = f"http://{SERVER_HOST}/items/{item_id}"

    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    path = os.path.join(QRCODE_DIR, f"{item_code}.png")
    img.save(path)
    return path


def generate_qrcode_pdf(items: list) -> str:
    """生成包含多个物品二维码的 PDF
    
    items: list of dicts with keys: qrcode_path, name, code
    """
    os.makedirs(EXPORT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    pdf_path = os.path.join(EXPORT_DIR, f"qrcodes_{timestamp}.pdf")

    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4
    cols, rows = 2, 4  # 每页 2列 x 4行
    cell_w = width / cols
    cell_h = height / rows

    for i, item in enumerate(items):
        page_idx = i % (cols * rows)
        if page_idx == 0 and i > 0:
            c.showPage()

        col = page_idx % cols
        row = page_idx // cols

        x = col * cell_w + 20
        y = height - (row + 1) * cell_h + 20

        # 画二维码图片
        qr_path = item.get("qrcode_path") or ""
        if os.path.exists(qr_path):
            c.drawImage(qr_path, x, y + 30, 80, 80)

        # 物品名称
        c.setFont("Helvetica", 10)
        c.drawString(x, y + 15, item.get("name", ""))
        # 物品编号
        c.setFont("Helvetica", 8)
        c.drawString(x, y, item.get("code", ""))

    c.save()
    return pdf_path
