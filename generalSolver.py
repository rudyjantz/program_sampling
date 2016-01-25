import sys
from crypto import ProgramSolver

production_lengths = {}
def record_production(p,d,l):
    global production_lengths
    if (p,d) in production_lengths:
        assert production_lengths[(p,d)] == l
    production_lengths[(p,d)] = l

def blank(l):
    return [0]*len(l)

tape_index = 0
def flip():
    global tape_index
    tape_index += 1
    return tape[tape_index-1]

def guard_expression(d,z):
    assert d > 0

    c1 = flip()
    c2 = flip()

    o = None
    if c1 and c2: o = 'eq'
    if not c1 and c2: o = 'gt'
    if not c2 and not c2: o = 'lt'

    program = "(%s %s)" % (o,z)
    mask = [1,1]

    record_production("guard",d,len(mask))
    
    return program,mask

def array_expression(d):
    assert d > 0

    c1 = flip()

    if d == 1:
        record_production("array",d,1)
        if c1: return "nil",[1]
        return "a",[1]

    choiceMask = [1,1,1]
    
    c2 = flip()
    c3 = flip()

    lp,lp_m = array_expression(d - 1)
    z,z_m = integer_expression(d - 1)
    g,g_m = guard_expression(d - 1,z)

    record_production("array",d,len(choiceMask+lp_m+z_m+g_m))
    shallow = False

    if (shallow and c1 and c2) or ((not shallow) and c1 and c2 and c3):
        return "nil",choiceMask+blank(lp_m)+blank(z_m)+blank(g_m)
    if (shallow and c1 and (not c2)) or ((not shallow) and c1 and c2 and (not c3)):
        return "a",choiceMask+blank(lp_m)+blank(z_m)+blank(g_m)
    if (shallow and (not c1) and c2) or ((not shallow) and c1 and (not c2) and c3):
        return ("(cdr %s)" % lp), choiceMask+lp_m+blank(z_m)+blank(g_m)
    if (shallow and (not c1) and (not c2)) or ((not shallow) and c1 and (not c2) and (not c3)):
        return ("(list %s)" % z), choiceMask+blank(lp_m)+z_m+blank(g_m)
    if (not shallow) and (not c1) and c2 and c3:
        return ("(filter %s %s)" % (g,lp)), choiceMask+lp_m+z_m+g_m

    return "FAILURE_A",[0]*(len(choiceMask+lp_m+z_m+g_m))

def integer_expression(d):
    assert d > 0
    if d == 1:
        record_production("integer",d,0)
        return '0',[]

    c1 = flip()
    c2 = flip()
    c3 = flip()
    choiceMask = [1,1,1]
    
    zp,z_m = integer_expression(d - 1)
    l,l_m = array_expression(d - 1)

    record_production("integer",d,len(choiceMask+z_m+l_m))

    if c1 and c2 and c3: return '0',choiceMask+blank(z_m)+blank(l_m)
    if c1 and c2 and (not c3): return ("(+1 %s)" % zp),choiceMask+z_m+blank(l_m)
    if c1 and (not c2) and c3: return ("(-1 %s)" % zp),choiceMask+z_m+blank(l_m)
    if c1 and (not c2) and (not c3): return ("(car %s)" % l),choiceMask+blank(z_m)+l_m
    if (not c1) and c2 and c3: return ("(length %s)" % l),choiceMask+blank(z_m)+l_m

    return "FAILURE_Z",[0]*(len(choiceMask+z_m+l_m))
#    assert False

def parse_tape(t):
    global tape
    global tape_index
    tape_index = 0
    tape = [ f == 1 for f in t ]
    c,c_m = integer_expression(2)
    g,g_m = guard_expression(2,c)
    target,t_m = integer_expression(2)
    b,b_m = array_expression(2)
    x,x_m = array_expression(3)
    rx = flip()
    y,y_m = array_expression(3)
    ry = flip()
    z,z_m = array_expression(3)
    rz = flip()

    if rx: x = '(recur %s)' % x
    if ry: y = '(recur %s)' % y
    if rz: z = '(recur %s)' % z

    program = '(if (%s %s)\n    %s\n    (append %s\n            %s\n            %s))' % (g,target,b,x,y,z)
    mask = c_m+g_m+t_m+b_m+x_m+[1]+y_m+[1]+z_m+[1]

    return program,mask

class GeneralSolver(ProgramSolver):
    def parse_tape(self,t):
        p,m = parse_tape(t)
        return p,m

if len(sys.argv) == 1:
    x = GeneralSolver()
    x.analyze_problem()
    print "total time = ",x.tt
else:
    if ',' in sys.argv[1]:
        input_tape = "[%s]" % sys.argv[1]
        p,m = parse_tape([ (x == 1) for x in eval(input_tape) ])
        print p
        print m
        print len(m)
        print production_lengths
    else:
        random_projections = int(sys.argv[1])
        a = None
        if len(sys.argv) > 2:
            a = int(sys.argv[2])
        x = GeneralSolver(fakeAlpha = a)
        x.enumerate_solutions(random_projections)
        print "total time = ",x.tt

        