#!/usr/bin/env python
import sys
import copy

#the buggy program
def remove_html_markup(s):
    tag   = False
    quote = False
    out   = ""

    for c in s:

        if c == '<' and not quote:
            tag = True
        elif c == '>' and not quote:
            tag = False
        elif c == '"' or c == "'" and tag:
            quote = not quote
        elif not tag:
            out = out + c

    return out

# The delta debugger   
def ddmin(s):
    #assert test(s) == "FAIL"

    n = 2     # Initial granularity
    while len(s) >= 2:
        start = 0
        subset_length = len(s) / n
        some_complement_is_failing = False

        while start < len(s):
            complement = s[:start] + s[start + subset_length:]

            if test(complement) == "FAIL":
                s = complement
                n = max(n - 1, 2)
                some_complement_is_failing = True
                break
                
            start += subset_length

        if not some_complement_is_failing:
            if n == len(s):
                break
            n = min(n * 2, len(s))

    return s

# We use these variables to communicate between callbacks and drivers
the_line      = None
the_iteration = None
the_state     = None
the_diff      = None
the_input     = None

def trace_fetch_state(frame, event, arg):
    global the_line
    global the_iteration
    global the_state
    
    line_no = frame.f_lineno
    
    if line_no not in trace_fetch_state.store:
        trace_fetch_state.store[line_no] = 0
    trace_fetch_state.store[line_no] += 1
               
    if the_line == line_no and the_iteration == trace_fetch_state.store[line_no]:        
        the_state = copy.deepcopy(frame.f_locals)  
    
    return trace_fetch_state

# Get the state at LINE/ITERATION
def get_state(input, line, iteration):
    global the_line
    global the_iteration
    global the_state
    
    the_line      = line
    the_iteration = iteration
    trace_fetch_state.store = {}
    
    sys.settrace(trace_fetch_state)
    y = remove_html_markup(input)
    sys.settrace(None)
    
    return the_state

def trace_apply_diff(frame, event, arg):
    global the_line    
    global the_iteration
    global the_diff

    line_no = frame.f_lineno
    
    if line_no not in trace_apply_diff.store:
        trace_apply_diff.store[line_no] = 0
    trace_apply_diff.store[line_no] += 1
               
    if the_line == line_no and the_iteration == trace_apply_diff.store[line_no]:        
        frame.f_locals.update(the_diff)
    
    return trace_apply_diff

# Testing function: Call remove_html_output, stop at THE_LINE/THE_ITERATION, 
# and apply the diffs in DIFFS at THE_LINE
def test(diffs):
    global the_line
    global the_iteration
    global the_diff
    global the_input
   
    the_diff = diffs
    trace_apply_diff.store = {}

    sys.settrace(trace_apply_diff)
    y = remove_html_markup(the_input)
    sys.settrace(None)

    if y.find('<') == -1:
        return "PASS"
    else:
        return "FAIL"
        
html_fail = '"<b>foo</b>"'
html_pass = "'<b>foo</b>'"

locations = [(8, 1), (14, 1), (14, 2), (14, 3), (23, 1)]

def auto_cause_chain(locations):
    global html_fail, html_pass, the_input, the_line, the_iteration, the_diff
    print "The program was started with", repr(html_fail)
    
    for (line, iteration) in locations:
        
        # Put the state of variables at the line and iteration
        # for the passing and the failing runs in the following variables.
        state_pass = get_state(html_pass,line,iteration)       
        state_fail = get_state(html_fail,line,iteration)
    
        # Compute the differences between the passing and failing runs.
        diffs = []
        for var in state_fail.keys():
            if not state_pass.has_key(var) or state_pass[var] != state_fail[var]:
                diffs.append((var, state_fail[var]))
 
        # Minimizing the failure-inducing set of differences
        the_input = html_pass
        the_line  = line
        the_iteration  = iteration
        cause = ddmin(diffs)
        
        # Pretty output
        print "Then, in Line " + repr(line) + " (iteration " + repr(iteration) + "),",
        for (var, value) in cause:
            print var, 'became', repr(value)
            
    print "Then the program failed."

auto_cause_chain(locations)

# The output should look like this:
"""
The program was started with '"<b>foo</b>"'
Then, in Line 8 (iteration 1), s became '"<b>foo</b>"'
Then, in Line 14 (iteration 1), c became '"'
Then, in Line 14 (iteration 2), quote became True
Then, in Line 14 (iteration 3), out became '<'
Then, in Line 23 (iteration 1), out became '<b>foo</b>'
Then the program failed.
"""
