from setuptools import find_packages, setup

#Read the contents of the README file
with open("README.txt", "r") as fh:
    long_description = fh.read()

setup(
    name='PTPNperfbound',
    packages=find_packages(include=['net','solver']),
    version='0.0.1',
    entry_points={
        'console-script' : [
            'ptpnbound = PTPNperfbound.src.ptpnbound:cli',
        ]
    },
    description='Performance bound solver for Probabilistic Timed Petri Nets',
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url="https://github.com/simber72/PTPNperfbound",
    author='Simona Bernardi',
    author_email="simonab@unizar.es",
    license='GPL-3',
    classifiers=[
    "Programming Language :: Python",
    "Programming Language :: Python :: 3.10",
    "Operating System :: OS Independent"
    ],
    python_requires='>=3.6.1',
    setup_requires=['pytest-runner'],
    tests_require=['pytest>=6.2.2'],
    test_suite='test'
)