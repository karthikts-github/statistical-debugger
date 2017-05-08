#!/usr/bin/env python
import sys
import math

# The buggy program
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

coverage = {}

# Tracing function that saves the coverage data
def traceit(frame, event, arg):
    global coverage
    if event == "line":
        filename = frame.f_code.co_filename
        lineno   = frame.f_lineno
        if not filename in coverage:
            coverage[filename] = {}
        coverage[filename][lineno] = True
        
    return traceit


# Run the program with each test case and record
# input, outcome and coverage of lines
def run_tests(inputs):
    runs   = []
    for input in inputs:
        global coverage
        coverage = {}
        sys.settrace(traceit)
        result = remove_html_markup(input)
        sys.settrace(None)
        
        if result.find('<') == -1:
            outcome = "PASS"
        else:
            outcome = "FAIL"
        
        runs.append((input, outcome, coverage))
    return runs

# Create empty tuples for each covered line
def init_tables(runs):
    tables = {}
    for (input, outcome, coverage) in runs:
        for filename, lines in coverage.items():
            for line in lines.keys():
                if not filename in tables:
                    tables[filename] = {}
                if not line in tables[filename]:
                    tables[filename][line] = (0, 0, 0, 0)

    return tables

# Print out values of phi, and result of runs for each covered line
def print_tables(tables):
    for filename in tables.keys():
        lines = open(filename).readlines()
        for i in range(6, 22): # lines of the remove_html_markup in this file
            if i+1 in tables[filename]:
                (n11, n10, n01, n00) = tables[filename][i + 1]
                try:
                    factor = phi(n11, n10, n01, n00)
                    prefix = "%+.4f%2d%2d%2d%2d" % (factor, n11, n10, n01, n00)
                except:
                    prefix = "       %2d%2d%2d%2d" % (n11, n10, n01, n00)
            else:
                prefix = "               "
                    
            print(prefix, lines[i])

# Calculate phi coefficient from given values            
def phi(n11, n10, n01, n00):
    return ((n11 * n00 - n10 * n01) / 
             math.sqrt((n10 + n11) * (n01 + n00) * (n10 + n00) * (n01 + n11)))


# Compute n11, n10, etc. for each line
def compute_n(tables):
    for filename, lines in tables.items():
        for line in lines.keys():
            (n11, n10, n01, n00) = tables[filename][line]
            for (input, outcome, coverage) in runs:
                if filename in coverage and line in coverage[filename]:
                    # Covered in this run
                    if outcome == "FAIL":
                        n11 += 1  # covered and fails
                    else:
                        n10 += 1  # covered and passes
                else:
                    # Not covered in this run
                    if outcome == "FAIL":
                        n01 += 1  # uncovered and fails
                    else:
                        n00 += 1  # uncovered and passes
            tables[filename][line] = (n11, n10, n01, n00)
    return tables
      
# These are the test cases          
inputs_line = ['foo', 
          '<b>foo</b>', 
          '"<b>foo</b>"', 
          '"foo"', 
          "'foo'", 
          '<em>foo</em>', 
          '<a href="foo">foo</a>',
          '""',
          "<p>"]

#execute algorithm

#run few tests with different inputs
runs = run_tests(inputs_line)

# Now compute (and report) phi for each line. The higher the value,
# the more likely the line is the cause of the failures.
tables = init_tables(runs)
tables = compute_n(tables)
print_tables(tables)      
