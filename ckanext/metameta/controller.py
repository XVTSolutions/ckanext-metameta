# -#-coding: utf-8 -#-
import ckan
import pylons
from ckan.lib.base import BaseController
import ckan.plugins as plugins
from ckan.model import Session
import ckan.lib.helpers as h
from ckan.logic.converters import convert_group_name_or_id_to_id
from helpers import *
from pylons.i18n import _


class MetametaController(BaseController):
    """
    ckanext-meta Controller class
    """

    def index(self, id):
        """
          main page for editing metadata fields
        """

        data_dict = {'id': id}

        context = {'model': ckan.model,
                   'session': ckan.model.Session,
                   'user': pylons.c.user or pylons.c.author}

        org_id = None
        edit_org = None
        org_details = None

        #check user can edit the organisation
        try:
            edit_org = plugins.toolkit.check_access('organization_update', context, data_dict=data_dict)
            org_details = plugins.toolkit.get_action('organization_show')(context, data_dict)
            print edit_org
        except Exception:
            pass

        try:
            org_id = convert_group_name_or_id_to_id(id, context)
        except Exception:
            print 'cannot convert org name to org id'

        if not edit_org:
            self.send_to_org_page()

        #if metadata default have not been set before, the org will not have
        #any entries in metameta table - create them
        if not org_has_defaults(org_id):
            init_metadata(org_id)

        plugins.toolkit.c.defaults = select_metametadata_for_org(org_id, metameta_id=None, active_only=False,  withPrefix=False)
        plugins.toolkit.c.org_name = id

        if org_details:
            plugins.toolkit.c.org_title = _(org_details['display_name'])

        return plugins.toolkit.render("index-ckanext-metameta.html", extra_vars = data_dict)

    def edit(self, id, metameta_id):
        """
         edit page
        """

        data_dict = {'id': id}

        context = {'model': ckan.model,
                   'session': ckan.model.Session,
                   'user': pylons.c.user or pylons.c.author}

        org_id = None
        edit_org = None
        org_details = None

        #get org id and bail-out if it's not valid
        try:
            org_id = convert_group_name_or_id_to_id(id, context)
            #check user can edit the organisation
            edit_org = plugins.toolkit.check_access('organization_update', context, data_dict=data_dict)
            org_details = plugins.toolkit.get_action('organization_show')(context, data_dict)
            print edit_org
        except Exception:
            'EDIT page - not valid org'
            self.send_to_org_page()


        #Handle receiving POST data
        defaults = select_metametadata_for_org(org_id, metameta_id=metameta_id, active_only=True, withPrefix=False)
        for dflt in defaults:
            dflt.update({"option_value": select_metameta_options(org_id, add_prefix_key(dflt.get('key')))})

        if plugins.toolkit.request.method == 'POST':
            data = plugins.toolkit.request.POST

            if edit_org:
                try:
                    option_values = []
                    if data.has_key('option_value[]'):
                        for key, value in data.iteritems():
                            if key == 'option_value[]' and len(value):
                                option_values.append(value)
                    #make the list unique
                    option_values = sorted(set(option_values))
                    errors = update_metameta_table(org_id, metameta_id, data)
                    if len(errors):
                        plugins.toolkit.c.errors = errors
                        print plugins.toolkit.c.errors
                        for dflt in defaults:
                            if dflt['id']==metameta_id:
                                dflt['key'] = data.get('key')
                                dflt['default_value'] = data.get('default_value')
                                dflt['readonly'] = str(data.get('readonly', False)).lower()=='True'.lower()
                                dflt['label'] = data.get('label')
                                dflt['min_value'] = data.get('min_value', 0.0)
                                dflt['max_value'] = data.get('max_value', 0.0)
                                dflt['validator'] = data.get('validator', validator_ignore_missing)
                                dflt['option_value'] = option_values
                        raise StopOnError('Validation Error')
                    #update metameta option value
                    search_key =  create_search_key(data.get('key'))
                    if data.get('field_type', field_type_text) == field_type_single_choice:
                        update_metameta_options(org_id, search_key, option_values)
                    else:
                        #remove all options
                        remove_metameta_options(org_id, search_key, None)
                    h.flash_success(_("The metadata field has been updated."))
                    self.send_to_index_page(id)
                except StopOnError, e:
                    h.flash_error(_('Validation Error'))
        else:
            #NOT post
            if not edit_org:
                self.send_to_org_page()

        plugins.toolkit.c.org_id = org_id
        plugins.toolkit.c.defaults = defaults
        plugins.toolkit.c.group_name = id
        plugins.toolkit.c.title = _('Edit Metadata Field')

        if org_details:
            plugins.toolkit.c.org_title = _(org_details['display_name'])

        return plugins.toolkit.render("edit-ckanext-metameta.html")

    def new(self, id):
        """
         new page
        """
        data_dict = {'id': id}

        context = {'model': ckan.model,
                   'session': ckan.model.Session,
                   'user': pylons.c.user or pylons.c.author}

        org_id = None
        edit_org = None
        org_details = None

        #get org id and bail-out if it's not valid
        try:
            org_id = convert_group_name_or_id_to_id(id, context)
            #check user can edit the organisation
            edit_org = plugins.toolkit.check_access('organization_update', context, data_dict=data_dict)
            org_details = plugins.toolkit.get_action('organization_show')(context, data_dict)
            print edit_org
        except Exception:
            'NEW page - not valid org'
            self.send_to_org_page()

        defaults =  [{'field_type':field_type_text, 'custom':True, 'presettable':True, 'readonly':False, 'validator':validator_ignore_missing, "option_value":[]}]

        #Handle receiving POST data
        if plugins.toolkit.request.method == 'POST':
            data = plugins.toolkit.request.POST

            if edit_org:
                try:
                    option_values = []
                    if data.has_key('option_value[]'):
                        for key, value in data.iteritems():
                            if key == 'option_value[]' and len(value):
                                option_values.append(value)
                    #make the list unique
                    option_values = sorted(set(option_values))
                    errors = insert_metameta_table(org_id, data)
                    if len(errors):
                        plugins.toolkit.c.errors = errors
                        defaults[0]['key'] = data.get('key')
                        defaults[0]['default_value'] = data.get('default_value')
                        defaults[0]['label'] = data.get('label')
                        defaults[0]['field_type'] = data.get('field_type', field_type_text)
                        defaults[0]['readonly'] = str(data.get('readonly', False)).lower()=='True'.lower()
                        defaults[0]['min_value'] = data.get('min_value', 0.0)
                        defaults[0]['max_value'] = data.get('max_value', 0.0)
                        defaults[0]['validator'] = data.get('validator', validator_ignore_missing)
                        defaults[0]['option_value'] = option_values
                        raise StopOnError('Validation Error')
                    #update metameta option value
                    search_key =  create_search_key(data.get('key'))
                    if data.get('field_type', field_type_text) == field_type_single_choice:
                        update_metameta_options(org_id, search_key, option_values)
                    else:
                        #remove all options
                        remove_metameta_options(org_id, search_key, None)
                    h.flash_success(_("New metadata field has been created."))
                    self.send_to_index_page(id)
                except StopOnError, e:
                    h.flash_error(_('Validation Error'))
        else:
            #NOT post

            if not edit_org:
                self.send_to_org_page()

        plugins.toolkit.c.org_id = org_id
        plugins.toolkit.c.group_name = id
        plugins.toolkit.c.title = _('Create New Metadata Field')
        plugins.toolkit.c.defaults = defaults
        if org_details:
            plugins.toolkit.c.org_title = _(org_details['display_name'])

        return plugins.toolkit.render("edit-ckanext-metameta.html")

    def chgstat(self, id, metameta_id, state):
        """
         activate/deactivate page
        """

        data_dict = {'id': id}

        context = {'model': ckan.model,
                   'session': ckan.model.Session,
                   'user': pylons.c.user or pylons.c.author}

        org_id = None
        edit_org = None
        org_details = None

        #get org id and bail-out if it's not valid
        try:
            org_id = convert_group_name_or_id_to_id(id, context)
            #check user can edit the organisation
            edit_org = plugins.toolkit.check_access('organization_update', context, data_dict=data_dict)
            org_details = plugins.toolkit.get_action('organization_show')(context, data_dict)
            print edit_org
        except Exception:
            'Activate page - not valid org'
            self.send_to_org_page()


        #Handle receiving POST data
        if plugins.toolkit.request.method == 'POST':
            if edit_org:
                try:
                    update_stat_metameta_table(org_id, metameta_id, state)
                    state_label = 'de-activated'
                    if is_active(state):
                        state_label = 'activated'
                    h.flash_success(_("The metadata field has been %s."%(state_label)))
                    self.send_to_index_page(id)
                except StopOnError, e:
                    h.flash_error(_('An error occurred: [%s]'%(str(e))))
        self.send_to_org_page()

    def send_to_org_page(self):
        """
         redirect to organisation index
        """
        plugins.toolkit.redirect_to(controller="organization", action="index")

    def send_to_index_page(self, org_id):
        """
         redirect to organisation index
        """
        plugins.toolkit.redirect_to("organization/metameta", id=org_id)





