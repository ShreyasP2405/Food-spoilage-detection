import subprocess
from pathlib import Path
from docx import Document
from lxml import etree

def convert_para(text):
    Path("temp.md").write_text(text)
    subprocess.run(["pandoc", "temp.md", "-o", "temp.docx"], check=True)
    doc = Document("temp.docx")
    for para in doc.paragraphs:
        return para._element
    return None

new_p = convert_para("The value of $x$ is $\\frac{1}{2}$.")
print(etree.tostring(new_p, pretty_print=True).decode())
