from django.utils.translation import gettext_noop as _

DROUGHTRISK_TYPES = {
    0:_('Abnormally Dry Condition'), 
    1:_('Moderate'), 
    2:_('Severe'), 
    3:_('Extreme'), 
    4:_('Exceptional')
}
DROUGHTRISK_TYPES_ORDER = [0,1,2,3,4]
 