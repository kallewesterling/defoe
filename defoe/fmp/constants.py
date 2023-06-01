import mimetypes

# Image types
mimetypes.init()
IMAGE_TYPES = [
    type
    for type, desc in mimetypes.types_map.items()
    if desc.split("/")[0] == "image"
]

# For matching
FUZZ_METHOD = "token_set_ratio"
MIN_RATIO = 85

# Colours
AUTO_FILL = (200, 100, 0)
AUTO_OPACITY = 0.25

NAMESPACES = {
    "mods": "http://www.loc.gov/mods/v3",
    "mets": "http://www.loc.gov/METS/",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    "premis": "info:lc/xmlns/premis-v2",
    "dcterms": "http://purl.org/dc/terms/",
    "fits": "http://hul.harvard.edu/ois/xml/ns/fits/fits_output",
    "xlink": "http://www.w3.org/1999/xlink",
}
