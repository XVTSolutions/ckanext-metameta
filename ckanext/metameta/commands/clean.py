from ckan.lib.cli import CkanCommand
import ckan
from ckanext.metameta.model import metameta_table, metameta_options_table

class CleanCommand(CkanCommand):
    '''
    '''
    summary = __doc__.split('\n')[0]
    usage = __doc__
    max_args = 9
    min_args = 0

    def __init__(self,name):
        super(CleanCommand,self).__init__(name)


    def command(self):
        self._load_config()
        
        print 'cleaning tables...'
        
        print 'metameta...'
        metameta_table.drop()
        
        print 'metameta_options'
        metameta_options_table.drop()
        
        print 'done'
        
        
        
