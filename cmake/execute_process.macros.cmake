# -*- mode: cmake -*-
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
 
 function(_execute_process
   explanation_
)
   set(options "")
   set(one_value_args "OUTPUT_VARIABLE" "RESULT_VARIABLE")
   set(multi_value_args "")
   
   cmake_parse_arguments(args "${options}" "${one_value_args}" "${multi_value_args}" ${ARGN} )
   
   string(TIMESTAMP start_time "%Y-%m-%dT %H:%M:%S")
   
   execute_process(
      ${args_UNPARSED_ARGUMENTS}
      RESULT_VARIABLE result
      OUTPUT_VARIABLE output
      ERROR_VARIABLE error
   )
   string(TIMESTAMP end_time "%Y-%m-%dT %H:%M:%S")
   
   if(NOT "${log_file}" STREQUAL "")
      file(APPEND "${log_file}"
"
${explanation_}
*****************************************************************
Command
*****************************************************************
${args_UNPARSED_ARGUMENTS}
*****************************************************************
Timing
*****************************************************************
Start: ${start_time}
End  : ${end_time}
*****************************************************************
Exit code
*****************************************************************
${result}
*****************************************************************
Stdout
*****************************************************************
${output}
*****************************************************************
Stderr
*****************************************************************
${error}
")
   endif()
   
   if(NOT result EQUAL 0)
      message("Unable to ${explanation_}")
      message("command: ${ARGN}")
      message("output: ${output}")
      message("error: ${error}")
      message("result: ${result}")
      message(FATAL_ERROR "Aborting.")
   endif()

   if(NOT "${args_OUTPUT_VARIABLE}" STREQUAL "")
      set("${args_OUTPUT_VARIABLE}" "${output}" PARENT_SCOPE)
   endif()
   
   if(NOT "${args_RESULT_VARIABLE}" STREQUAL "")
      set("${args_RESULT_VARIABLE}" "${result}" PARENT_SCOPE)
   endif()
   
endfunction()