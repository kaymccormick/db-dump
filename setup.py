from setuptools import setup, find_packages

requires = ['SqlAlchemy', 'plaster', 'psycopg2', 'plaster_pastedeploy', 'zope.interface',
            'zope.component']

setup(
    name='db_dump',
    author='Kay Mccormick',
    author_email='kay@kaymccormick.com',
    packages=find_packages(),
    install_requires=requires,
    entry_points={
        'plaster.loader_factory': [
            'data = db_dump.main:DataLoader'
        ],
        'console_scripts': [
            'db_dump = db_dump.main:main',
        ],
    },
)
