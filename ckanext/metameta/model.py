import ckan
import sqlalchemy
from datetime import datetime
from sqlalchemy import orm, Table, Column, types, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from ckan.model.meta import metadata
from ckan.model.types import make_uuid
from ckan.model import domain_object, meta


field_type_text = 'text'
field_type_textarea = 'textarea'
field_type_single_choice = 'single_choice'

validator_not_empty = 'not_empty'
validator_ignore_missing = 'ignore_missing'
validator_range = 'metameta_range'

state_active = 'active'
state_deleted = 'deleted'



metameta_table = Table('metameta', metadata,
            Column('id', types.UnicodeText, primary_key=True, default=make_uuid),
            Column('org_id', types.UnicodeText, nullable = True),
            Column('key', types.UnicodeText, default=u''),
            Column('default_value', types.UnicodeText, default=u''),
            Column('label', types.UnicodeText, default=u''),
            Column('revision_id', types.UnicodeText, nullable = True),
            Column('state', types.String, default=state_active),
            Column('validator', types.String, default=validator_ignore_missing),
            Column('custom', types.Boolean, default=True),
            Column('presettable', types.Boolean, default=True),
            Column('readonly', types.Boolean, default=True),
            Column('field_type', types.UnicodeText, default=u'text'),
            Column('min_value', types.Float, default=0.0),
            Column('max_value', types.Float, default=0.0),
            Column('sort_order', types.Integer, default=0),
            Column('modified_date', types.DateTime, default=datetime.utcnow),
        )

metameta_options_table = Table('metameta_options', metadata,
        Column('id', types.UnicodeText, primary_key=True, default=make_uuid),
        Column('org_id', types.UnicodeText),
        Column('key', types.UnicodeText, default=u''),
        Column('option_value', types.UnicodeText, default=u''),
        Column('modified_date', types.DateTime, default=datetime.utcnow),
    )


class Metameta(domain_object.DomainObject):
    def __init__(self, org_id, key, label, default_value, revision_id, state, validator, custom, presettable, readonly, field_type, sort_order, min_value=0.0, max_value=0.0):
        self.id = make_uuid()
        self.org_id = org_id
        self.key = key
        self.default_value = default_value
        self.label = label
        self.revision_id = revision_id
        self.state = state
        self.validator = validator
        self.custom = custom
        self.presettable = presettable
        self.readonly = readonly
        self.field_type = field_type
        self.sort_order = sort_order
        self.min_value = min_value
        self.max_value = max_value
        self.modified_date = datetime.datetime.now()

    @classmethod
    def by_metameta_org_id_and_key(cls, org_id, key=None):
        query = ckan.model.Session.query(cls)
        query = query+query.filter_by(org_id = org_id)
        if key:
            query = query+query.filter_by(key = key)
        return query.all()

meta.mapper(Metameta, metameta_table)

class MetametaOpt(domain_object.DomainObject):
    def __init__(self, org_id, key, option_value):
        self.id = make_uuid()
        self.org_id = org_id
        self.key = key
        self.option_value = option_value
        self.modified_date = datetime.datetime.now()

    @classmethod
    def by_metameta_org_id_and_key(cls, org_id, key):
        return ckan.model.Session.query(cls) \
                .filter_by(org_id = org_id) \
                .filter_by(key = key) \
                .all()

meta.mapper(MetametaOpt, metameta_options_table)

def create_metameta_table():
    """
     create the metameta table from schema
    """
    #create the table in the database
    metameta_table.create(checkfirst=True)

def create_metameta_options_table():
    """
     create the metameta_options table from schema
    """
    #create the table in the database
    metameta_options_table.create(checkfirst=True)


