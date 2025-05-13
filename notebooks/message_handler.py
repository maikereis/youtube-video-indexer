import xml.etree.ElementTree as ET

def handle_response(xml_data: str):
    try:
        # Parse the XML content
        root = ET.fromstring(xml_data)

        # Define namespaces
        namespaces = {
            "atom": "http://www.w3.org/2005/Atom",
            "yt": "http://www.youtube.com/xml/schemas/2015",
        }

        # Find the entry element
        entry = root.find("atom:entry", namespaces)
        if entry is not None:
            video_id = entry.find("yt:videoId", namespaces).text
            channel_id = entry.find("yt:channelId", namespaces).text
            title = entry.find("atom:title", namespaces).text
            published_at = entry.find("atom:published", namespaces).text
            updated_at = entry.find("atom:updated", namespaces).text

            # store in valkey queue
            #.....

            # Process the extracted information as needed
            print(f"New video uploaded: {title} (ID: {video_id}) on channel {channel_id}")
            print(f"Published at: {published_at}, Updated at: {updated_at}")
        else:
            print("No entry found in the feed.")

    except ET.ParseError as e:
        print(f"Failed to parse XML: {e}")