#!/usr/bin/python

# -*- mode: python -*-
# Leidokos-Testing -- Testing framework for the Kaleidoscope firmware
# Copyright (C) 2017 noseglasses (shinynoseglasses@github.com)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-

# This python script prepares testing specifications to
# facilitate the generation of tests with external build systems.
#
# The script traverses a hierarchical directory structure,
# collects and parses files and generates a set of
# firmware builds and test runs that use the firmware 
# that is build.
#
# *** Test specification ***
#
# A test is define by the following information
#
# - a name (without whitespaces)
# - a description string
# - driver command line parameters (optional)
# - a python driver file (driver.py)
# - a firmware sketch (sketch.ino)
# - a set of custom modules, where every module can define
#    - an url of a git repository
#    - a commit (optional)
#    - a name (the directory name of a Kaleidoscope module,
#         that matches the basepath of the cloned git repository)
#
# Some of this information can be defined in a yaml-specificaton file
# (specification.yaml).
#
# A yaml file can e.g. read
#
#   name: Test1
#   description: Description
#   driver_cmd_line_flags: <command line flags passed to 
#                           the driver Python process>
#   modules:
#      - url: url1
#        commit: commit1
#        name: name1
#      - url: url2
#        commit: commit2
#        name: name2
#
# When no "name" attribute is define, the basename of the respective
# directory is used instead.
#
# All tests use a dedicated firmware that is defined by the set of custom modules
# and the firmware sketch. If a custom module is given a name but 
# no url, the stock module with same name is used. If both, a name and 
# an url are specified, the remote git repository specified by url is 
# cloned to the local libraries sub-directory specified by name.
#
# Tests that define equal combinations of custom modules and firmware sketch share
# a common firmware build to minimize the amount of build overhead.
# The firmware is build to run on the host system (x86) and wrapped
# in a shared library that can be loaded as a Python module.
# The latter is done using the Leidokos-Python-Wrapper.
#
# The actual name of a test is generated as a combination of the names
# that are generated on the different levels of the testing directory
# tree, either read from the yaml specification or derived from
# the directory basename.
#
# *** Testing directory structure ***
#
# The directory structure may be hierarchical. 
#
# A basic principal is that information on higher levels of the
# directory tree override similar information on lower levels.
#
# Each directory can but does not have to contain the following
#
# - *sketch.ino : An arduino firmware sketch file
# - *driver.py : A python script that drives the actual test.
# - *specification.yaml : a yaml file with test information.
# - __external__ : A directory that can contain the same files,
#     i.e. sketch, driver and specification and that can e.g.
#     actually be a git submodule to pull in external test 
#     definitions. The __external__ directory is not further
#     traversed.
# - __test__ : A flag file that, if present, triggers
#     the generation of tests on the respective directory
#     level even though it is not a leaf directory.
#     Note, that this file does have no effect if present in leaf
#     directories.
#
# Tests are automatically generated for every node in the 
# directory tree that is either a leaf node or contains a 
# file named "__test__".

import argparse
import sys
import os
import hashlib
import yaml
import copy
import fnmatch

# Finds a files that match the globbing pattern 
# (non-recursively)
#
def find_files(pattern, path):
   result = []
   for root, dirs, files in os.walk(path):
      if path != root:
         continue
      for name in files:
         if fnmatch.fnmatch(name, pattern):
            result.append(os.path.join(root, name))
   return result

# Finds a files that matches name (non-recursively)
#
def find_file(name, path):
   for root, dirs, files in os.walk(path):
      if path != root:
         continue
      if name in files:
         return os.path.join(root, name)
   return None

def find_unique_file(pattern, path, file_type_descr):
   
   files = find_files(pattern, path)
   
   n_files = len(files)
   
   selected_file = None
   if n_files > 0:
      selected_file = files[0]
      if n_files > 1:
         sys.stdout.write("Warning: Multiple " + file_type_descr + " found in directory \""
            + path + "\". Using the first encounter \""
            + selected_file + "\"")
   return selected_file

# The names of the files and directories
# that may be defined in the testing directory structure.
# See the description at the top of this script for
# more information about their meaning.
#
external_specification_subdir_name  = "__external__"
test_trigger_basename               = "__test__"
firmware_sketch_pattern            = "*sketch.ino"
test_driver_pattern                = "*driver.py"
test_specification_pattern         = "*specification.yaml"

# Every bit of information that influences a test is an
# abstract entity. 
#
# Entities are assigned to a path where they were
# encountered. This is especially useful when complex test
# hierarchies are defined to keep track of what is defined
# on which hierarchy level.
#
class Entity(object):
   
   def __init__(self):
      self.path = None
   
   def attach(self, path):
      self.path = path.path

class File(Entity):

   def __init__(self, filename = None):
       
      self.filename = filename
      
   def __eq__(self, other):
    return self.filename == other.filename

class PythonDriver(File):
   pass

class FirmwareSketch(File):
   pass
       
# A property represents any bit of information that
# was e.g. collected from the yaml specification. 
# Properties define a name -> value relation.
# The name is not stored in the property but
# defined by the class member name.
#
class Property(Entity):
   
   def __init__(self, value = None):
      
      self.value = value
   
   def __eq__(self, other):
    return self.value == other.value
 
# A Kaleidoscope module is either a core module or
# a plugin, defined by its URL and an optional commit information.
# If a commit is defined, it will be checked out before the
# firmware is build. Else the head of the master branch will be
# used instead.
# A module can replace or remove a stock module with given name
# if necessary.
#
# If no url is defined but a name, we assume that 
# a parent module with respective name is supposed to be removed.
# The sketch must take care that in such a case the 
# removed stock module is not referenced in any possible way.
#
class KaleidoscopeModule(object):
   
   def __init__(self):
      
      self.url = None
      self.commit = None
      self.name = None
      
   # To be able to easily distinguish module definitions
   # we compute a digest of all information that defines it.
   #
   def getDigest(self):
      
      m = hashlib.sha256()
      
      m.update(str(self.url).encode('utf-8'))
      m.update(str(self.commit).encode('utf-8'))
      m.update(str(self.name).encode('utf-8'))
      
      return m.hexdigest()
    
class FirmwareBuild(Entity):

   def __init__(self, parent_build = None):
      
      if parent_build:
         self.modules = parent_build.modules
         self.module_digests = parent_build.module_digests
         self.firmware_sketch = parent_build.firmware_sketch
         self.boards_url = parent_build.boards_url
         self.boards_commit = parent_build.boards_commit
      else:
         self.modules = []
         self.module_digests = []
         self.firmware_sketch = None
         self.boards_url = None
         self.boards_commit = None
         
   # Checks if the firmware build is valid, i.e. well 
   # defined
   #
   def checkValidity(self):
      if not self.firmware_sketch:
         return False
      
      return True
   
   # Checks if a certain module is already contained
   #
   def containsModule(self, new_module):
          
      new_module_digest = new_module.getDigest()

      # Check if a module with same digest is already present
      #
      try:
         list_index = self.module_digests.index(new_module_digest)
         
         # The fact that no exception has been thrown 
         # indicates that a matching digest was found.
         
         # In this case, we do not need to take any 
         # action and just go with the parent list
         # of modules.
         
         return True
         
      except:
         pass
         
      return False
   
   # Clones a firmware sketch definition on a certain tree level 
   # to be customized on the next higher tree level
   #
   def clone(self):
            
      new_self = FirmwareBuild(self)
      
      # This firmware build must be made unique.
      # Therefore, make a shallow copy of modules and module_digests. 
      #
      new_self.modules = copy.copy(self.modules)
      new_self.module_digests = copy.copy(self.module_digests)
      new_self.firmware_sketch = self.firmware_sketch
      
      return new_self
     
   # Adds a module to the firmware definition
   #
   def addModule(self, new_module):

      new_name = new_module.name
      do_append = True
      
      new_digest = new_module.getDigest()
      
      if new_name:
         
         # Checks if the firmware build already
         # contains a module that has the same name as the new
         # module. If so, we replace it.
         #
         for i, module in enumerate(self.modules):
            if module.name == new_name:
               self.modules[i] = new_module
               self.module_digests[i] = new_digest
               do_append = False
               break
            
      if do_append:
         self.modules.append(new_module)
         self.module_digests.append(new_digest)
            
   # Computes the module_digests of all modules. As the order of
   # updating the overall digest is not commutative 
   # with respect to the members, we have to sort them first
   #
   def getDigest(self):

      module_digests = []
      for module in self.modules:
         module_digests.append(module.getDigest())
      
      module_digests.sort()
      
      m = hashlib.sha256()
      
      for digest in module_digests:
         m.update(str(digest).encode('utf-8'))
         
      m.update(str(self.boards_url).encode('utf-8'))
      m.update(str(self.boards_commit).encode('utf-8'))
      m.update(self.firmware_sketch.filename.encode('utf-8'))
         
      return m.hexdigest()

# Every subdirectory in the testing directory tree is mapped to an 
# instance of class TestNode
#
class TestNode(object):
    
   def __init__(self, path, parent = None):
      
      self.children = []
      
      self.parent = parent
      
      self.path = path
      
      self.python_driver = None
   
      # Properties
      #
      self.name = None
      self.description = None
      self.driver_cmd_line_flags = None
      
      self.boards_url = None
      self.boards_commit = None
      
      # Defines if tests are supposed to be run on this level
      #
      self.is_test_target = False
      
      self.setup()
      
   # Generates a global name that references the test node
   # by concatenating the names of all parent nodes.
   #
   def generateGlobalName(self):
     
      if self.parent:
         
         parent_name = self.parent.generateGlobalName()
         
         if not (self.name is self.parent.name):
            return parent_name + "." + self.name.value
         else:
            return parent_name
      else:
         return self.name.value
   
   # Checks if a node is supposed to generated tests.
   # For this to be the case, the node must either be a leaf node
   # or an interior node that defines a __test__ flag file.
   #
   def generatesTests(self):
      return self.is_test_target or (len(self.children) == 0)
   
   # Checks the validity of all test tree nodes and their 
   # children
   #
   def recursivelyCheckValidity(self):
      
      is_valid = True
      
      if self.generatesTests():
      
         #sys.stdout.write("A test node \"%s\" has %d children and is test_target: %d\n" % (self.path, len(self.children), self.is_test_target))
      
         if not self.path:
            is_valid = False
            sys.stdout.write(
               "A test node without a path definition was found.\n")
                  
         if not self.name:
            is_valid = False
            sys.stdout.write(
               "A test node for path \"%s\" was found that does not "
               "feature a name.\n" % (self.path))
         
         if not self.description:
            is_valid = False
            sys.stdout.write(
               "A test node for path \"%s\" was found that does not "
               "feature a description.\n" % (self.path))
                  
         if not self.python_driver:
            is_valid = False
            sys.stdout.write(
               "A test node for path \"%s\" was found that does not "
               "feature a python driver file (%s).\n" 
                  % (self.path, test_driver_pattern))
            
         if not self.firmware_build:
            is_valid = False
            sys.stdout.write(
               "A test node for path \"%s\" was found that does not "
               "feature a firmware build.\n" % (self.path))
            
         if not self.firmware_build.checkValidity():
            is_valid = False
            sys.stdout.write(
               "A test node for path \"%s\" was found that does not "
               "feature a firmware sketch (%s).\n" % (self.path, firmware_sketch_pattern))
            #sys.stdout.write("Node: " + str(id(self)) + "\n")
            #sys.stdout.write("FB str: " + str(self.firmware_build) + "\n")
            
      for child in self.children:
         is_valid &= child.recursivelyCheckValidity()
         
      return is_valid
      
   # Copies a member variable of the parent directory's TestNode to 
   # this node (this can be seen a an inheritance of the respective property)
   #
   def useParentEntity(self, name):

      if self.parent:
         setattr(self, name, getattr(self.parent, name))
      
   # Looks for a python driver file in the current directory
   #
   def findPythonDriver(self, path):

      python_driver_file = find_unique_file(test_driver_pattern, path,
                                               "python test driver files")
      if python_driver_file:
         self.python_driver = PythonDriver(python_driver_file)
         self.python_driver.attach(self)
         return
      
      # If we don.f fine one, we inherit the parents driver file
      #
      self.useParentEntity("python_driver")
        
   # Looks for a python driver file in the current directory
   #
   def findFirmwareSketch(self, path):
      
      firmware_sketch_file = find_unique_file(firmware_sketch_pattern, path,
                                               "sketch files")
      
      if firmware_sketch_file:
         
         #sys.stdout.write("Sketch file %s found\n" % (firmware_sketch_file))
         
         # A firmware build is defined by its modules and the firmware sketch.
         # Thus, if the firmware sketch differs from that of the parent nodes
         # firmware build, we generate an individual build.
         #
         if not self.firmware_build.firmware_sketch \
               or not (self.firmware_build.firmware_sketch.filename \
                              == firmware_sketch_file):
               
            self.conditionallyCloneFirmwareBuild()
         
            self.firmware_build.firmware_sketch \
               = FirmwareSketch(firmware_sketch_file)
            self.firmware_build.firmware_sketch.attach(self)
         
         #sys.stdout.write("Sketch file %s\n" % (self.firmware_build.firmware_sketch.filename))
         return
      
   # Looks for an explicit test trigger flag file (such a file
   # is only required for non-leaf directores of the testing tree).
   #
   def findTestTrigger(self, path):
      
      test_trigger = find_file(test_trigger_basename, path)
      
      if test_trigger:
         #sys.stdout.write("File %s in path %s found\n" % (test_trigger, path))
         self.is_test_target = True
      
   # Reads a yaml specification file, if present.
   #
   def parseYAMLDefinitions(self, path):
      
      yaml_file = find_unique_file(test_specification_pattern, path,
                                               "test specification files")
      
      if not yaml_file:
         return
      
      my_yaml = None
      with open(yaml_file, 'r') as stream:
         try:
            my_yaml = yaml.load(stream)
         except yaml.YAMLError as exc:
            print(exc)
            return
            
      # my_yaml now contains all necessary information as 
      # a nested data set of dictionaries and lists
      #
      new_name = my_yaml.get("name") 
      if new_name:
         self.name = Property(new_name)
         self.name.attach(self)
         
      new_despription = my_yaml.get("description") 
      if new_despription:
         self.description = Property(new_despription)
         self.description.attach(self)
         
      new_driver_cmd_line_flags = my_yaml.get("driver_cmd_line_flags") 
      if new_driver_cmd_line_flags:
         self.driver_cmd_line_flags = Property(new_driver_cmd_line_flags)
         self.driver_cmd_line_flags.attach(self)
         
      new_boards_url = my_yaml.get("boards_url") 
      if new_boards_url:
         
         if not self.firmware_build.boards_url \
               or not (self.firmware_build.firmware_sketch.boards_url \
                              == new_boards_url):
               
            self.conditionallyCloneFirmwareBuild()
         
            self.firmware_build.boards_url = new_boards_url
         
      new_boards_commit = my_yaml.get("boards_commit") 
      if new_boards_commit:
         if not self.firmware_build.boards_commit \
               or not (self.firmware_build.firmware_sketch.boards_commit \
                              == new_boards_commit):
               
            self.conditionallyCloneFirmwareBuild()
         
            self.firmware_build.boards_commit = new_boards_commit
         
      new_modules = my_yaml.get("modules")
      if new_modules:
         
         # Iterate over the modules and establish a 
         # firmware build
         #
         for module_dict in new_modules:
         
            new_module = KaleidoscopeModule()
            new_module.url = module_dict.get("url") or "__NONE__"
            new_module.commit = module_dict.get("commit") or "__NONE__"
            new_module.name = module_dict.get("name") or "__NONE__"

            # If we find a module that is not contained in 
            # the current set of modules
            #
            if not self.firmware_build.containsModule(new_module):
               
               # And this path does not have its own firmware build...
               #
               self.conditionallyCloneFirmwareBuild()
                  
               self.firmware_build.addModule(new_module)
               
   def cloneFirmwareBuild(self):
      
      #sys.stdout.write("Cloning firmware build at %s\n"
         #% (self.path))
  
      self.firmware_build = self.firmware_build.clone()
      self.firmware_build.path = self.path
      self.has_dedicated_firmware = True
      
      #sys.stdout.write("FB after clone: " + str(id(self.firmware_build)) + "\n")
      #sys.stdout.write("FB.modules after clone: " + str(id(self.firmware_build.modules)) + "\n")
      
   def conditionallyCloneFirmwareBuild(self):
      if not self.has_dedicated_firmware:
         self.cloneFirmwareBuild()
               
   def setup(self):
      
      if self.parent:
         self.firmware_build = self.parent.firmware_build
         self.has_dedicated_firmware = False
      else:
         
         # The root node has its own FirmwareBuild class to be able
         # to inherit properties.
         
         self.firmware_build = FirmwareBuild()
         self.firmware_build.path = self.path
         self.has_dedicated_firmware = True
      
      # Check if there is a __external__ directory.
      # Such a directory could, e.g. be a git submodule.
      # If such a directory is found, anything else (driver, specification, firmware)
      # in the path is ignored.
      #
      external_specification_dir \
         = find_file(external_specification_subdir_name, self.path) 
      
      if external_specification_dir:
         
         if not os.path.isdir(external_specification_dir):
            
            sys.exit("path \"" + self.path +
              "\" contains an external specification \"" +
              external_specification_subdir_name
              + "\" that is not an path.");
         
         # If we found an external specfication path, 
         # check for any other files being present, 
         # appart from the test trigger file.
         # If so, abort with an error.
         
         all_files = find_files("*", self.path)
         
         trigger_wrong_files_error = False
         if len(all_files) > 2:
            trigger_wrong_files_error = True
         elif len(all_files) == 2:
            other_file_is_test_trigger = False
            if all_files(1) == test_trigger_basename:
               other_file_is_test_trigger = True
            elif all_files(2) == test_trigger_basename:
               other_file_is_test_trigger = True
               
            if not other_file_is_test_trigger:
               trigger_wrong_files_error = True
            
         if trigger_wrong_files_error:
            sys.exit("path \"" + self.path +
              "\" contains an external specification \"" +
              external_specification_subdir_name
              + "\" and also additional files/directories appart from the test trigger (" + test_trigger_basename + "). "
              "Please make sure that either the external specification "
              "or other files are found.");
         
         source_path = external_specification_dir
      else:
         source_path = self.path
            
      # Inherit some information from the parent node to generate a
      # default configuration that can be overriden during further 
      # setup.
      #
      self.useParentEntity("description")
      self.useParentEntity("driver_cmd_line_flags")
      self.useParentEntity("boards_url")
      self.useParentEntity("boards_commit")
      self.useParentEntity("firmware_build")
       
      # The source path is the path that is searched
      # for any test information. This might either be the current
      # path or the external test reference path
      # determined above.
      
      self.findPythonDriver(source_path)
      self.findFirmwareSketch(source_path)
      self.parseYAMLDefinitions(source_path)
      
      # Look in the current path for a __test__ trigger file
      #
      self.findTestTrigger(self.path)
               
      if not self.name:
         path_basename = os.path.basename(self.path)
         self.name = Property(path_basename)
         self.name.attach(self)
         
def setup_testing_tree(testing_tree_root):
   
   test_nodes_by_path = {}
   
   root_node = TestNode(testing_tree_root)
   
   test_nodes_by_path[testing_tree_root] = root_node
   
   # Recursively traverses the testing directory structure
   # and generate the testing tree.
   #
   for dirpath, dirs, files in os.walk(testing_tree_root, followlinks=True):
      
      # Ignores empty directories
      #
      if (len(dirs) == 0) and (len(files) == 0):
         continue
      
      dirpath_basename = os.path.basename(dirpath)
      
      # Skips any external testing specification dirs
      #
      if dirpath_basename == external_specification_subdir_name:
         continue
      
      my_parent_test_node = test_nodes_by_path.get(dirpath)
      
      for my_dir in dirs:
         
         # Skip any external testing specification dirs
         #
         if my_dir == external_specification_subdir_name:
            continue
         
         my_abs_dir = os.path.join(dirpath, my_dir)
         
         new_test_node = TestNode(my_abs_dir, my_parent_test_node)
         
         my_parent_test_node.children.append(new_test_node)
         
         test_nodes_by_path[my_abs_dir] = new_test_node
         
   # Perform a validity check ot the testing information contained in
   # the testing directory tree.
   #
   test_nodes_valid = root_node.recursivelyCheckValidity()
   
   if not test_nodes_valid:
      
      sys.exit("An invalid testing setup was detected. "
         "Please correct any errors and start over.")
         
   return test_nodes_by_path

# Checks and ensures that all tests have individual names. 
# By defining identical name properties in the yaml specification
# files, it is possible that two subdirs test nodes
# are assigned the same global name.
#
def check_test_name_uniqueness(test_nodes_by_path):
   
   test_name_to_test_node = {}
   
   for test_node in test_nodes_by_path.values():
      
      test_name = test_node.generateGlobalName()
      
      if test_name in test_name_to_test_node.keys():
         
         sys.exit("Two tests in directories \"%s\" and \"%s\" that "
            "have the same name \"%s\". Please ensure that all tests have individual names" % (test_node.path, test_name_to_test_node.get(test_name).path, test_name))
         
      test_name_to_test_node[test_name] = test_node

# It is possible that different subdirectories of the build tree 
# specify identical firmware modules and sketch. The corresponding 
# firmware builds can, however, be shared. To detect this
# we compute a digest of every firmware build, join builds with
# identical module_digests and finally assign the unique builds to the test nodes.
#
def determine_unique_firmware_builds(test_nodes_by_path):

   # Generate a unique set of firmware builds.

   unique_firmware_builds_by_digest = {}

   set_id = 1
   for test_node in test_nodes_by_path.values():
      
      if test_node.generatesTests() and \
            test_node.has_dedicated_firmware:
         
         my_digest = test_node.firmware_build.getDigest()
         
         if not my_digest in unique_firmware_builds_by_digest.keys():
            test_node.firmware_build.set_id = set_id
            unique_firmware_builds_by_digest[my_digest] = test_node.firmware_build
            set_id = set_id + 1
            
   # Now replace references to modules with the unique versions
   #
   for test_node in test_nodes_by_path.values():
      
      if test_node.generatesTests():
         my_digest = test_node.firmware_build.getDigest()
         
         test_node.unique_firmware_build \
            = unique_firmware_builds_by_digest.get(my_digest)
      
   return unique_firmware_builds_by_digest
      
def sep_line(file):   
   file.write(
"################################################################################\n")
      
# Exports firmware build and test information in a way that resembels
# CMake function calls.
#
# A note to developers:
#    If test specifications are supposed to be generated in other formats,
#    just copy and adapt this function.
#
def export_as_cmake(cmake_filename, 
                    test_nodes_by_path, 
                    unique_firmware_builds_by_digest):
   
   cmake_file = open(cmake_filename, "w") 
   
   # First export the firmware builds 
   #
   sep_line(cmake_file)
   cmake_file.write("# Kaleidoscope firmware builds\n")
   sep_line(cmake_file)
   
   for digest, firmware_build in sorted(unique_firmware_builds_by_digest.items(), key=lambda x: x[1].set_id):
   #for digest, firmware_build in unique_firmware_builds_by_digest.items():
      cmake_file.write("kaleidoscope_firmware_build(\n")
      cmake_file.write("   BUILD_ID \"" + str(firmware_build.set_id) + "\"\n")
      if firmware_build.boards_url:
            cmake_file.write("   BOARDS_URL \"" + str(firmware_build.boards_url) + "\"\n")
      if firmware_build.boards_commit:
            cmake_file.write("   BOARDS_COMMIT \"" + str(firmware_build.boards_commit) + "\"\n")
      cmake_file.write("   DIGEST \"" + str(digest) + "\"\n")
      cmake_file.write("   FIRMWARE_SKETCH \"" + firmware_build.firmware_sketch.filename + "\"\n")
      for mod in firmware_build.modules:
         cmake_file.write("   URL \"" + mod.url + "\"\n")
         cmake_file.write("   COMMIT \"" + mod.commit + "\"\n")
         cmake_file.write("   NAME \"" + mod.name + "\"\n")
      cmake_file.write(")\n")
      cmake_file.write("\n")  
      
   # Now export the test definitions
   #
   sep_line(cmake_file)
   cmake_file.write("# Kaleidoscope tests\n")
   sep_line(cmake_file)
   
   test_id = 1
   for test_node in test_nodes_by_path.values():
      
      # Any interior nodes of the testing tree have to contain a
      # tag file for tests for them to be created. 
      # For leaf nodes of the testing tree, we always generate 
      # tests.
      #
      if not test_node.generatesTests():
         continue
      
      cmake_file.write("kaleidoscope_test(\n")
      cmake_file.write("   TEST_ID \"" + str(test_id) + "\"\n")
      cmake_file.write("   TEST_NAME \"" + test_node.generateGlobalName() + "\"\n")
      cmake_file.write("   TEST_DESCRIPTION \"" + test_node.description.value + "\"\n")
      if(test_node.driver_cmd_line_flags):
         cmake_file.write("   DRIVER_CMD_LINE_FLAGS \"" + test_node.driver_cmd_line_flags.value + "\"\n")
      cmake_file.write("   PYTHON_DRIVER \"" +
                test_node.python_driver.filename + "\"\n")  
      cmake_file.write("   FIRMWARE_BUILD_ID \"" +
                str(test_node.unique_firmware_build.set_id) + "\"\n")
      
      # Additional information that is probably not used by CMake
      #
      cmake_file.write("\n") 
      cmake_file.write("   # Directories where information was found\n") 
      cmake_file.write("   #\n") 
      cmake_file.write("   NAME_ORIGIN \"" + test_node.name.path + "\"\n")      
      cmake_file.write("   DESCRIPTION_ORIGIN \"" + test_node.description.path + "\"\n")
      if test_node.driver_cmd_line_flags:
         cmake_file.write("   DRIVER_CMD_LINE_FLAGS_ORIGIN \"" + test_node.driver_cmd_line_flags.path + "\"\n")
      cmake_file.write("   FIRMWARE_BUILD_ORIGIN \"" + test_node.firmware_build.path + "\"\n")
      
      cmake_file.write(")\n")
      cmake_file.write("\n")
      
      test_id += 1
   
   cmake_file.close()
   
   sys.stdout.write("CMake information written to file \"" + cmake_filename
                    + "\"\n")
   
def main():
    
    parser = argparse.ArgumentParser( 
       description = 
       "This tool traverses the testing path hierarchy of a "
       "Kaleidoscope module and generates testing information "
       "that can be used to generate and run tests using an additional "
       "build system.")

    parser.add_argument('-d', '--testing_tree_root', 
      metavar  = 'path', 
      dest     = 'testing_tree_root', 
      required = 'True', 
      nargs    = 1,
      help     = 'The root path of the Kaleidoscope module\'s testing tree'
    )
    
    parser.add_argument('-c', '--cmake_test_definition_file', 
      metavar  = 'file', 
      dest     = 'cmake_test_definition_file', 
      required = 'False', 
      nargs    = 1,
      help     = 'An output file with test specifications in CMake format'
    )
                   
    args = parser.parse_args()

    tree_root = "".join(args.testing_tree_root)
    sys.stdout.write("Configuring testing tree in \"" 
       + tree_root + "\"\n")
    
    test_nodes_by_path = setup_testing_tree(tree_root)
    
    check_test_name_uniqueness(test_nodes_by_path)
    
    unique_firmware_builds_by_digest \
      = determine_unique_firmware_builds(test_nodes_by_path)
   
    if args.cmake_test_definition_file:
       cmake_test_definition_file = "".join(args.cmake_test_definition_file)
       export_as_cmake( cmake_test_definition_file, 
                        test_nodes_by_path, 
                        unique_firmware_builds_by_digest)
                   
if __name__ == "__main__":
    main()