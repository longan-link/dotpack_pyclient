# upload to pypi
https://pypi.org/project/twine/

*  python -m pip install --upgrade twine setuptools wheel
*  python setup.py sdist bdist_wheel
*  twine upload dist/*