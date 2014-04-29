# -#-coding: utf-8 -#-

#metametadata fields

_prefix = 'metameta_'
default_value_copyright_statement = u'© default copyright statement 2014'


'''
PRESET_METAMETADATA = {
    Define preset record for meta metarecord
    Example:
    'owner':{'label': u'Owner', 'validator': 'not_empty', 'state': 'active', 'custom': False, 'presettable': False, 'readonly': False, 'field_type': 'text', 'default_value' : '', 'sort_order': 1},
    'copyright_statement':{'label': u'Copyright Statement', 'validator': 'not_empty', 'state': 'active', 'custom': False, 'presettable': True, 'readonly': True, 'field_type': 'single_choice', 'default_value' : default_value_copyright_statement, 'sort_order': 2},
}
'''
PRESET_METAMETADATA = {
}
def get_metameta_options_preset(vocabulary):
    '''
    Define preset options for meta metarecord which is single choice (dropdown list) field
    Must prepend "_prefix" to the dictionary key
    Example:
    return {
        _prefix+'copyright_statement': [
                default_value_copyright_statement,
                u'CC - Attribution-Noncommercial 3.0 Australia',
                u'CC - Attribution-Noncommercial-No Derivative Works 3.0 Australia',
                u'CC - Attribution-Noncommercial-Share Alike 3.0 Australia',
                u'CC - Attribution-No Derivative Works 3.0 Australia',
                u'CC - Attribution-Share Alike 3.0 Australia',
                u'Copyright',
                u'The BSD License',
                u'The MIT License'
                ],
        }[vocabulary]
    '''
    return {
        }[vocabulary]

