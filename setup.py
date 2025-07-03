from setuptools import setup, find_packages


setup(
    name='PyWSL',
    version='0.1.0',
    packages=find_packages(),
    url='https://github.com/ssantosv/pywsl',  # Reemplaza con tu URL
    license='MIT',
    author='Sergio de los Santos',  # Reemplaza con tu nombre
    author_email='s.delossantos@gmail.com',  # Reemplaza con tu email
    description='Python WSL wrapper',
    python_requires='>=3.7',  # Python version
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    keywords=['WSL', 'windows subsystem for linux'],
)