'''
Created on June 24, 2019
@author: Andrew Habib
'''

import sys
import jsonschema

this = sys.modules[__name__]

this.VALIDATOR = jsonschema.Draft4Validator     # Which schema validator draft to use
this.PRINT_DB = False                           # Print debugging info?
this.WARN_UNINHABITED = False                   # Enable uninhabited types warning?

#-------------------------------^^^----------------------------

# Path to cache directory for semantic graphs
SEMANTIC_CACHE_DIR = None

# Additional RDF graph URLs to load
SEMANTIC_GRAPH_URLS = []

# Enable/disable semantic reasoning
SEMANTIC_REASONING_ENABLED = True

# API to enable/disable semantic reasoning
def set_semantic_reasoning(enabled=True):
    this.SEMANTIC_REASONING_ENABLED = enabled

# API to set the semantic cache directory
def set_semantic_cache_dir(path):
    this.SEMANTIC_CACHE_DIR = path
    
# API to add additional semantic graph URLs
def add_semantic_graph_url(url):
    if url not in this.SEMANTIC_GRAPH_URLS:
        this.SEMANTIC_GRAPH_URLS.append(url)


#-------------------------------^^^----------------------------

# API to set which schema validator draft to use
def set_json_validator_version(v=jsonschema.Draft4Validator):
    ''' Currently, our subtype checking supports json schema draft 4 only,
        so VALIDATOR should not changed.
        We prodive the method for future support of other json schema versions. '''

    this.VALIDATOR = v


# API to set print debugging info?
def set_debug(b=False):
    if b:
        this.PRINT_DB = True
    else:
        this.PRINT_DB = False


# API to enable uninhabited types warning?
def set_warn_uninhabited(b=False):
    if b:
        this.WARN_UNINHABITED = True
    else:
        this.WARN_UNINHABITED = False
