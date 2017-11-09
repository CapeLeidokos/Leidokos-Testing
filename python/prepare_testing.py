#!/usr/bin/python

# -*- coding: utf-8 -*-

import argparse
import sys
import os
import hashlib
import yaml

def find_files(pattern, path):
    result = []
    for root, dirs, files in os.walk(path):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                result.append(os.path.join(root, name))
    return result
 
def find_file(name, path):
    for root, dirs, files in os.walk(path):
        if name in files:
            return os.path.join(root, name)
    return None
 
external_specification_subdir_name  = "__external__"
test_trigger_basename               = "__test__"
firmware_sketch_basename            = "sketch.ino"
test_driver_basename                = "driver.py"
test_specification_basename         = "specification.yaml"

# Every information that defines a test is an
# abstract entity. 
#
# Entities can either store data by themselfs, which is the 
# case if they represent an entity that overrides a
# parent entity, or they can reference an entity
# that was defined on a parent level of the directory
# structure and was not overridden.
#
class Entity(object):
   
   def __init__(self):
      self.directory = None
   
   def attach(self, directory):
      self.directory = .name

class File(Entity):

   def __init__(self, filename = None):
       
      self.filename = filename
      
   def __eq__(self, other):
    return self.filename == other.filename

class PythonDriver(File)
class ArduinoSketch(File)
       
# A property represents any information that
# was collected from the yaml specification. 
# Properties define a name -> value relation.
#
class Property(Entity):
   
   def __init__(self, value = None):
      
      self.value = value
   
   def __eq__(self, other):
    return self.value == other.value
 
# A Kaleidoscope module is either a core module or
# a plugin, defined by ifs URL and optionally a commit definition.
# If the commit is not explicitly defined, the masters head will 
# be used.
# A module can replace or remove a parent module with given name
# if necessary.
#
# If no url is defined but a name, we assume that 
# a parent module with respective name is supposed to be removed.
# The sketch must take care that in such a case the 
# removed module is not referenced in no possible way.
#
class KaleidoscopeModule(object):
   
   def __init__(self):
      
      self.url = None
      self.commit = None
      self.name = None
      
   # To be able to define a module and its purpose
   # exactly, we compute a sha256 identifier
   #
   def getSha256(self):
      
      m = hashlib.sha256()
      m.update(self.url)
      m.update(self.commit)
      m.update(self.name)
      m.digest()
      
      return m
    
class FirmwareBuild(Entity):

   def __init__(self, parent_build = None):
      
      if parent_build:
         self.modules = parent_build.modules
         self.SHAs = parent_build.SHAs
         self.firmware_sketch = parent_build.firmware_sketch
      else:
         self.modules = None
         self.SHAs = None
         self.firmware_sketch = None
   
   def containsModule(self, new_module):
          
      new_sha = new_module.getSha256()

      # Check if a module with same sha is already present
      #
      try:
         list_index = self.SHAs.index(new_sha)
         
         # The fact that no exception has been thrown 
         # indicates that the sha was found.
         
         # In this case, we do not need to take any 
         # action and just go with the parent list
         # of modules.
         
         return True
         
      except:
         
      return False
   
   def clone(self):
            
      new_self = FirmwareBuild(self)
      
      # This firmware build must be made unique.
      # Therefore, make a shallow copy of modules and SHAs. 
      #
      new_self.new_modules = copy.copy(self.modules)
      new_self.SHAs = copy.copy(self.SHAs)
      
      return new_self
     
   def addModule(self, new_module):
      
      # If the new module does not define a name, just add it to the 
      # list of modules
      #
      new_name = new_module.getName()
      do_append = True
      
      if new_name:
         
         # Check if the firmware build
         # contains a module that has the same name as the new
         # module. If so, we replace it.
         #
         for i, module in enumerate(self.modules):
            if module.getName() == new_name:
               self.modules(i) = new_module
               self.SHAs(i) = new_sha
               do_append = False
               break
            
      if do_append:
         self.modules.append(new_module)
         self.SHAs.append(new_sha)
            
   # Compute the sha of all modules. As the order of
   # updating the overall sha is not commutative 
   # with respect to the members, we have to sort it first
   #
   def getSha256(self):

      SHAs = []
      for module in self.modules:
         SHAs.append(module.getSha256())
      
      SHAs.sort()
      
      m = hashlib.sha256()
      
      for sha in SHAs:
         m.update(sha)
         
      m.update(self.firmware_build.filename)
         
      return m

class TestNode(object):
    
   def __init__(self, path, parent = None):
      
      self.children = []
      
      self.parent = parent
      
      self.path = path
      
      self.initEntities()
      
      self.setup()
      
   def generateGlobalName(self):
     
      if self.parent:
         
         parent_name = self.parent.generateGlobalName()
         
         if not (self.name is self.parent.name):
            return parent_name + "." + self.name.value
         else:
            return parent_name
      else:
         return self.name.value
      
   def generatesTests(self)
      return self.is_test_target or (len(self.children) == 0)
   
   def recursively_check_validity(self):
      
      is_valid = True
      
      if self.generatesTests()
      
         if not self.path:
            is_valid = False
            sys.stdout.write("A test node without a path definition was found\n")
                  
         if not self.name:
            sys.stdout.write("A test node for path %s was found that does not feature a name\n")
         
         if not self.description:
            sys.stdout.write("A test node for path %s was found that does not feature a description\n")
         
         if not self.firmware_build:
            sys.stdout.write("A test node for path %s was found that does not feature a firmware_build\n")
            
      for child in self.children:
         is_valid &= child.recursively_check_validity()
         
      return is_valid
      
   def initEntities(self):
      
      self.python_driver = None
   
      # Properties
      #
      self.name = None
      self.description = None
      
      # Defines if tests are supposed to be run on this level
      #
      self.is_test_target = None
      
   def useParentEntity(self, name):

      if self.parent:
         setattr(self, name, getattr(self.parent, name))
      
   def findPythonDriver(self, path):
      
      python_driver_file = find_file(test_driver_basename, path)
      
      if python_driver_file:
         self.python_driver = PythonDriver(python_driver_file)
         self.python_driver.attach(self)
         return
      
      useParentEntity(python_driver)
         
   def findArduinoSketch(self, path):
      
      arduino_sketch_file = find_file(firmware_sketch_basename, path)
      
      if arduino_sketch_file:
         
         if not self.needs_own_firmware_build:
            
            if not self.firmware_build.arduino_sketch.filename == arduino_sketch_file:
               
               self.cloneFirmwareBuild()
         
         self.firmware_build.arduino_sketch = ArduinoSketch(arduino_sketch_file)
         self.firmware_build.arduino_sketch.attach(self)
         return
      
      useParentEntity(arduino_sketch)
      
   def findTestTrigger(self, path):
      
      test_trigger = find_file(test_trigger_basename, path)
      
      if test_trigger:
         self.is_test_target = True
      else:
         self.is_test_target = False
      
   def parseYAMLDefinitions(self, path):
      
      yaml_file = find_file(test_specification_basename, path)
      
      # Every entity that is not modified below, points
      # to its parent 
      #
      useParentEntity(name)
      useParentEntity(description)
      useParentEntity(firmware_build)
      
      if not yaml_file:
         return
      
      my_yaml = None
      with open(yaml_file, 'r') as stream:
         try:
            my_yaml = yaml.load(stream)
         except yaml.YAMLError as exc:
            print(exc)
            return
            
      # my_yaml contains all necessary information as 
      # a large dictionary
      #
      new_name = my_yaml.get("name") 
      if new_name:
         self.name = Property(new_name)
         self.name.attach(self)
      else:
         path_basename = os.path.basename(path)
         self.name = Property(path_basename)
         self.name.attach(self)
         
      new_despription = my_yaml.get("description") 
      if new_despription:
         self.description = Property(new_despription)
         self.description.attach(self) 
         
      new_modules = my_yaml.get("modules")
      if new_modules:
         
         # Iterate over the modules and establish a 
         # firmware build
         #
         for module_dict in new_modules:
         
            new_module = KaleidoscopeModule()
            new_module.url = module_dict.get("url")
            new_module.commit = module_dict.get("commit")
            new_module.name = module_dict.get("name")

            # If we find a module that is not contained in 
            # the current set of modules
            #
            if not self.firmware_build.containsModule(new_module):
               
               # And this directory does not have its own set of
               # modules...
               #
               if not self.needs_own_firmware_build:
                  
                  # We clone a new copy
                  #
                  self.cloneFirmwareBuild()
                  
               self.firmware_build.addModule(new_module)
               
   def cloneFirmwareBuild(self):
  
      self.firmware_build = self.firmware_build.clone()
      self.needs_own_firmware_build = True
               
   def setup(self):
      
      if self.parent:
         self.firmware_build = self.parent.firmware_build
         self.needs_own_firmware_build = False
      else:
         self.firmware_build = FirmwareBuild()
         self.needs_own_firmware_build = True
      
      # Check if there is a external reference to another subdirectory
      # Such a subdirectory could, e.g. be a git submodule.
      # If an external specification is found, anythin else
      # in the directory is ignored.
      #
      external_specification_dir \
         = find_file(external_specification_subdir_name, self.path) 
      
      if external_specification_dir:
         
         if not os.path.isdir(external_specification_dir):
            
            sys.exit("Directory \"" + self.path +
              "\" contains an external specification \"" +
              external_specification_subdir_name
              + "\" that is not an directory.");
         
         # If we found an external specfication directory, 
         # check for any other files being present, 
         # appart from the test trigger file.
         # If so, we abort with an error.
         
         all_files = find_files("*", self.path)
         
         trigger_wrong_files_error = False
         if len(all_files) > 2:
            trigger_wrong_files_error = True
         else if len(all_files) == 2:
            other_file_is_test_trigger = False
            if all_files(1) == test_trigger_basename:
               other_file_is_test_trigger = True
            else if all_files(2) == test_trigger_basename:
               other_file_is_test_trigger = True
               
            if not other_file_is_test_trigger:
               trigger_wrong_files_error = True
            
         if trigger_wrong_files_error:
            sys.exit("Directory \"" + self.path +
              "\" contains an external specification \"" +
              external_specification_subdir_name
              + "\" and also additional files/directories appart from the test trigger (" + test_trigger_basename + "). "
              "Please make sure that either the external specification "
              "or other files are found.");
         
         source_path = external_specification_dir
      else:
         source_path = self.path
       
      # The source path is the directory that is searched
      # for test information. This can either be the current
      # directory or the external test reference directory
      # determined above
      
      self.findPythonDriver(source_path)
      self.findArduinoSketch(source_path)
      self.parseYAMLDefinitions(source_path)
      
      # Look in the current directory for a TEST trigger file
      #
      self.findTestTrigger(self.path)

def setup_testing_tree(testing_tree_root)

   # Every 
   
   test_nodes_by_path = {}
   
   root_node = TestNode(testing_tree_root)
   
   test_nodes_by_path.insert(testing_tree_root, root_node)
   
   # Recursively traverse the testing directory structure
   # and establish a testing tree
   #
   for dirpath, dirs, files in os.walk(testing_tree_root):
      
      # Ignore empty directories
      #
      if (len(dirs) == 0) and (len(files) == 0):
         continue
      
      dirpath_basename = os.path.basename(dirpath)
      
      # Skip any external testing specification dirs
      #
      if dirpath_basename == external_specification_subdir_name:
         continue
      
      my_parent_test_node = test_nodes_by_path.get(dirpath)
      
      for my_dir in dirs:
         
         # Skip any external testing specification dirs
         #
         if my_dir == external_specification_subdir_name:
            continue
         
         new_test_node = TestNode(testing_tree_root, my_parent_dir)
         
         my_parent_test_node.children.append(new_test_node)
         
         test_nodes_by_path.insert(os.path.join(dirpath, my_dir), new_test_node)
         
   root_node.recursively_check_validity()
         
   return test_nodes_by_path

def check_test_name_uniqueness(test_nodes_by_path):
   
   test_name_to_test_node = {}
   
   for test_node in test_nodes_by_path.values():
      
      test_name = test_node.generateGlobalName()
      
      if test_name in test_name_to_test_node.keys():
         
         sys.exit("To tests in directories \"%s\" and \"%s\" that "
            "have the same name \"%s\". Please ensure that all tests have individual names" % (test_node.path, test_name_to_test_node.get(test_name).path, test_name))
         
      test_name_to_test_node.insert(test_name, test_node)

def determine_unique_firmware_builds(test_nodes_by_path)

   # Generate a unique set of firmware builds.

   unique_firmware_builds_by_SHA = {}

   for test_node in test_nodes_by_path.values():
      
      if test_node.needs_own_firmware_build:
         
         my_sha = test_node.firmware_build.getSha256()
         
         set_id = 1
         if not my_sha in unique_firmware_builds_by_SHA.keys():
            test_node.firmware_build.set_id = set_id
            unique_firmware_builds_by_SHA.insert(my_sha, test_node.firmware_build)
            set_id = set_id + 1
            
   # Now replace references to modules with the unique versions
   #
   for test_node in test_nodes_by_path.values():
      
      my_sha = test_node.firmware_build.getSha256()
      
      test_node.unique_modules = unique_firmware_builds_by_SHA.get(my_sha)
      
   return unique_firmware_builds_by_SHA
      
def sep_line(file):   
   file.write(
"################################################################################")
      
def export_as_cmake(cmake_filename, 
                    test_nodes_by_path, 
                    unique_firmware_builds_by_SHA):
   
   cmake_file = open(cmake_filename, "w") 
   
   # First export the firmware builds 
   #
   sep_line(cmake_file)
   cmake_file.write("Kaleidoscope firmware builds")
   sep_line(cmake_file)
   
   for firmware_build in unique_firmware_builds_by_SHA:
      cmake_file.write("kaleidoscope_firmware_build(")
      cmake_file.write("   BUILD_ID \"" + firmware_build.set_id + "\"")
      cmake_file.write("   ARDUINO_SKETCH \"" + firmware_build.arduino_sketch.filename + "\"")
      for mod in firmware_build.modules:
         cmake_file.write("   URL \"" + mod.url + "\"")
         cmake_file.write("   COMMIT \"" + mod.commit + "\"")
         cmake_file.write("   NAME \"" + mod.name + "\"")
      cmake_file.write(")")
      cmake_file.write("")  
      
   # Now export the test definitions
   #
   sep_line(cmake_file)
   cmake_file.write("Kaleidoscope tests")
   sep_line(cmake_file)
   
   test_id = 1
   for test_node in test_nodes_by_path.values():
      
      # Any interior nodes of the testing tree have to contain a
      # tag file for tests for them to be created. 
      # For leaf nodes of the testing tree, we always generate 
      # tests.
      #
      if not test_node.generatesTests()
         continue
      
      cmake_file.write("kaleidoscope_firmware_test(")
      cmake_file.write("   TEST_ID \"" + test_id + "\"")
      cmake_file.write("   TEST_NAME \"" + test_node.generateGlobalName() + "\"")
      cmake_file.write("   TEST_DESCRIPTION \"" + test_node.description + "\"")
      cmake_file.write("   PYTHON_DRIVER \"" +
                test_node.python_driver.filename + "\"")  
      cmake_file.write("   FIRMWARE_BUILD_ID \"" +
                test_node.firmware_build.set_id + "\"")
      
      # Additional information that is probably not used by CMake
      #
      cmake_file.write("   # Directories where information was found \"" + test_node.name.directory + "\"") 
      cmake_file.write("   NAME_ORIGIN \"" + test_node.name.directory + "\"")      
      cmake_file.write("   DESCRIPTION_ORIGIN \"" + test_node.description.directory + "\"")
      cmake_file.write("   PYTHON_DRIVER_ORIGIN \"" + test_node.python_driver.directory + "\"")
      cmake_file.write("   FIRMWARE_BUILD_ID_ORIGIN \"" + test_node.firmware_build.directory + "\"")
      
      cmake_file.write(")")
      cmake_file.write("")
      
      test_id += 1
   
   cmake_file.close()
   
def main():
    
    parser = argparse.ArgumentParser( 
       description = 
       "This tool traverses the testing directory hierarchy of a "
       "Kaleidoscope module and generates testing information "
       "that can be used to generate and run tests using an additional "
       "build system.")

    parser.add_argument('-d', '--testing_tree_root', 
      metavar  = 'directory', 
      dest     = 'testing_tree_root', 
      required = 'True', 
      nargs    = 1,
      help     = 'The root directory of the Kaleidoscope module\'s testing tree'
    )
    
    parser.add_argument('-c', '--cmake_test_definition_file', 
      metavar  = 'file', 
      dest     = 'cmake_test_definition_file', 
      required = 'False', 
      nargs    = 1,
      help     = 'An output file with test specifications in CMake format'
    )
                   
    args = parser.parse_args()

    sys.stdout.write("Configuring testing tree in \"" 
       + args.testing_tree_root + "\"\n")
    
    test_nodes_by_path = setup_testing_tree(args.testing_tree_root)
    
    check_test_name_uniqueness(test_nodes_by_path)
    
    unique_firmware_builds_by_SHA \
      = determine_unique_firmware_builds(test_nodes_by_path)
   
    if args.cmake_test_definition_file:
       export_as_cmake( args.cmake_test_definition_file, 
                        test_nodes_by_path, 
                        unique_firmware_builds_by_SHA):
          
    # If test specifications are supposed to be generated in other formats,
    # just copy and adapt the export_as_cmake function
                   
if __name__ == "__main__":
    main()