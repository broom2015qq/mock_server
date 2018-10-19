import sys
from ruamel.yaml import YAML

inp = """\
# example
name:
  # details
  family: Smith   # very common
  given: Alice    # one of the siblings
"""
yaml_str = """\
name: w
people: a

"""
yaml = YAML()
code = yaml.load(yaml_str)
code['name']= 'Bob'

yaml.dump(code, sys.stdout)