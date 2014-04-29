# -#-coding: utf-8 -#-
import datetime
import logging
import uuid
import ckan.plugins.toolkit as tk
import formencode.validators
import ckan
import pylons
import re
import pytz
import copy
from pytz import timezone
from ckan.lib.helpers import date_str_to_datetime
from ckan.common import _
from ckan import model
from sqlalchemy import Table, Column, types, ForeignKey
from ckan.model.meta import metadata
from ckan.model.types import make_uuid
from ckan.model import Session
from preset_metadata_fields import PRESET_METAMETADATA, get_metameta_options_preset
from ckan.logic import _import_module_functions, UnknownValidator, NotAuthorized, NotFound, get_action

from ckan.lib.navl.dictization_functions import StopOnError
from webhelpers.html import escape, HTML, literal, url_escape
from webhelpers.markdown import markdown
from webhelpers.text import wrap_paragraphs
import pylons.config as config
from ckan.logic.validators import object_id_validators
from ckan.lib.dictization import table_dictize
import ckan.logic.converters as converters
from model import Metameta, MetametaOpt 
import model as metameta_module

DATETIME_FORMAT = '%d-%m-%Y %H:%M:%S'

# find all tags but ignore < in the strings so that we can use it correctly
# in markdown
RE_MD_HTML_TAGS = re.compile('<[^><]*>')

_validators_cache = {}
_prefix = 'metameta_'
field_type_text = metameta_module.field_type_text
field_type_textarea = metameta_module.field_type_textarea
field_type_single_choice = metameta_module.field_type_single_choice

validator_not_empty = metameta_module.validator_not_empty
validator_ignore_missing = metameta_module.validator_ignore_missing
validator_range = metameta_module.validator_range

state_active = metameta_module.state_active
state_deleted = metameta_module.state_deleted

activity_assign_maintainer = 'assign maintainer'


def select_metametadata_for_org(org_id, metameta_id=None, active_only=True, withPrefix=False, sort_order_from=None, sort_order_to=None):
    """
     parameter: string
     parameter: metameta_id
     parameter: boolean withPrefix
     returns dict of metameta data
    """
    records = []

    if org_id is None or len(org_id.strip())==0:
        return records

    sql = "SELECT id, key, default_value, label, revision_id, state, validator, custom, presettable, readonly, field_type, min_value, max_value, sort_order, modified_date FROM metameta WHERE org_id = '" + org_id + "' "
    if metameta_id is not None:
        sql = sql + " AND id = '" + metameta_id +"'"
    if active_only:
        sql = sql + " AND state = '" + state_active +"'"
    if sort_order_from and sort_order_to:
        sql = sql + " AND sort_order BETWEEN %d and %d "%(int(sort_order_from), int(sort_order_to))
    elif sort_order_from:
        sql = sql + " AND sort_order >= %d "%(int(sort_order_from))
    elif sort_order_to:
        sql = sql + " AND sort_order <= %d "%(int(sort_order_to))
    sql = sql + "ORDER BY sort_order, presettable, custom, key ASC;"
    rows = Session.execute(sql)
    for row in rows:
        key = row['key']
        if not withPrefix:
            key = remove_prefix_key(key)
        records.append({
            'id': row['id'],
            'key': key,
            'default_value': row['default_value'],
            'label': row['label'],
            'revision_id': row['revision_id'],
            'state': row['state'],
            'validator': row['validator'],
            'custom': row['custom'],
            'presettable': row['presettable'],
            'readonly' :row['readonly'],
            'field_type': row['field_type'],
            'min_value': row['min_value'],
            'max_value': row['max_value'],
            'sort_order': row['sort_order'],
            'modified_date': row['modified_date'],
        })
    return records
def get_metameta_minmax(org_id, key):
    """
     parameter: org_id
     parameter: key
     returns dict of meta metadata
    """
    records = []

    if org_id is None or len(org_id.strip())==0:
        return records

    sql = "SELECT min_value, max_value FROM metameta WHERE org_id = '%s' AND key = '%s' AND state = '%s' LIMIT 1;"%(org_id, key, state_active)
    rows = Session.execute(sql)
    for row in rows:
        records.append({
            'min_value': row['min_value'],
            'max_value': row['max_value'],
        })
    return records
def get_owner_org_for_package(package_name):
    """
     parameter: package_name
    """
#     sql = "SELECT owner_org FROM package WHERE name = '%s' and state = 'active';"%(package_name)
#     rows = Session.execute(sql)
#     for row in rows:
#         return row['owner_org']
# 
#     return None

    pkg = ckan.model.Session.query(ckan.model.Package.owner_org).filter(ckan.model.Package.name == package_name).first()
    
    if pkg:
        return pkg.owner_org
    
    return None
    

def init_organization():
    #create metameta if not exists
    ids = get_organization_ids()
    for id in ids:
        init_metadata(id)

def create_search_key(key):
    _key = re.sub("[\W_-]+", "_", key).lower()
    if not has_prefix_key(_key):
        return add_prefix_key(_key)
    return _key

def init_metadata(org_id):

    #retrieve metameta records for org_id
    records = select_metametadata_for_org(org_id, metameta_id=None, active_only=False, withPrefix=True)
    sql = "INSERT INTO metameta(id, org_id, key, default_value, label, validator, state, custom, presettable, readonly, field_type, min_value, max_value, sort_order, modified_date) VALUES "
    update_count = 0;
    for key, values in PRESET_METAMETADATA.iteritems():
        if not key or len(key)==0:
            continue
        print '********key=%s*******'%(key)
        cmetamenta_key = add_prefix_key(key)

        #check whether key exists or not
        key_exists = False
        for record in records:
            if record['key']==cmetamenta_key:
                key_exists = True
                break

        if not key_exists:

            #check field type
            if values.get('field_type') == field_type_single_choice:

                presets = get_metameta_options_preset(cmetamenta_key)
                update_metameta_options(org_id, cmetamenta_key, presets)
            update_count += 1

            #create a record for a text field
            sql = sql + " ('%s', '%s', '%s', '%s', '%s', '%s', '%s', %r, %r, %r, '%s', %f, %f, %d, '%s'),"%(str(uuid.uuid4()), org_id, cmetamenta_key, values.get('default_value'), values.get('label'), values.get('validator'), values.get('state'), str(values.get('custom')), str(values.get('presettable')), str(values.get('readonly')), values.get('field_type'), 0.0, 0.0, int(values.get('sort_order')), datetime.datetime.utcnow().isoformat())

    if update_count > 0:
        sql = sql[:-1]
        sql = sql + ';'

        result = Session.execute(sql)
        Session.commit()

def update_metameta_table(org_id, metameta_id, data):
    """
     update metameta table with new values
    """

    errors = {}
    #key
    if not (data.has_key('key') and len(data['key'].strip())):
        #TODO validation
        errors.update({'key': _('%s field is required.'%('key'))})
        return errors
    key = data['key'].strip()

    #label: if not set, insert key
    if data.has_key('label') and len(data['label'].strip()):
        label = data['label'].strip()
    else:
        label = key.title()

    #convert non-alphanumeric to underscore
    key = create_search_key(key)
    if org_has_defaults(org_id, key, metameta_id):
        #TODO validation
        errors.update({'key': _('%s has been already used by the organization.'%(key))})
        return errors

    #readonly attribute
    readonly = str(data.get('readonly', False)).lower()=='True'.lower()

    #validator
    validator = data.get('validator', validator_not_empty)

    #default_value
    default_value = data.get('default_value', '')

    #field_type
    field_type = data.get('field_type', field_type_text)
    min_value = max_value = 0.0
    if field_type == field_type_text and validator == validator_range:
        min_value = data.get('min_value', 0.0)
        max_value = data.get('max_value', 0.0)

    update_sql = "UPDATE metameta SET key='%s', default_value='%s', label='%s', validator='%s', readonly=%r, field_type='%s', min_value=%f, max_value=%f, modified_date='%s' WHERE id ='%s' AND org_id='%s';"%(key, default_value, label, validator, readonly, field_type, float(min_value), float(max_value), datetime.datetime.utcnow().isoformat(), metameta_id, org_id)

    result = Session.execute(update_sql)
    Session.commit()
    return errors

def insert_metameta_table(org_id, data):
    """
     creates entries in metameta table for the organisation.
     value fields are null
    """
    errors = {}
    #key
    if not (data.has_key('key') and len(data['key'].strip())):
        #TODO validation
        errors.update({'key': _('%s field is required.'%('key'))})
        return errors
    key = data['key'].strip()

    #label: if not set, insert key
    if data.has_key('label') and len(data['label'].strip()):
        label = data['label'].strip()
    else:
        label = key.title()

    #convert non-alphanumeric to underscore
    key = create_search_key(key)
    if org_has_defaults(org_id, key):
        #TODO validation
        errors.update({'key': _('%s has been already used by the organization.'%(key))})
        return errors

    #readonly attribute
    readonly = str(data.get('readonly', False)).lower()=='True'.lower()

    #validator
    validator = data.get('validator', validator_not_empty)

    #default_value
    default_value = data.get('default_value', '')

    #field_type
    field_type = data.get('field_type', field_type_text)
    min_value = max_value = 0.0
    if field_type == field_type_text and validator == validator_range:
        min_value = data.get('min_value', 0.0)
        max_value = data.get('max_value', 0.0)

    sql = "INSERT INTO metameta(id, org_id, key, default_value, label, validator, state, custom, presettable, readonly, field_type, min_value, max_value, sort_order, modified_date) VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s', %r, %r, %r, '%s', %f, %f, (CASE WHEN (SELECT MAX(sort_order)+1 FROM metameta WHERE org_id='%s')>101 THEN (SELECT MAX(sort_order)+1 FROM metameta WHERE org_id='%s') ELSE 101 END), '%s');"%(str(uuid.uuid4()), org_id, key, default_value, label, validator, state_active, True, True, readonly, field_type, float(min_value), float(max_value), org_id, org_id, datetime.datetime.utcnow().isoformat())

    result = Session.execute(sql)
    Session.commit()
    return errors

def update_stat_metameta_table(org_id, metameta_id, state):
    """
     update stat on metameta table with new status
    """

    update_sql = "UPDATE metameta SET state='%s', modified_date='%s' WHERE id ='%s' AND org_id='%s';"%(state, datetime.datetime.utcnow().isoformat(), metameta_id, org_id)

    result = Session.execute(update_sql)
    Session.commit()

def select_metameta_options(org_id, key, option_value=None):
    """
     parameter: string org_id
     parameter: key
     parameter: option_value
     returns dict of metameta options
    """
    records = []
    sql = "SELECT option_value FROM metameta_options WHERE org_id = '%s' and key = '%s' "%(org_id, key)
    if option_value:
        sql = sql + "option_value = '%s' "%(option_value)
    sql = sql + " order by option_value ASC;"
    rows = Session.execute(sql)
    for row in rows:
        records.append(row['option_value'])
    return records

def insert_metameta_options(org_id, key, option_value):
    """
     creates entries in metameta options table for the organisation.
     value fields are null
    """
    sql = "INSERT INTO metameta_options(id, org_id, key, option_value, modified_date) VALUES ('%s', '%s', '%s', '%s', '%s');"%(str(uuid.uuid4()), org_id, key, option_value, datetime.datetime.utcnow().isoformat())

    result = Session.execute(sql)
    Session.commit()
    return

def remove_metameta_options(org_id, key, option_value=None):
    """
     creates entries in metameta options table for the organisation.
     value fields are null
    """
    sql = "DELETE FROM metameta_options WHERE org_id = '%s' AND key = '%s' "%(org_id, key)
    if option_value:
        sql = sql + " AND option_value='%s' "%(option_value)
    sql = sql + ";"
    result = Session.execute(sql)
    Session.commit()
    return

def org_has_defaults(org_id, key=None, metameta_id=None):
    """
     check if org has any entries in metameta table
     (it won't if no defaults have been set before)
     parameter: key
    """
    sql = "SELECT 1 FROM metameta WHERE org_id = '" + org_id + "'"
    if key is not None:
        sql = sql + " AND key = '" + key +"'"
    if metameta_id is not None:
        sql = sql + " AND id <> '" + metameta_id +"'"
    sql = sql + " LIMIT 1;"
    result = Session.execute(sql)

    if result.first():
        return True
    else:
        return False

def clear_validators_cache():
    _validators_cache.clear()

def update_metameta_options(org_id, key, newlist):
    """
    parameter: org_id
    parameter: key (with prefix) string
    """

    #make the list unique
    newsets = sorted(set(newlist))
    options = select_metameta_options(org_id, key)

    #add new options if not existing
    for newset in newsets:
        option_exist = False
        for option in options:
            if option==newset:
                option_exist = True
                break
        if not option_exist:
            insert_metameta_options(org_id, key, newset)
    #remove unused options if existing
    for option in options:
        newset_exist = False
        for newset in newsets:
            if option==newset:
                newset_exist = True
                break
        if not newset_exist:
            remove_metameta_options(org_id, key, option)

def _get_org_id(data):
    org_id = None
    
    if tk.request.method == "POST" and tk.request.POST.has_key("owner_org"):
        #when editing a dataset and the organisation is changed, set the org_id to the newly selected org
        org_id = tk.request.POST.get("owner_org", None)
    elif data is not None and data.has_key('group_id') and data['group_id'] is not None:
        #when creating new dataset, can get organization_id from group_id
        org_id = data['group_id']
    elif data is not None and data.has_key('organization') and data['organization'] is not None:
        #when updating the dataset, can get organization_id from organization.id
        organization = data["organization"]
        if organization and organization.has_key('is_organization') and organization['is_organization'] and organization.has_key('id'):
            org_id = organization['id']
    elif data is not None and data.has_key('owner_org') and data['owner_org'] is not None:
        #when creating new dataset that is not valid, can get organization_id from owner_org
        org_id = data['owner_org']
        
    #make sure owner_org is the same value
    if 'owner_org' in data and data['owner_org'] != org_id:
        data['owner_org'] = org_id
    if 'group_id' in data and data['group_id'] != org_id:
        data['group_id'] = org_id  
        
    #make sure extras are loaded properly
    if 'extras' in data:
        for e in data['extras']:
            data[e['key']] = e['value']
    
    if org_id is not None and len(org_id) > 0:
        return org_id
    
    return None

def metameta_get_data(data, sort_order_from=None, sort_order_to=None):
    org_id = _get_org_id(data)
    
    if org_id is not None:
        return select_metametadata_for_org(org_id, metameta_id=None, active_only=True, withPrefix=True, sort_order_from=sort_order_from, sort_order_to=sort_order_to)
    
    return []

def get_maintainers(data):
    #get organization id
    org_id = _get_org_id(data)

    if org_id is None:
        return []

    order_by = ('name')

    context = { 'model': model,
                'session': model.Session,
                'user': tk.c.user or tk.c.author,
                }
    data_dict = {
            'id': org_id,
            'object_type': 'user',
            }
    try:
        members = get_action('member_list')(context, data_dict)
    except NotAuthorized:
        tk.abort(401, _('Not authorized to see this page'))
    except NotFound:
        tk.abort(401, _('There is no registered member for this organization'))
    
    #make the current user on the top
    current_user_name = None
    member_names = []
    for member in members:
        user = model.User.get(member[0])    #user id
        if user.name == (tk.c.user or tk.c.author):
            current_user_name = user.name
        else:
            member_names.append(user.name)

    member_names.sort()
    member_options = []
    for member in member_names:
        member_options.append(
            {'value': member}
        )

    if current_user_name:
        member_options.insert(0, {'value': current_user_name})

    return member_options

"""
Validator Definition
"""
def metamenta_notes_length(key, data, errors, context):
    max_length = 255
    min_length = 1
    value = data.get(key)
    if len(value) < min_length or len(value) > max_length:
        errors[key].append(_('Description length should be between %d and %d'%(min_length, max_length)))
        raise StopOnError
    return value

def metameta_range(key, data, errors, context):
    raw_key = key
    if isinstance(key, tuple) or isinstance(key, list):
        key = key[0]
    org_id = get_organization_id()
    records = get_metameta_minmax(org_id, key)
    value = data.get(raw_key)
    try:
        for record in records:
            min_value = float(record["min_value"])
            max_value = float(record["max_value"])
            if float(value) < min_value or float(value) > max_value:
                errors[raw_key].append(_('Value range should be between %d and %d'%(min_value, max_value)))
                raise StopOnError
        return value
    except TypeError:
        errors[raw_key].append(_('Type Error: Numeric value is required.'))
        raise StopOnError
    except ValueError:
        errors[raw_key].append(_('Type Error: Numeric value is required.'))
        raise StopOnError

def get_validator(validator):
    '''Return a validator function by name.

    :param validator: the name of the validator function to return,
        eg. ``'package_name_exists'``
    :type validator: string

    :raises: :py:exc:`~ckan.plugins.toolkit.UnknownValidator` if the named
        validator is not found

    :returns: the named validator function
    :rtype: ``types.FunctionType``

    '''
    if  not _validators_cache:
        validators = _import_module_functions('ckan.lib.navl.validators')
        _validators_cache.update(validators)
        validators = _import_module_functions('ckan.logic.validators')
        _validators_cache.update(validators)
        validators = _import_module_functions('ckanext.metameta.helpers')
        _validators_cache.update(validators)
        _validators_cache.update({'OneOf': formencode.validators.OneOf})
    try:
        return _validators_cache[validator]
    except KeyError:
        raise UnknownValidator('Validator `%s` does not exist' % validator)

def append_validator(tag_string_schema, appended_validator):
    '''
        parameter tag_string_schema(list)
        parameter appended_validator(function)
    '''
    #append not_empty
    tag_string_schema.append(appended_validator)
    return tag_string_schema

def debug_print(data):
    if data is not None:
        print "****json****"
        #print [value for value in json.iteritems()]
        for key, value in data.iteritems():
            print "++++key++++"
            print key
            print "++++value++++"
            print value

def get_value(data, key, default_value):
    if data.has_key(key):
        value = data.get(key)
        if isinstance(value, basestring):
            return value
        else:
            return ""
    return default_value

def get_error(key, errors):
    if errors.has_key(key):
        return errors[key]
    return ""

def is_obsolete_and_empty(data, key, state):
    """
    when meta meta data is logically deleted and there is no asset with regard to this metameta data, return True
    """
    if state==state_deleted:
        if not (data.has_key(key) and isinstance(data.get(key), basestring)):
            return True
    return False

def has_prefix_key(key):
    if key:
        return key.startswith(_prefix)
    return key
def add_prefix_key(key):
    if key and not has_prefix_key(key):
        key = _prefix + key
    return key

def remove_prefix_key(key):
    if has_prefix_key(key):
        key = key[len(_prefix):]
    return key

def convert_error_keys(errors):
    prefix = 'Metameta '
    if errors:
        for key, error in errors.items():
            if key.lower().startswith(prefix.lower()):
                #remove old info
                errors.pop(key, None)
                key = key[len(prefix):]
                #add new info
                errors.update({key.capitalize(): error})
    return errors

def is_metameta_validator(validator):
    if validator:
        return validator.startswith(_prefix)
    return validator

def validator_label(validator):
    return get_validators()[validator]

def get_validators():
    return {
        validator_not_empty: 'Not Empty',
        validator_ignore_missing: 'Allow Empty',
        validator_range: 'Specify Range',
        }


def get_readonly():
    return {
        True: 'Read Only',
        False: 'Editable',
        }

def is_required(validator):
    return validator!=validator_ignore_missing

def is_text_field(field_type):
    return field_type==field_type_text
    
def is_textarea_field(field_type):
    return field_type==field_type_textarea
    
def is_dropdown_field(field_type):
    return field_type==field_type_single_choice

def field_type_label(field_type):
    return get_field_types()[field_type]

def get_field_types():
    return {
        field_type_text: 'Text',
        field_type_textarea: 'Text Area',
        field_type_single_choice: 'Single Choice',
        }

def is_active(state):
    return state==state_active
    
def is_oneline_textarea():
    #get config
    return config.get('ckan.oneline_textarea', False)

def is_maintainer_notification():
    #get config
    return config.get('ckan.maintainer_notification', False)

def get_organization_ids():
    #user = tk.get_action('get_site_user')({'ignore_auth': True}, {})
    context = {'user': pylons.c.user}
    data_dict = {'permission': 'edit_group'}
    organization_list = tk.get_action('organization_list_for_user')(context, data_dict)
    ids=[]
    for organization in organization_list:
        #TODO existance check
        if organization['type']=='organization' and organization['is_organization'] and organization.has_key('id'):
            ids.append(organization['id'])
    return ids
def get_organization_id():
    org_id = None
    if tk.request.method == "POST" and tk.request.POST.has_key("owner_org"):
        org_id = tk.request.POST.get("owner_org", None)
        return org_id
    elif tk.request.method == "GET" and tk.request.GET.has_key("owner_org"):
        org_id = tk.request.GET.get("owner_org", None)
    if org_id:
        return org_id
    
    if tk.c.pkg_dict and 'owner_org' in tk.c.pkg_dict:
        return tk.c.pkg_dict['owner_org']

    #user = tk.get_action('get_site_user'){('ignore_auth': True}, {})
    context = {'model': model, 'session': Session, 'user': pylons.c.user}
    
    # organization id
    owner_org = get_owner_org_for_package( tk.c.id)
    return owner_org

def markdown_wrap(text, extract_length=190):
    ''' return the plain text representation of markdown encoded text.  That
    is the texted without any html tags.  If extract_length is 0 then it
    will not be truncated.'''
    if (text is None) or (text.strip() == ''):
        return ''
    plain = RE_MD_HTML_TAGS.sub('', markdown(text))
    if not extract_length or len(plain) < extract_length:
        return literal(plain)
    return literal(unicode(wrap_paragraphs(plain, width=extract_length)))

def metameta_convert_to_local_timestamp(str_timestamp):
    if not str_timestamp:
        return ''
    #calculate past time by considering utc
    utc_datetime = date_str_to_datetime(str_timestamp)

    #get local time
    tz_code = config.get('ckan.timezone', 'Australia/Melbourne')
    local = timezone(tz_code)

    if _is_naive(utc_datetime):
        utc_datetime = _make_aware(utc_datetime, pytz.utc)
    local_datetime = utc_datetime.astimezone(local)

    return local_datetime.strftime(DATETIME_FORMAT)

def _is_aware(value):
    """
    Determines if a given datetime.datetime is aware.

    The logic is described in Python's docs:
    http://docs.python.org/library/datetime.html#datetime.tzinfo
    """
    return value.tzinfo is not None and value.tzinfo.utcoffset(value) is not None

def _is_naive(value):
    """
    Determines if a given datetime.datetime is naive.

    The logic is described in Python's docs:
    http://docs.python.org/library/datetime.html#datetime.tzinfo
    """
    return value.tzinfo is None or value.tzinfo.utcoffset(value) is None

def _make_aware(value, timezone):
    """
    Makes a naive datetime.datetime in a given time zone aware.
    """
    if hasattr(timezone, 'localize'):
        # available for pytz time zones
        return timezone.localize(value, is_dst=None)
    else:
        # may be wrong around DST changes
        return value.replace(tzinfo=timezone)

def _make_naive(value, timezone):
    """
    Makes an aware datetime.datetime naive in a given time zone.
    """
    value = value.astimezone(timezone)
    if hasattr(timezone, 'normalize'):
        # available for pytz time zones
        value = timezone.normalize(value)
    return value.replace(tzinfo=None)

def retrieve_packages(owner_org, state=state_active, search_key=None):

    p_info = _retrieve_package_info(owner_org, state, search_key)
    package_list = []
    for p in p_info:
        context = { 'model': model,
                    'session': model.Session,
                    'user': tk.c.user or tk.c.author,
                    'auth_user_obj': model.User.get(tk.c.user or tk.c.author)
                    }

        #retrieve package data as activity_data
        try:
            package =  tk.get_action('package_show')(context, {'id': p.get('package_id'), 'ignore_auth': True})
            package_list.append(package)
        except NotAuthorized:
            tk.abort(401, _('Not authorized to see this page'))
        except NotFound:
            tk.abort(401, _('There is no registered member for this organization'))
            continue
    return package_list

def _retrieve_package_info(owner_org, state=state_active, search_key=None):
    if not search_key:
        search_key = tk.c.q  #search query

    sql = "SELECT P.id AS package_id, P.name AS package_name "
    sql = sql + "FROM package P " 
    sql = sql + "LEFT OUTER JOIN \"group\" G ON P.owner_org = G.id AND G.is_organization IS TRUE "  #only organization
    sql = sql + "LEFT OUTER JOIN package_extra extra ON extra.package_id = P.id "
    sql = sql + "LEFT OUTER JOIN package_tag ptag ON ptag.package_id = P.id "
    sql = sql + "LEFT OUTER JOIN tag T ON T.id = ptag.tag_id "
    sql = sql + "WHERE P.owner_org = '%s' AND P.state = '%s' "%(owner_org, state)
    if search_key and len(search_key):    
        sql = sql + " AND (P.name LIKE '%" + search_key + "%' OR "
        sql = sql + " P.name LIKE '%" + search_key + "%' OR "
        sql = sql + " P.title LIKE '%" + search_key + "%' OR "
        sql = sql + " P.notes LIKE '%" + search_key + "%' OR "
        sql = sql + " P.license_id LIKE '%" + search_key + "%' OR "
        sql = sql + " P.author LIKE '%" + search_key + "%' OR "
        sql = sql + " P.author_email LIKE '%" + search_key + "%' OR "
        sql = sql + " P.maintainer LIKE '%" + search_key + "%' OR "
        sql = sql + " P.maintainer_email LIKE '%" + search_key + "%' OR "
        sql = sql + " extra.value LIKE '%" + search_key + "%' OR "
        sql = sql + " T.name LIKE '" + search_key + "' ) "
    sql = sql + "GROUP BY P.id, P.name "
    sql = sql + "ORDER BY P.name ASC "
    rows = model.Session.execute(sql).fetchall()
    package_list = []
    for row in rows:
        package_list.append({
            'package_id':row['package_id'],
            'package_name':row['package_name'],
            })
    return package_list

def topoffwith(data, topoff):
    #sort by topping topoff on the data

    if not data or not topoff or not len(topoff):
        return data

    if isinstance(data, list) or isinstance(data, tuple):
        data = [datum for datum in data if datum != topoff]
        data.insert(0, topoff)
    return data

def follow_dataset(data_dict, maintainer):
    #create user
    context = {'model': model,
        'session': ckan.model.Session,
        'user': maintainer.name,
        'ignore_auth': True}
    if not tk.get_action('am_following_dataset')(context, data_dict):
        return tk.get_action('follow_dataset')(context, data_dict)

def activity_stream_string_assign_maintainer(context, activity):
    return tk._("{user} has been assigned to the maintainer of {dataset}")

def notify_maintainer(pkg_dict, maintainer):

    if not is_maintainer_notification():
        return

    object_id_validators[activity_assign_maintainer] = tk.get_validator('user_id_exists')

    context = {'model': model,
        'session': ckan.model.Session,
        'user': tk.c.user or tk.c.author,
        'ignore_auth': True}
    
    admin_user = tk.get_action('get_site_user')(context,{})
    dataset_context = {
        'model': model,
        'session': ckan.model.Session,
        'user': tk.c.user or tk.c.author,
        'api_version': 3,
        'for_edit': True,
        'auth_user_obj': admin_user,
        'ignore_auth': True
        }
    activity_data = {}
    activity_object_id = pkg_dict.get('id')
    if not activity_object_id:
        return

    #retrieve package data as activity_data
    try:
        activity_data =  tk.get_action('package_show')(dataset_context, {'id': activity_object_id})
    except NotFound:
        #at new creation of the package, the data has not been existing in the DB, so retrieve the data from pkg_dict and sanitize it
        activity_data = copy.deepcopy(pkg_dict)
        _sanitize_dict(activity_data) #sanitize

    maintainer_dict = table_dictize(maintainer, context)

    #add item into the creators activity stream indicating the maintainer has been assigned
    activity_dict = {
        'user_id': tk.c.user or tk.c.author,
        'object_id': maintainer.id,
        'data' : { 'dataset': activity_data,  'user': maintainer_dict },
        'activity_type': activity_assign_maintainer,
    }
    tk.get_action('activity_create')(context, activity_dict)
    print 'done'

def _sanitize_dict(dictionary):
    for k,v in dictionary.items():
        if isinstance(v, dict):
            _sanitize_dict(v)
        elif isinstance(v, list):
            for i in v:
                _sanitize_dict(i)
        if type(v) is datetime.datetime:
            del dictionary[k] #delete this since this contains unserialized datetime object

