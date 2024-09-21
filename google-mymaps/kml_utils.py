import xml.etree.ElementTree as ET

# Setting up KML namespace
KML_NAMESPACE = {"kml": "http://www.opengis.net/kml/2.2"}

# Registering namespace
ET.register_namespace("", "http://www.opengis.net/kml/2.2")

def color_to_kml(color):
    # Convert HEX color code to KML format (AABBGGRR)
    if color.startswith("#") and len(color) == 7:
        hex_color = color[1:]
    else:
        # Default to black if color format is incorrect
        hex_color = "000000"
    # Convert to AABBGGRR format
    hex_color = hex_color.lower()
    rr = hex_color[0:2]
    gg = hex_color[2:4]
    bb = hex_color[4:6]
    kml_color = "ff" + bb + gg + rr  # assuming full opacity
    return kml_color

def escape(s):
    if s:
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    else:
        return ""