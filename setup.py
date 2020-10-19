from setuptools import find_packages, setup

DEPENDENCIES = [
    'Flask',
    'Flask-SQLAlchemy',
    'Flask-Migrate',
    'Flask-WTF',
    'psycopg2',
    'email_validator',
    'requests',
    'indice_pollution==0.3.2'
]

setup(
    name='ecosante',
    version='0.1.0',
    description='ecosante.beta.gouv.fr',
    url='https://github.com/betagouv/ecosante',
    download_url='https://github.com/betagouv/ecosante/archive/0.1.0.tar.gz',
    author='Vincent Lara',
    author_email='vincent.lara@beta.gouv.fr',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.8'
    ],
    keywords='air quality aasqa atmo iqa',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=DEPENDENCIES,
    extras_require={"test": ["pytest"]}
)
