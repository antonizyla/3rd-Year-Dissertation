#/bin/sh

# format and cleanup code 
ruff format src/
ruff check src/ --fix
ruff format src/ 

# remove any pycaches
find src/ -type d -name "__pycache__" -exec rm -rf {}

# generate pdoc
rm -rf docs
cd src/Influence_Modelling
pdoc ./*.py -o ../../docs
cd ..
cd ..

# remove all packages
rm -rf dist/

# build and install the package
pip uninstall -y Influence_Modelling
python -m build
pip install dist/*.whl
