from django.utils.translation import gettext_noop as _

DROUGHTRISK_TYPES = {
    0:_('Abnormally Dry Condition'), 
    1:_('Moderate'), 
    2:_('Severe'), 
    3:_('Extreme'), 
    4:_('Exceptional')
}
DROUGHTRISK_TYPES_ORDER = [0,1,2,3,4]
DROUGHTLANDCOVER_TYPES = {
    "vineyards":"Vineyards",
    "fruit_trees":"Fruit Trees",
    "forest_shrub":"Forest & Shrub",
    "irrigated_agricultural_land":"Irrigated Agricultural Land",
    "build_up":"Build Up",
    "rangeland":"Rangeland",
    "rainfed":"Rainfed",    
}
DROUGHTLANDCOVER_TYPES_ORDER = [
    "vineyards",
    "fruit_trees",
    "forest_shrub",
    "irrigated_agricultural_land",
    "build_up",
    "rangeland",
    "rainfed",    
]
 