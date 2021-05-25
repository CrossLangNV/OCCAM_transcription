from setuptools import setup

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='OCCAM-transcription', # the name of the package
    version='0.1',
    packages=['xml_orm'], # contains our actual code
    author='Laurens Meeus',
    author_email='laurens.meeus@crosslang.com',
    description="Python wrapper for the XML's regarding the transcription",
    # scripts=[''], # the launcher script
    install_requires=required,  # external packages as dependencies
)