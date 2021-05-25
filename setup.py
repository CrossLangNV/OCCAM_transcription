from setuptools import setup, find_packages


with open("README.md", 'r') as f:
    long_description = f.read()

with open('requirements.txt') as f:
    required = f.read().splitlines()


setup(
    name='OCCAM-transcription', # the name of the package
    version='0.1',
    # contains our actual code
    packages=find_packages(
        where = 'src',
    ), # =['xml_orm'],  # No submodules are taken
    package_dir={"": "src"},
    # package_data={'': ['license.txt']},
    include_package_data=True,  # To add non-.py files.
    author='Laurens Meeus',
    author_email='laurens.meeus@crosslang.com',
    description="Python wrapper for the XML's regarding the transcription",
    long_description=long_description,
    # scripts=[''], # the launcher script
    install_requires=required,  # external packages as dependencies
)

