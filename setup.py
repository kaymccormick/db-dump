from setuptools import setup, find_packages

requires = ['SqlAlchemy', 'plaster', 'plaster_pastedeploy', 'python-datauri']

packages = find_packages(exclude=['tests'])
print(packages)
setup(
    name='db_dump',
    author='Kay Mccormick',
    author_email='kay@kaymccormick.com',
    version='0.1',
    packages=packages,
    install_requires=requires,
    entry_points={
        'plaster.loader_factory': [
            'data = db_dump.loader:DataLoader',
        ],
        'console_scripts': [
            'db_dump = db_dump.main:main',
        ],
    },
)
