'''
Created on August 6, 2019
@author: Andrew Habib

Enhanced with semantic type support by adding RDF and semantic web dependencies.
'''

from setuptools import setup, find_packages
import sys

# Check Python version
if sys.version_info < (3, 8):
    sys.exit('Python 3.8 or higher is required.')

with open("README.md", "r", encoding='utf-8') as fh:
    long_description = fh.read()

# Platform-specific dependencies
platform_deps = []
if sys.platform == "darwin":  # macOS
    platform_deps.extend([
        'wheel>=0.37.0',  # Helps with binary package installation on macOS
    ])

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
    packages=find_packages(),
    license='Apache License 2.0',
    
    # Core dependencies
    install_requires=[
        # Original dependencies
        'portion>=2.3.0',           # Interval arithmetic
        'greenery>=4.0.0',          # Regular expression operations
        'jsonschema>=4.0.0',        # JSON Schema validation
        'jsonref>=0.2',             # JSON reference resolution
        
        # Essential semantic dependencies
        'rdflib>=6.0.0',            # Core RDF processing
        'requests>=2.25.0',         # HTTP requests for ontology loading
        'urllib3>=1.26.0',          # URL handling (explicit for compatibility)
        
        # Additional dependencies your code uses
        'pytest>=6.0.0',            # For testing (used in your test files)
    ] + platform_deps,
    
    # Optional dependencies for enhanced functionality
    extras_require={
        'dev': [
            'pytest>=6.0.0',
            'pytest-cov>=2.0.0',
            'black>=21.0.0',
            'flake8>=3.8.0',
        ],
        'performance': [
            'lxml>=4.6.0',          # Faster XML parsing for RDF
            'cchardet>=2.1.0',      # Faster character encoding detection
        ],
        'ontologies': [
            'owlrl>=5.2.0',         # OWL reasoning (optional)
            'SPARQLWrapper>=1.8.0', # Advanced SPARQL queries (optional)
        ]
    },
    
    # Python version requirement
    python_requires='>=3.8',
    
    # Entry points
    entry_points={
        'console_scripts': [
            'jsonsubschema-semantic=jsonsubschema.cli:main'
        ]
    },
    
    # Classifiers for better package discovery
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Text Processing :: Markup',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    
    # Keywords for package discovery
    keywords='json schema validation semantic web rdf ontology qudt foaf skos',
    
    # Package data
    include_package_data=True,
    zip_safe=False,
)