from setuptools import setup

setup(
    name='hello_world_project',
    version='0.1',
    py_modules=['main'],
    install_requires=[
        'requests==2.31.0',
    ],
    entry_points={
        'console_scripts': [
            'hello-world=main:say_hello',
        ],
    },
)
