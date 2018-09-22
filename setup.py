from setuptools import setup, find_packages

requires = ['SqlAlchemy', 'plaster', 'psycopg2', 'plaster_pastedeploy', 'zope.interface',
            'zope.component', 'zope.sqlalchemy','python-datauri', 'marshmallow']

packages = find_packages(exclude=['tests'])
print(packages)
setup(
    name='db_dump',
    author='Kay Mccormick',
    author_email='kay@kaymccormick.com',
    packages=packages,
    install_requires=requires,
    entry_points={
        'plaster.loader_factory': [
            'data = db_dump.loader:DataLoader',
            'zc+tcp = db_dump.loader:ZooKeeperLoader'
        ],
        'console_scripts': [
            'db_dump = db_dump.main:main',
        ],
    },
)
