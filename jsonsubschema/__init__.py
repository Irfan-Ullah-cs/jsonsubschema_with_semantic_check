'''
Created on August 6, 2019
@author: Andrew Habib
'''


from jsonsubschema import api
from jsonsubschema import config
from jsonsubschema import exceptions
from jsonsubschema import _canonicalization

isSubschema = api.isSubschema
meetSchemas = api.meet
joinSchemas = api.join
isEquivalent = api.isEquivalent

canonicalizeSchema = _canonicalization.canonicalize_schema

set_debug = config.set_debug
set_warn_uninhabited = config.set_warn_uninhabited


#-------------------------------^^^----------------------------

set_semantic_reasoning = config.set_semantic_reasoning
set_semantic_cache_dir = config.set_semantic_cache_dir
add_semantic_graph_url = config.add_semantic_graph_url

#-------------------------------^^^----------------------------