import os
import xml.etree.ElementTree as ET
from kml_utils import color_to_kml, escape, KML_NAMESPACE
import argparse
import config


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Combine KML files into a single map.")
    parser.add_argument(
        "--coloring-mode",
        choices=["user", "point"],
        default="user",
        help="Coloring mode: 'user' or 'point'.",
    )

    parser.add_argument(
        "--section",
        required=True,
        help="Section to process from KML files.",
    )

    args = parser.parse_args()

    coloring_mode = args.coloring_mode
    section_to_process = args.section

    if section_to_process not in config.SECTION_POINTS:
        print(f"Section '{section_to_process}' is not recognized.")
        print(f"Available sections: {', '.join(config.SECTION_POINTS.keys())}")
        exit()

    expected_count = config.SECTION_POINTS[section_to_process]

    script_directory = os.path.dirname(os.path.abspath(__file__))
    kml_directory = os.path.join(script_directory, "sample")

    if not os.path.exists(kml_directory):
        print(f"Directory {kml_directory} not found.")
        exit()

    kml_files = [
        os.path.join(kml_directory, f)
        for f in os.listdir(kml_directory)
        if f.endswith(".kml")
    ]

    data = []
    user_color_map = {}
    point_color_map = {}

    # Process each KML file
    for kml_file in kml_files:
        is_valid = True  # Flag to check if the KML file is valid
        validation_errors = []  # List to collect validation errors

        if not os.path.exists(kml_file):
            print(f"File {kml_file} not found. Please check the file path.")
            continue

        # Get the user name from the file name
        base_name = os.path.splitext(os.path.basename(kml_file))[0]
        user_name = base_name  # Assuming the file name is 'Name Lastname.kml'

        # Parse the KML file
        try:
            tree = ET.parse(kml_file)
            root = tree.getroot()
        except ET.ParseError as e:
            print(f"Error parsing {kml_file}: {e}")
            continue

        # Validate required section
        # Construct the folder name
        folder_name = f"{section_to_process}: {user_name}"
        # Search for the folder
        folder = None
        folders = root.findall(".//kml:Folder", KML_NAMESPACE)
        for f in folders:
            name_element = f.find("kml:name", KML_NAMESPACE)
            if name_element is not None and name_element.text.strip().lower() == folder_name.strip().lower():
                folder = f
                break

        if not folder:
            is_valid = False
            validation_errors.append(f"Missing section '{folder_name}' in {kml_file}")
        else:
            # Get placemarks in the folder
            placemarks = folder.findall(".//kml:Placemark", KML_NAMESPACE)
            placemark_names = [
                pm.find("kml:name", KML_NAMESPACE).text
                for pm in placemarks
                if pm.find("kml:name", KML_NAMESPACE) is not None
            ]

            # Expected placemark names
            expected_placemark_names = [str(i) for i in range(expected_count)]

            # Check if all expected placemarks are present
            if sorted(placemark_names) != sorted(expected_placemark_names):
                is_valid = False
                missing = set(expected_placemark_names) - set(placemark_names)
                extra = set(placemark_names) - set(expected_placemark_names)
                error_message = f"In section '{folder_name}' in {kml_file}:"

                if missing:
                    error_message += f" Missing placemarks {', '.join(sorted(missing))}."
                if extra:
                    error_message += f" Unexpected placemarks {', '.join(sorted(extra))}."
                validation_errors.append(error_message)

        if not is_valid:
            print(f"KML file '{kml_file}' is invalid:")
            for error in validation_errors:
                print(f"- {error}")
            print("This file will be skipped.\n")
            continue  # Skip processing this file

        # Assign a color to the user if not already assigned
        if user_name not in user_color_map:
            color_index = len(user_color_map) % len(config.USER_COLORS)
            user_color_map[user_name] = config.USER_COLORS[color_index]

        # Process the specified section
        # Construct the folder name
        folder_name = f"{section_to_process}: {user_name}"
        # Search for the folder
        folder = None
        folders = root.findall(".//kml:Folder", KML_NAMESPACE)
        for f in folders:
            name_element = f.find("kml:name", KML_NAMESPACE)
            if name_element is not None and name_element.text.strip().lower() == folder_name.strip().lower():
                folder = f
                break

        if not folder:
            continue  # This should not happen due to validation, but added for safety

        # Extract placemarks
        placemarks = folder.findall(".//kml:Placemark", KML_NAMESPACE)
        for placemark in placemarks:
            # Get the point name
            point_name_element = placemark.find("kml:name", KML_NAMESPACE)
            if point_name_element is not None:
                point_name = point_name_element.text
            else:
                point_name = "Unknown"

            # Assign a color to the point name if not already assigned
            if point_name not in point_color_map:
                color_index = len(point_color_map) % len(config.POINT_COLORS)
                point_color_map[point_name] = config.POINT_COLORS[color_index]

            # Get coordinates
            point = placemark.find(".//kml:Point", KML_NAMESPACE)
            if point is not None:
                coordinates_element = point.find("kml:coordinates", KML_NAMESPACE)
                if coordinates_element is not None:
                    coordinates = coordinates_element.text.strip()
                else:
                    coordinates = ""
            else:
                coordinates = ""

            # Save data
            data.append({
                "user_name": user_name,
                "point_name": point_name,
                "coordinates": coordinates,
                "section_name": section_to_process,
            })

    # Check if there is data to process
    if not data:
        print("No valid data to process.")
        exit()

    # Create the root KML element
    kml = ET.Element("{http://www.opengis.net/kml/2.2}kml")

    # Create the Document element
    document = ET.SubElement(kml, "Document")

    # Add the document name (set to the section name)
    doc_name = ET.SubElement(document, "name")
    doc_name.text = section_to_process

    # Create a single layer with placemarks
    for entry in data:
        placemark = ET.SubElement(document, "Placemark")
        name_element = ET.SubElement(placemark, "name")
        name_element.text = escape(entry["point_name"])

        # Add description with the user's name
        description_element = ET.SubElement(placemark, "description")
        description_element.text = f"User: {escape(entry['user_name'])}"

        # Embed style directly in the Placemark
        style = ET.SubElement(placemark, "Style")
        iconstyle = ET.SubElement(style, "IconStyle")
        iconstyle_color = ET.SubElement(iconstyle, "color")

        # Choose coloring mode based on command-line argument
        if coloring_mode == "user":
            color_code = user_color_map[entry["user_name"]]
        elif coloring_mode == "point":
            color_code = point_color_map[entry["point_name"]]
        else:
            color_code = "#000000"  # default to black

        iconstyle_color.text = color_to_kml(color_code)

        # Set icon style (can be customized as needed)
        icon = ET.SubElement(iconstyle, "Icon")
        href = ET.SubElement(icon, "href")
        href.text = "https://www.gstatic.com/mapspro/images/stock/503-wht-blank_maps.png"

        # Add coordinates
        point_element = ET.SubElement(placemark, "Point")
        coordinates_element = ET.SubElement(point_element, "coordinates")
        coordinates_element.text = entry["coordinates"]

    # Write the KML to file
    output_file = os.path.join(script_directory, "combined_map.kml")
    tree = ET.ElementTree(kml)
    tree.write(output_file, encoding="utf-8", xml_declaration=True)

    print(f"Combined map saved to file: {output_file}")


if __name__ == "__main__":
    main()