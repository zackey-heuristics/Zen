from setuptools import setup, find_packages


setup(
    name='Zen',
    version="1.1",
    packages=find_packages(),
    author="zackey-heuristics",
    install_requires=["requests"],
    description="Output Zen results in JSON format",
    include_package_data=True,
    url='https://github.com/zackey-heuristics/Zen',
    py_modules=["zen", "zen_json_output"],
    entry_points={
        "console_scripts": [
            "zen-json = zen_json_output:main",
        ],
    },
)