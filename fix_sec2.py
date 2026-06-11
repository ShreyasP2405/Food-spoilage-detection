from docx import Document
from lxml import etree
doc = Document('/Users/shreyaspatel/Desktop/food-spoilage-detector-main/report/Banana_Spoilage_Detection_Report_Final.docx')
NSMAP = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
sect_main = doc.sections[1]._sectPr
pgNumType_main = sect_main.find(f'{{{NSMAP["w"]}}}pgNumType')
if pgNumType_main is not None:
    pgNumType_main.set(f'{{{NSMAP["w"]}}}fmt', 'decimal')
else:
    pgNumType_main = etree.SubElement(sect_main, f'{{{NSMAP["w"]}}}pgNumType')
    pgNumType_main.set(f'{{{NSMAP["w"]}}}fmt', 'decimal')
    pgNumType_main.set(f'{{{NSMAP["w"]}}}start', '1')
doc.save('/Users/shreyaspatel/Desktop/food-spoilage-detector-main/report/Banana_Spoilage_Detection_Report_Final.docx')
