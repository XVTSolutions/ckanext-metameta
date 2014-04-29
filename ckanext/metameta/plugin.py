import ckan.plugins as plugins
import ckan.plugins.toolkit as tk
import ckan.lib.navl.dictization_functions as df
import helpers as h
from ckan.lib.navl.dictization_functions import StopOnError
from ckan.lib.navl.validators import not_empty
import ckan
from ckan.model import UserFollowingDataset, User
import sqlalchemy
from ckan.lib.activity_streams import activity_stream_string_functions, activity_stream_string_icons
from model import create_metameta_table, create_metameta_options_table

class MetametaPlugin(plugins.SingletonPlugin, tk.DefaultDatasetForm):
    """
    Setup plugin
    """
    print "loading ckanext-metameta"

    plugins.implements(plugins.IConfigurer, inherit=True)
    plugins.implements(plugins.IConfigurable, inherit=True)
    plugins.implements(plugins.IDatasetForm, inherit=False)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IOrganizationController, inherit=True)
    plugins.implements(plugins.IPackageController, inherit=True)

    def before_view(self, pkg_dict):
        # IOrganizationController
        #initialization if any non-updated
        h.init_organization()
        return super(MetametaPlugin, self).before_view( pkg_dict)

    def is_fallback(self):
        # Return True to register this plugin as the default handler for
        # package types not handled by any other IDatasetForm plugin.
        return True

    def configure(self, config):
        #create table if not existing
        create_metameta_table()
        create_metameta_options_table()

        activity_stream_string_functions[h.activity_assign_maintainer] = h.activity_stream_string_assign_maintainer
        activity_stream_string_icons[h.activity_assign_maintainer] = 'user'


    def update_config(self, config):
        tk.add_template_directory(config, 'templates')
        tk.add_public_directory(config, 'public')
        tk.add_resource('public', 'ckanext-metameta')
        tk.add_resource('fanstatic', 'fanstatic')


    def before_map(self, map):

        map.connect('organization/metameta', '/organization/metameta/{id}',
            controller='ckanext.metameta.controller:MetametaController',
            action='index')

        map.connect('organization/metameta/edit', '/organization/metameta/edit/{id}/{metameta_id}',
            controller='ckanext.metameta.controller:MetametaController',
            action='edit')

        map.connect('organization/metameta/chgstat', '/organization/metameta/chgstat/{id}/{metameta_id}/{state}',
            controller='ckanext.metameta.controller:MetametaController',
            action='chgstat')

        map.connect('organization/metameta/new', '/organization/metameta/new/{id}',
            controller='ckanext.metameta.controller:MetametaController',
            action='new')

        return map

    def get_helpers(self):
        # ITemplateHelpers
        # TODO
        return {
            'metameta_markdown_wrap'        : h.markdown_wrap,
            'metameta_select_options'       : h.select_metameta_options,
            'metameta_validator_label'      : h.validator_label,
            'metameta_field_type_label'     : h.field_type_label,
            'metameta_debug_print'          : h.debug_print,
            'metameta_convert_error_keys'   : h.convert_error_keys,
            'metameta_is_text_field'        : h.is_text_field,
            'metameta_is_textarea_field'    : h.is_textarea_field,
            'metameta_is_dropdown_field'    : h.is_dropdown_field,
            'metameta_is_active'            : h.is_active,
            'metameta_is_required'          : h.is_required,
            'metameta_is_obsolete_and_empty': h.is_obsolete_and_empty,
            'metameta_get_data'             : h.metameta_get_data,
            'metameta_get_error'            : h.get_error,
            'metameta_get_value'            : h.get_value,
            'metameta_get_validators'       : h.get_validators,
            'metameta_get_readonly'         : h.get_readonly,
            'metameta_get_field_types'      : h.get_field_types,
            'metadata_get_maintainers'      : h.get_maintainers,
            'metameta_retrieve_packages'    : h.retrieve_packages,
            'metameta_convert_to_local_timestamp'    : h.metameta_convert_to_local_timestamp,
            'metameta_topoffwith'           : h.topoffwith,
            'metameta_is_oneline_textarea'  : h.is_oneline_textarea,
                }

    def package_types(self):
        # This plugin doesn't handle any special package types, it just
        # registers itself as the default (above).
        # IDatasetForm
        return []

    def _modify_package_schema(self, schema):

        #retrieve metameta data
        org_id = h.get_organization_id()
        records = h.select_metametadata_for_org(org_id, metameta_id=None, active_only=True, withPrefix=True)

        for record in records:
            validator = record['validator']
            if h.is_metameta_validator(record['validator']):
               validator = h.get_validator(validator)
            else:
               validator = tk.get_validator(validator)

            # convert_to_extras instead of convert_to_tags.
            schema.update({
                    record['key']: [
                        validator,
                        tk.get_converter('convert_to_extras')]
                    })

        return schema

    def create_package_schema(self):
        # IDatasetForm
        schema = super(MetametaPlugin, self).create_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def update_package_schema(self):
        # IDatasetForm
        schema = super(MetametaPlugin, self).update_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def show_package_schema(self):
        # IDatasetForm
        schema = super(MetametaPlugin, self).show_package_schema()

        # Don't show vocab tags mixed in with normal 'free' tags
        # (e.g. on dataset pages, or on the search page)
        schema['tags']['__extras'].append(tk.get_converter('free_tags_only'))

        #retrieve metameta data
        org_id = h.get_organization_id()
        records = h.select_metametadata_for_org(org_id, metameta_id=None, active_only=True, withPrefix=True)

        for record in records:
            validator = record['validator']
            if h.is_metameta_validator(record['validator']):
               validator = h.get_validator(validator)
            else:
               validator = tk.get_validator(validator)

            # convert_from_extras instead of convert_from_tags.
            schema.update({
                record['key']: [
                    tk.get_converter('convert_from_extras'),
                    validator]
                })


        return schema

    def setup_template_variables(self, context, data_dict):
        # IDatasetForm
        #IARDatasetFormPlugin.num_times_setup_template_variables_called += 1
        # TODO
        #self._trace(context, data_dict)
        return super(MetametaPlugin, self).setup_template_variables(
                context, data_dict)

    def _trace(self, context, data_dict=None):
        if context is not None:
            print "----context----"
            print [value for value in context.iteritems()]
        if data_dict is not None:
            print "----data_dict----"
            print [value for value in data_dict.iteritems()]
            pass
        if plugins.toolkit.c is not None:
            print "----plugins.toolkit.c----"
            print plugins.toolkit.c
            pass


    #CVJ-137
    def after_create(self, context, pkg_dict):
        return self._after_update(context, pkg_dict)

    def after_update(self, context, pkg_dict):
        return self._after_update(context, pkg_dict)

    def _after_update(self, context, pkg_dict):

        #add notification to maintainer user's activity stream, if field has changed
        if tk.c.action in (u'new', u'edit') and pkg_dict['maintainer']:
            maintainer = ckan.model.User.get(pkg_dict['maintainer'])
            h.notify_maintainer(pkg_dict, maintainer)
        return context, pkg_dict
