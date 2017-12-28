function(_execute_process
   explanation_
)
   execute_process(
      ${ARGN}
      RESULT_VARIABLE result
      OUTPUT_VARIABLE output
      ERROR_VARIABLE error
   )
   
   if(NOT result EQUAL 0)
      message("Unable to ${explanation_}")
      message("command: ${ARGN}")
      message("output: ${output}")
      message("error: ${error}")
      message("result: ${result}")
      message(FATAL_ERROR "Aborting.")
   endif()
endfunction()