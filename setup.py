from setuptools import setup, find_packages

setup(
    name='Py4WSL',
    version='0.0.2',
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    url='https://github.com/ssantosv/py4wsl',
    license='MIT',
    author='Sergio de los Santos',
    author_email='s.delossantos@gmail.com',
    description='Python WSL wrapper',
    python_requires='>=3.7',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    keywords=['WSL', 'windows subsystem for linux'],
)
