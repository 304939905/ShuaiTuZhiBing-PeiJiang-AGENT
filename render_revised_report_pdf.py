from pathlib import Path
import sys

import pypdfium2 as pdfium


PDF = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(r"D:\Desktop\shandou\_qa_s1_report_revised\S1_report_revised.pdf")
OUT = PDF.parent


def main() -> None:
    pdf = pdfium.PdfDocument(str(PDF))
    scale = 150 / 72
    for index in range(len(pdf)):
        page = pdf[index]
        image = page.render(scale=scale).to_pil()
        image.save(OUT / f"page-{index + 1}.png")
        page.close()
    print(len(pdf))


if __name__ == "__main__":
    main()
