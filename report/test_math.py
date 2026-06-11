import subprocess
from pathlib import Path
from docx import Document
from lxml import etree

def latex_to_omml(latex_str, is_inline=False):
    # write to temp md
    md_text = f"${latex_str}$" if is_inline else f"$${latex_str}$$"
    Path("temp.md").write_text(md_text)
    # convert to docx
    subprocess.run(["pandoc", "temp.md", "-o", "temp.docx"], check=True)
    # read docx
    doc = Document("temp.docx")
    for para in doc.paragraphs:
        # find omml
        ns = {'m': 'http://schemas.openxmlformats.org/officeDocument/2006/math'}
        math_elements = para._element.findall('.//m:oMath', ns)
        if math_elements:
            return math_elements[0]
    return None

omml = latex_to_omml("x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}")
print(etree.tostring(omml, pretty_print=True).decode())
