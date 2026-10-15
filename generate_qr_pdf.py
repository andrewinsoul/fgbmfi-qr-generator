
import os
from pathlib import Path

import qrcode
from PIL import Image
from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"
LOGO_FILE = BASE_DIR / "logo.png"
OUTPUT_PDF = BASE_DIR / "FGBMFI_Connect_Permanent_CheckIn_QR.pdf"
TEMP_QR = BASE_DIR / ".checkin_qr_temp.png"


def load_env_file(path: Path) -> None:
    """Load simple KEY=VALUE entries without printing secrets."""
    if not path.is_file():
        raise FileNotFoundError(
            f"Environment file not found: {path}"
        )

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        # Preserve variables already provided by the shell.
        if key and key not in os.environ:
            os.environ[key] = value


def generate_qr(payload: str, output: Path) -> None:
    """Generate a high-error-correction QR code."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=12,
        border=4,
    )

    qr.add_data(payload)
    qr.make(fit=True)

    image = qr.make_image(
        fill_color="#2E165F",
        back_color="white",
    ).convert("RGB")

    image.save(output)


def generate_pdf() -> None:
    load_env_file(ENV_FILE)

    token = os.environ.get("CHECK_IN_QR_TOKEN", "").strip()

    if not token:
        raise ValueError(
            "CHECK_IN_QR_TOKEN is missing. "
            "Set it in .env or your environment."
        )

    if not LOGO_FILE.is_file():
        raise FileNotFoundError(
            f"Logo not found at {LOGO_FILE}. "
            "Place the fellowship logo there."
        )

    # Generate the QR code using the exact backend token.
    generate_qr(token, TEMP_QR)

    try:
        page_width, page_height = A4

        # FGBMFI Connect brand palette
        purple = HexColor("#2E165F")
        purple_mid = HexColor("#5630A5")
        gold = HexColor("#D9B45B")
        ink = HexColor("#251A3D")
        muted = HexColor("#6E6680")
        pale = HexColor("#F6F2FF")
        border = HexColor("#E6DDF8")
        background = HexColor("#FBF9FF")

        pdf = canvas.Canvas(str(OUTPUT_PDF), pagesize=A4)
        pdf.setTitle(
            "FGBMFI Connect - Permanent Check-In QR"
        )
        pdf.setAuthor("FGBMFI Connect")

        # Page background
        pdf.setFillColor(background)
        pdf.rect(
            0, 0, page_width, page_height,
            stroke=0, fill=1,
        )

        # Branded header
        pdf.setFillColor(purple)
        pdf.rect(
            0, page_height - 172,
            page_width, 172,
            stroke=0, fill=1,
        )

        pdf.setFillColor(gold)
        pdf.rect(
            0, page_height - 178,
            page_width, 6,
            stroke=0, fill=1,
        )

        # Logo panel
        panel_x = 54
        panel_y = page_height - 144
        panel_width = 78
        panel_height = 78

        pdf.setFillColor(white)
        pdf.roundRect(
            panel_x, panel_y,
            panel_width, panel_height,
            16, stroke=0, fill=1,
        )

        with Image.open(LOGO_FILE) as source_logo:
            logo = source_logo.convert("RGBA")

        logo.thumbnail(
            (68, 68),
            Image.Resampling.LANCZOS,
        )

        pdf.drawImage(
            ImageReader(logo),
            panel_x + (panel_width - logo.width) / 2,
            panel_y + (panel_height - logo.height) / 2,
            width=logo.width,
            height=logo.height,
            mask="auto",
        )

        # Fellowship name and tagline
        pdf.setFillColor(white)
        pdf.setFont("Helvetica-Bold", 21)
        pdf.drawString(
            148, page_height - 91,
            "FGBMFI CONNECT",
        )

        pdf.setFillColor(HexColor("#E7DDFB"))
        pdf.setFont("Helvetica", 10.5)
        pdf.drawString(
            149, page_height - 113,
            "HIS BANNER OVER US IS LOVE.",
        )

        # Main heading
        pdf.setFillColor(ink)
        pdf.setFont("Helvetica-Bold", 25)
        pdf.drawCentredString(
            page_width / 2,
            page_height - 226,
            "Fellowship Check-In",
        )

        pdf.setFillColor(muted)
        pdf.setFont("Helvetica", 11)
        pdf.drawCentredString(
            page_width / 2,
            page_height - 248,
            "Scan the official QR code below to record your attendance.",
        )

        # QR card
        card_x = 115
        card_y = 185
        card_width = page_width - 230
        card_height = 340

        pdf.setFillColor(white)
        pdf.setStrokeColor(border)
        pdf.setLineWidth(1)
        pdf.roundRect(
            card_x, card_y,
            card_width, card_height,
            22, stroke=1, fill=1,
        )

        qr_size = 250
        qr_x = (page_width - qr_size) / 2
        qr_y = card_y + 58

        pdf.drawImage(
            str(TEMP_QR),
            qr_x, qr_y,
            width=qr_size,
            height=qr_size,
            preserveAspectRatio=True,
            mask="auto",
        )

        pdf.setFillColor(purple_mid)
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawCentredString(
            page_width / 2,
            card_y + 31,
            "SCAN TO CHECK IN",
        )

        # Instructions
        pdf.setFillColor(pale)
        pdf.roundRect(
            58, 111,
            page_width - 116, 48,
            12, stroke=0, fill=1,
        )

        pdf.setFillColor(purple)
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawCentredString(
            page_width / 2,
            140,
            "HOW TO CHECK IN",
        )

        pdf.setFillColor(ink)
        pdf.setFont("Helvetica", 9.5)
        pdf.drawCentredString(
            page_width / 2,
            124,
            "Open FGBMFI Connect  •  Choose Scan QR  •  Wait for confirmation",
        )

        # Footer
        pdf.setFillColor(gold)
        pdf.roundRect(
            58, 77,
            page_width - 116, 3,
            1.5, stroke=0, fill=1,
        )

        pdf.setFillColor(muted)
        pdf.setFont("Helvetica", 8.5)
        pdf.drawCentredString(
            page_width / 2,
            60,
            "Use the official FGBMFI Connect app. "
            "Check-in requires an open meeting session.",
        )

        pdf.setFillColor(purple)
        pdf.setFont("Helvetica-Bold", 8)
        pdf.drawCentredString(
            page_width / 2,
            43,
            "FGBMFI CONNECT",
        )

        pdf.save()

        print(f"PDF generated successfully: {OUTPUT_PDF}")

    finally:
        # Remove the temporary QR image even if PDF generation fails.
        TEMP_QR.unlink(missing_ok=True)


if __name__ == "__main__":
    try:
        generate_pdf()
    except (ValueError, FileNotFoundError) as error:
        raise SystemExit(f"Error: {error}") from error
