class Article(object):
    def __init__(
        self,
        document,
        area_id,
        area_type,
        area_category,
        original_image,
        coord_type,
        coords,
    ):
        self.document = document
        self.area_id = area_id
        self.area_type = area_type
        self.area_category = area_category
        self.original_image = original_image
        self.coord_type = coord_type
        self.coords = coords
