import xml.etree.ElementTree as ET

# Parse the source xml
src_xml = "Standard EV QA test cases.xml"
tree = ET.parse(src_xml)
root = tree.getroot()

# Create new elementtree with same root
Top = ET.Element(root.tag, root.attrib)

# For child other than report
for firstnode in root.findall("ichicsrmessageheader"):
	Top.append(firstnode)

i = 1
# Create and dump to the xml
for report in root.findall('safetyreport'):
	Top.append(report)
	data = ET.tostring(Top)
	OPxml = "Standard EV QA test case{}.xml".format(i)
	myfile = open(OPxml, "wb")
	myfile.write(data)
	myfile.close()
	i+=1
	Top.remove(report)
