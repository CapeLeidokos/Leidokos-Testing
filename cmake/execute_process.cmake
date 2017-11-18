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
      message(SEND_ERROR "Unable to ${explanation}")
      message(SEND_ERROR "${output}")
      message(SEND_ERROR "${error}")
      message(FATAL_ERROR "Aborting.")
   endif()
endfunction()