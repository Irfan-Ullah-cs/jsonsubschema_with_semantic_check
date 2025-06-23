'''
Created on August 6, 2019
@author: Andrew Habib

Enhanced with semantic type support by adding RDF and semantic web dependencies.
'''

from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='jsonsubschema-with-semantic',  
    version='0.1.0', 
    author='Maxime Lefrançois, Irfan Ullah',
    author_email='imirfan.cs@gmail.com',  
    maintainer='Irfan Ullah (based on work by Andrew Habib, Avraham Shinnar, Martin Hirzel)',
    description="JSON Schema subtyping with semantic type validation using RDF ontologies (QUDT, FOAF, SKOS)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/Irfan-Ullah-cs/jsonsubschema_with_semantic_check',
    packages=['jsonsubschema'],
    license='Apache License 2.0',
    
    # Core dependencies only
    install_requires=[
        # Original dependencies
        'portion',
        'greenery>=4.0.0',
        'jsonschema',
        'jsonref',
        
        # Essential semantic dependencies
        'rdflib>=6.0.0',           # Core RDF processing
        'requests>=2.25.0',        # HTTP requests for ontology loading
    ],
    
    # Python version requirement 
    python_requires='>=3.7',
    
    # Entry points
    entry_points={
        'console_scripts': [
            'jsonsubschema-semantic=jsonsubschema.cli:main'
        ]
    }
    
 
)